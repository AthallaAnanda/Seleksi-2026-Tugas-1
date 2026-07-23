"""
load_data.py - Load: JSON clean (Data Scraping/data/) → OLTP PostgreSQL

Mengikuti panduan-implementasi.md Tahap 3.

Deviasi sadar dari pseudocode:
  · Semua tabel (termasuk kandidat COPY: nav_record, portfolio_holding,
    benchmark_data_point) di-load lewat execute_values + ON CONFLICT, bukan
    COPY mentah - COPY tidak mendukung ON CONFLICT sehingga re-run kedua akan
    gagal duplicate-key, bukan idempotent. Skala data (maks ~341rb baris)
    masih cukup cepat tanpa staging table; upgrade ke COPY+staging adalah
    pekerjaan optimasi §15, bukan §12.
  · manager_personnel & manager_shareholder tidak punya UNIQUE constraint
    selain PK serial-nya sendiri (tidak ada conflict target) → idempotency
    dicapai lewat full-refresh per manager_id (DELETE lalu INSERT), bukan
    ON CONFLICT.
  · fund_ranking: 302 baris dengan risk_rank=rating_rank=all_risk_rank=
    pasardana_rating=risk_rating=all_risk_rating=0 sekaligus adalah sentinel
    API "belum ada ranking periode ini" (melanggar CHECK), bukan data asli
    → di-skip, bukan dipaksa insert.
  · mutual_fund: fund_id=4374 (Batavia Proteksi Maxima 16) punya
    min_next_subscription=-1 (sentinel "tidak berlaku" utk fund proteksi
    tertutup, melanggar CHECK >= 0) → dikoreksi jadi NULL saat load.

Jalankan:
  python load_data.py            # full load
  python load_data.py --subset 20  # uji: hanya 20 fund_id pertama
"""
import argparse
import json
import logging
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

BASE_DIR = Path(__file__).resolve().parent          # Data Storing/src
ROOT_DIR = BASE_DIR.parent.parent                   # project root
DATA_DIR = ROOT_DIR / "Data Scraping" / "data"
ENV_PATH = ROOT_DIR / ".env"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger("load")

# SANITY THRESHOLDS (dipakai oleh fungsi fix_* di bawah)
TELEPHONE_MAX_LEN = 50          # VARCHAR(50) custodian_bank.telephone
FEE_SANITY_MAX_PCT = 100        # fee > 100% tidak masuk akal secara bisnis (BUG 3)
TREYNOR_OUTLIER_THRESHOLD = 10000  # |treynor_ratio| di atas ini = artefak beta~0 (BUG 6)


# CONFIG
def load_env(path: Path) -> dict:
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip()
    return env


def get_conn():
    env = load_env(ENV_PATH)
    return psycopg2.connect(
        host=env.get("PG_HOST", "localhost"),
        port=env.get("PG_PORT", "5432"),
        dbname=env.get("PG_DB", "reksadana"),
        user=env.get("PG_USER", "postgres"),
        password=env.get("PG_PASSWORD", "postgres"),
    )


def load_json(name: str) -> list:
    return json.loads((DATA_DIR / f"{name}.json").read_text())


# HELPER GENERIK
def bulk_upsert(conn, table: str, columns: list[str], rows: list[dict],
                 conflict_cols: list[str], do_update: bool = True,
                 bump_scraped_at: bool = False) -> int:
    """Pola B generik via execute_values + ON CONFLICT."""
    if not rows:
        log.info(f"{table}: 0 baris (skip)")
        return 0
    cols_sql = ", ".join(columns)
    conflict_sql = ", ".join(conflict_cols)
    if do_update:
        update_cols = [c for c in columns if c not in conflict_cols]
        set_clauses = [f"{c} = EXCLUDED.{c}" for c in update_cols]
        if bump_scraped_at:
            set_clauses.append("scraped_at = NOW()")
        conflict_clause = f"DO UPDATE SET {', '.join(set_clauses)}"
    else:
        conflict_clause = "DO NOTHING"
    sql = f"INSERT INTO {table} ({cols_sql}) VALUES %s ON CONFLICT ({conflict_sql}) {conflict_clause}"
    values = [tuple(r.get(c) for c in columns) for r in rows]
    with conn.cursor() as cur:
        execute_values(cur, sql, values, page_size=5000)
    conn.commit()
    log.info(f"{table}: {len(rows)} baris di-upsert")
    return len(rows)


def refresh_child(conn, table: str, columns: list[str], rows: list[dict],
                   parent_col: str = "manager_id") -> int:
    """Full-refresh per parent_id - untuk tabel tanpa UNIQUE constraint natural
    (manager_personnel, manager_shareholder)."""
    if not rows:
        log.info(f"{table}: 0 baris (skip)")
        return 0
    parent_ids = list({r[parent_col] for r in rows})
    cols_sql = ", ".join(columns)
    sql = f"INSERT INTO {table} ({cols_sql}) VALUES %s"
    values = [tuple(r.get(c) for c in columns) for r in rows]
    with conn.cursor() as cur:
        cur.execute(f"DELETE FROM {table} WHERE {parent_col} = ANY(%s)", (parent_ids,))
        execute_values(cur, sql, values, page_size=5000)
    conn.commit()
    log.info(f"{table}: refresh {len(parent_ids)} {parent_col}, {len(rows)} baris")
    return len(rows)


def load_snapshots(conn, rows: list[dict]) -> dict:
    """Pola C: RETURNING + DO UPDATE dummy agar snapshot_id lama tetap terbaca saat re-run."""
    if not rows:
        return {}
    sql = """
        INSERT INTO portfolio_snapshot
            (fund_id, date_based, domestic_allocation_pct, foreign_allocation_pct)
        VALUES %s
        ON CONFLICT (fund_id, date_based) DO UPDATE SET fund_id = EXCLUDED.fund_id
        RETURNING snapshot_id, fund_id, date_based
    """
    values = [
        (r["fund_id"], r["date_based"], r.get("domestic_allocation_pct"), r.get("foreign_allocation_pct"))
        for r in rows
    ]
    with conn.cursor() as cur:
        result = execute_values(cur, sql, values, page_size=2000, fetch=True)
    conn.commit()
    snap_map = {(fid, str(dbased)): sid for sid, fid, dbased in result}
    log.info(f"portfolio_snapshot: {len(rows)} baris, {len(snap_map)} snapshot_id ter-map")
    return snap_map


def resolve_snapshot_rows(rows: list[dict], snap_map: dict) -> list[dict]:
    resolved, missing = [], 0
    for r in rows:
        key = tuple(r["snapshot_ref"])
        sid = snap_map.get(key)
        if sid is None:
            missing += 1
            continue
        resolved.append({**r, "snapshot_id": sid})
    if missing:
        log.warning(f"  {missing} baris dilewati: snapshot_ref tidak ditemukan di snap_map")
    return resolved


def aggregate_duplicates(rows: list[dict], key_field: str) -> list[dict]:
    """BUG 7: sebagian snapshot punya >1 baris utk (snapshot_ref, key_field) yang
    sama dgn value_pct BERBEDA (mis. fund 1717 @2026-06-30: category_id=0 muncul
    dua kali, 69.9 + 21.8 - dan total SELURUH baris snapshot itu tepat 100%).
    Ini bukan duplikat keliru, melainkan dua entri sumber yang kebetulan
    berbagi category_id/security_id yang sama → dijumlahkan (SUM), bukan
    dibuang salah satunya via ON CONFLICT DO NOTHING (yang akan merusak
    invarian total=100% utk portfolio_allocation)."""
    agg = {}
    for r in rows:
        key = (tuple(r["snapshot_ref"]), r[key_field])
        if key in agg:
            agg[key]["value_pct"] += r["value_pct"]
        else:
            agg[key] = dict(r)
    n_merged = len(rows) - len(agg)
    if n_merged:
        log.info(f"  {n_merged} baris digabung (SUM) karena berbagi (snapshot, {key_field})")
    return list(agg.values())


# DATA-CORRECTION FIXES (anomali sumber, ditemukan lewat audit CHECK constraint)
def fix_negative_min_next_subscription(funds: list[dict]) -> int:
    """BUG 2: fund_id=4374 (Batavia Proteksi Maxima 16) min_next_subscription=-1
    → sentinel "tidak berlaku" (fund proteksi tertutup), CHECK >= 0 akan reject.
    Mengubah funds in place. Return jumlah baris yang dikoreksi."""
    n_fixed = 0
    for f in funds:
        if f.get("min_next_subscription") is not None and f["min_next_subscription"] < 0:
            f["min_next_subscription"] = None
            n_fixed += 1
    if n_fixed:
        log.info(f"mutual_fund: {n_fixed} nilai min_next_subscription negatif dikoreksi ke NULL")
    return n_fixed


def fix_unreasonable_fees(funds: list[dict], fee_fields: list[str]) -> None:
    """BUG 3: fund_id=1281 (MEGA ASSET MANTAP) red_fee_max_pct=200.0 - melebihi
    presisi kolom NUMERIC(6,4) (maks 99.9999) & tidak masuk akal secara bisnis
    (fee lain di fund itu wajar: 1%, 3%, 0.25%). Tidak ada cara memastikan
    nilai "benar"-nya (mis. 2.00 dgn titik desimal salah) → di-null-kan,
    bukan ditebak. Mengubah funds in place."""
    for f in funds:
        for field in fee_fields:
            if f.get(field) is not None and f[field] >= FEE_SANITY_MAX_PCT:
                log.info(f"mutual_fund {f['fund_id']}: {field}={f[field]} tidak masuk akal, di-null-kan")
                f[field] = None


def dedupe_isin_code(funds: list[dict]) -> None:
    """BUG 4: isin_code UNIQUE, tapi 2 pasang kelas (Kelas C/N grup 5591;
    Kelas B/D grup 2438) berbagi isin_code sama persis di sumber. Tidak bisa
    dipastikan kelas mana yang ISIN-nya benar → dipertahankan hanya untuk
    kemunculan pertama, sisanya di-null-kan (bukan menebak salah satunya).
    Mengubah funds in place."""
    seen_isin = set()
    for f in funds:
        code = f.get("isin_code")
        if code is None:
            continue
        if code in seen_isin:
            log.info(f"mutual_fund {f['fund_id']}: isin_code {code} duplikat, di-null-kan")
            f["isin_code"] = None
        else:
            seen_isin.add(code)


def fix_policy_pct_range(funds: list[dict], policy_fields: list[str]) -> None:
    """BUG 5: policy_{bond,equity,money_market}_pct seharusnya berjumlah ~100%
    per fund, tapi 3 fund punya kombinasi yang meleset dari [0,100] (mis.
    fund 2113: equity=102.52 & money_market=-2.52 - rounding/plug-figure
    yang salah di sumber, jumlahnya tetap 100 tapi salah satu sisi negatif).
    Tidak bisa direkonstruksi split yang benar → field yang out-of-range
    di-null-kan per fund, bukan ditebak. Mengubah funds in place."""
    for f in funds:
        for field in policy_fields:
            if f.get(field) is not None and not (0 <= f[field] <= 100):
                log.info(f"mutual_fund {f['fund_id']}: {field}={f[field]} di luar 0-100, di-null-kan")
                f[field] = None


def fix_treynor_outlier(performances: list[dict]) -> int:
    """BUG 6: treynor_ratio = return / beta - saat beta mendekati nol, rasio
    meledak jadi ribuan (3 baris: -30098, 29550, -29550) melebihi presisi
    NUMERIC(12,8) dan jauh di luar rentang normal (~-350..350 utk 1347
    baris lain). Ini artefak numerik pembagian-hampir-nol, bukan performa
    asli → di-null-kan. Mengubah performances in place. Return jumlah baris
    yang dikoreksi."""
    n_fixed = 0
    for r in performances:
        if r.get("treynor_ratio") is not None and abs(r["treynor_ratio"]) >= TREYNOR_OUTLIER_THRESHOLD:
            r["treynor_ratio"] = None
            n_fixed += 1
    if n_fixed:
        log.info(f"fund_performance: {n_fixed} treynor_ratio meledak (beta~0), di-null-kan")
    return n_fixed


def filter_sentinel_zero_rankings(rankings: list[dict], zero_fields: list[str]) -> list[dict]:
    """BUG 1: 302 baris dgn risk_rank=rating_rank=all_risk_rank=
    pasardana_rating=risk_rating=all_risk_rating=0 sekaligus → sentinel
    "belum dinilai periode ini", melanggar CHECK. Di-skip, bukan dipaksa
    insert. Return list baru (tidak mengubah rankings)."""
    filtered = [r for r in rankings if not all(r[f] == 0 for f in zero_fields)]
    n_skipped = len(rankings) - len(filtered)
    if n_skipped:
        log.info(f"fund_ranking: {n_skipped} baris sentinel-zero di-skip (belum ada ranking periode ini)")
    return filtered


# MAIN
def main(subset: int | None):
    conn = get_conn()
    log.info(f"Terhubung ke {conn.dsn.split(' ')[0]}...")

    funds = load_json("funds")
    subset_ids = None
    if subset:
        subset_ids = {f["fund_id"] for f in funds[:subset]}
        funds = [f for f in funds if f["fund_id"] in subset_ids]
        log.info(f"--subset {subset}: dibatasi ke {len(subset_ids)} fund_id")

    def keep(rows, key="fund_id"):
        return rows if subset_ids is None else [r for r in rows if r[key] in subset_ids]

    def keep_by_snapshot_fund(rows):
        return rows if subset_ids is None else [r for r in rows if r["snapshot_ref"][0] in subset_ids]

    # Tahap 1 (tanpa FK)
    bulk_upsert(conn, "investment_manager",
        ["manager_id", "name", "ojk_code", "mi_permit_num", "ppe_permit_num", "pee_permit_num",
         "description", "address", "telephone", "fax", "email", "website_url",
         "capital", "paid_in_capital", "is_active", "data_last_update"],
        load_json("investment_managers"), ["manager_id"], do_update=True, bump_scraped_at=True)

    # bank_id=10 punya telephone berisi beberapa nomor sekaligus (55 char),
    # melebihi VARCHAR(50) - dipotong, bukan menaikkan batas kolom.
    custodian_banks = load_json("custodian_banks")
    for b in custodian_banks:
        if b.get("telephone") and len(b["telephone"]) > TELEPHONE_MAX_LEN:
            log.info(f"custodian_bank {b['bank_id']}: telephone dipotong ke {TELEPHONE_MAX_LEN} char")
            b["telephone"] = b["telephone"][:TELEPHONE_MAX_LEN]

    bulk_upsert(conn, "custodian_bank",
        ["bank_id", "name", "ojk_code", "description", "address", "telephone", "fax", "email",
         "website_url", "niu_bank_umum", "niu_bk", "date_start_sk", "ownership_status",
         "activity_status", "is_active", "data_last_update"],
        custodian_banks, ["bank_id"], do_update=True, bump_scraped_at=True)

    bulk_upsert(conn, "sales_company",
        ["company_id", "name", "aperd_id", "npwp", "no_sttd_sk", "date_sttd_sk", "address",
         "telephone", "fax", "email", "website_url", "contact_person"],
        load_json("sales_companies"), ["company_id"], do_update=True, bump_scraped_at=True)

    bulk_upsert(conn, "benchmark", ["benchmark_id", "name"],
        load_json("benchmarks"), ["benchmark_id"], do_update=False)

    # asset_category.name UNIQUE, tapi category_id=7 dan =9 sama-sama berlabel
    # "Pasar Uang" di data/*.json. BUKAN duplikat murni: pada fund 2624 & 4155
    # keduanya muncul BERSAMAAN di snapshot yang sama (mis. 0.15% + 99.85% =
    # 100%) - menggabungkan id akan merusak invarian "Type 0 total = 100%"
    # (KD-5). Dicek raw JSON (Data Scraping/raw/portfolio/): SpesificType=9
    # cuma muncul di 3 fund sumber (2416="Pasar Uang", 2624 & 4155="Real
    # Estate") - mayoritas sebenarnya "Real Estate", preprocessor.py cuma
    # kebetulan pilih nama minoritas saat dedup. Override manual di sini,
    # bukan suffix generik "(9)".
    CATEGORY_NAME_OVERRIDE = {9: "Real Estate"}
    asset_categories = load_json("asset_categories")
    seen_names = set()
    for r in sorted(asset_categories, key=lambda r: r["category_id"]):
        if r["category_id"] in CATEGORY_NAME_OVERRIDE:
            r["name"] = CATEGORY_NAME_OVERRIDE[r["category_id"]]
        elif r["name"] in seen_names:
            log.info(f"asset_category {r['category_id']}: nama '{r['name']}' didisambiguasi (duplikat label)")
            r["name"] = f"{r['name']} ({r['category_id']})"
        seen_names.add(r["name"])

    bulk_upsert(conn, "asset_category", ["category_id", "name"],
        asset_categories, ["category_id"], do_update=True)

    bulk_upsert(conn, "security", ["security_id", "code", "name", "security_type", "source_stock_id"],
        load_json("securities"), ["security_id"], do_update=True)

    bulk_upsert(conn, "fund_class", ["class_group_id", "base_name"],
        load_json("fund_classes"), ["class_group_id"], do_update=True)

    # Tahap 2 (FK→1)
    refresh_child(conn, "manager_personnel", ["manager_id", "name", "title"],
        load_json("manager_personnel"), parent_col="manager_id")

    refresh_child(conn, "manager_shareholder", ["manager_id", "shareholder_name", "share_amount"],
        load_json("manager_shareholders"), parent_col="manager_id")

    bulk_upsert(conn, "manager_aum_record",
        ["manager_id", "record_date", "aum_value", "total_units"],
        load_json("manager_aum_records"), ["manager_id", "record_date"], do_update=False)

    fix_negative_min_next_subscription(funds)

    fee_fields = ["sub_fee_max_pct", "red_fee_max_pct", "switching_fee_max_pct",
                  "manager_fee_max_pct", "custodian_fee_max_pct"]
    fix_unreasonable_fees(funds, fee_fields)

    dedupe_isin_code(funds)

    policy_fields = ["policy_bond_pct", "policy_equity_pct", "policy_money_market_pct"]
    fix_policy_pct_range(funds, policy_fields)

    bulk_upsert(conn, "mutual_fund",
        ["fund_id", "manager_id", "bank_id", "class_group_id", "name", "class_name", "isin_code",
         "bloomberg_quote", "fund_type", "currency", "is_sharia", "is_etf", "is_index",
         "has_dividend", "is_active", "ipo_date", "description", "official_benchmark",
         "min_subscription", "min_next_subscription", "min_redemption", "min_balance",
         "sub_fee_max_pct", "red_fee_max_pct", "switching_fee_max_pct", "manager_fee_max_pct",
         "custodian_fee_max_pct", "policy_bond_pct", "policy_equity_pct",
         "policy_money_market_pct", "last_update"],
        funds, ["fund_id"], do_update=True, bump_scraped_at=True)

    # Tahap 3 (FK→2)
    bulk_upsert(conn, "nav_record", ["fund_id", "record_date", "nav_value", "class_total_value"],
        keep(load_json("nav_records")), ["fund_id", "record_date"], do_update=False)

    bulk_upsert(conn, "aum_record",
        ["fund_id", "record_date", "published_date", "aum_value", "total_units", "class_total_value"],
        keep(load_json("aum_records")), ["fund_id", "record_date"], do_update=False)

    snap_map = load_snapshots(conn, keep(load_json("portfolio_snapshots")))

    performances = keep(load_json("fund_performances"))
    fix_treynor_outlier(performances)

    bulk_upsert(conn, "fund_performance",
        ["fund_id", "period_code", "as_of_date", "return_pct", "std_dev", "beta", "sharpe_ratio",
         "modified_sharpe_ratio", "treynor_ratio", "sortino_ratio", "tracking_error",
         "max_drawdown", "cagr", "jensen_alpha"],
        performances, ["fund_id", "period_code", "as_of_date"], do_update=True)

    rankings = keep(load_json("fund_rankings"))
    zero_fields = ["risk_rank", "rating_rank", "all_risk_rank",
                   "pasardana_rating", "risk_rating", "all_risk_rating"]
    filtered_rankings = filter_sentinel_zero_rankings(rankings, zero_fields)

    bulk_upsert(conn, "fund_ranking",
        ["fund_id", "period_code", "category_code", "as_of_date", "risk_rank", "rating_rank",
         "all_risk_rank", "pasardana_rating", "risk_rating", "all_risk_rating"],
        filtered_rankings, ["fund_id", "period_code", "category_code", "as_of_date"], do_update=True)

    bulk_upsert(conn, "fund_quarterly_return", ["fund_id", "quarter_start", "return_pct"],
        keep(load_json("fund_quarterly_returns")), ["fund_id", "quarter_start"], do_update=True)

    bulk_upsert(conn, "benchmark_data_point", ["benchmark_id", "record_date", "value"],
        load_json("benchmark_data_points"), ["benchmark_id", "record_date"], do_update=False)

    bulk_upsert(conn, "fund_benchmark", ["fund_id", "benchmark_id", "is_official"],
        keep(load_json("fund_benchmarks")), ["fund_id", "benchmark_id"], do_update=True)

    bulk_upsert(conn, "fund_sales_company", ["fund_id", "company_id", "commission_fee"],
        keep(load_json("fund_sales_companies")), ["fund_id", "company_id"], do_update=True)

    # Tahap 4 (FK→1 & 3)
    raw_allocations = aggregate_duplicates(keep_by_snapshot_fund(load_json("portfolio_allocations")), "category_id")
    allocations = resolve_snapshot_rows(raw_allocations, snap_map)
    bulk_upsert(conn, "portfolio_allocation", ["snapshot_id", "category_id", "value_pct"],
        allocations, ["snapshot_id", "category_id"], do_update=False)

    raw_holdings = aggregate_duplicates(keep_by_snapshot_fund(load_json("portfolio_holdings")), "security_id")
    holdings = resolve_snapshot_rows(raw_holdings, snap_map)
    bulk_upsert(conn, "portfolio_holding", ["snapshot_id", "security_id", "value_pct"],
        holdings, ["snapshot_id", "security_id"], do_update=False)

    # Tahap 5
    with conn.cursor() as cur:
        cur.execute("ANALYZE;")
    conn.commit()
    log.info("ANALYZE selesai")

    with conn.cursor() as cur:
        cur.execute("SELECT relname, n_live_tup FROM pg_stat_user_tables ORDER BY relname")
        log.info("Ringkasan baris per tabel:")
        for relname, n in cur.fetchall():
            log.info(f"  {relname:<28} {n}")

    conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--subset", type=int, default=None,
                         help="Batasi ke N fund_id pertama (uji coba)")
    args = parser.parse_args()
    main(args.subset)
