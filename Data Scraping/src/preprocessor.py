"""
preprocessor.py - Transform: raw JSON → clean JSON per entitas (22 file)

Input  : Data Scraping/raw/*.json   (output Extract, Phase 1-8)
Output : Data Scraping/data/*.json  (22 file, siap Load ke OLTP §7)

TIDAK menghitung atribut turunan:
  · daily_return        → VIEW v_nav_return (KD-1)
  · conservative_label  → GENERATED column, ditegakkan DBMS (KD-7)

Dibangun per-modul (panduan-implementasi.md Tahap 2): tiap entitas punya
fungsi transform terpisah. Bisa diuji dengan subset via argumen --subset N.

Jalankan:
  python preprocessor.py            # full
  python preprocessor.py --subset 20 # uji dengan 20 fund pertama
"""
import argparse
import calendar
import json
import logging
import re
from pathlib import Path
from typing import Any

# PATH
RAW_DIR = Path(__file__).resolve().parent.parent / "raw"
DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# LOGGING (rejects & sanity)
logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s",
)
log = logging.getLogger("transform")
rejects = []   # baris yang gagal validasi (§11.7) - dicatat, bukan di-raise

# KONSTANTA
# Kode fund_type API - dipakai di expected_label()
FUND_TYPE_MIXED = 0
FUND_TYPE_EQUITY = 1
FUND_TYPE_FIXED_INCOME = 2
FUND_TYPE_MONEY_MARKET = 3
FUND_TYPE_PROTECTED = 4
FUND_TYPE_GLOBAL = 7

# Toleransi selisih SUM allocation Type 0 vs 100% sebelum dianggap anomali sumber (§17.5)
ALLOCATION_SUM_TOLERANCE_PCT = 5


# ════════════════════════════════════════════════════════════════════════════
# HELPER: parsing tipe
# ════════════════════════════════════════════════════════════════════════════

def _is_dash(v):
    """Email/kontak "-" di API berarti tidak ada → null."""
    return v is None or (isinstance(v, str) and v.strip() == "-")


def parse_str_or_none(v, dash_null: bool = True) -> str | None:
    """Trim string, kembalikan None utk kosong. dash_null=True: '-' juga jadi None."""
    if dash_null and _is_dash(v):
        return None
    if v is None:
        return None
    s = str(v).strip()
    return s or None


def safe_list(d: dict, key: str) -> list:
    """d.get(key) yang selalu list - API sering kirim null, bukan [], utk field kosong."""
    return d.get(key) or []


def parse_int(v):
    """Rp / nilai absolut string → int. Bisa null."""
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return int(v)
    s = str(v).replace(".", "").replace(",", "").replace("Rp", "").replace(" ", "")
    digits = re.sub(r"[^0-9-]", "", s)
    return int(digits) if digits not in ("", "-") else None


def parse_float(v):
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", ".")          # desimal Eropa "2,00%" → "2.00"
    s = re.sub(r"[^0-9.\-]", "", s)
    return float(s) if s not in ("", "-") else None


def parse_fee_pct(v):
    """'Maks 0,30%' / '2,000%' → float persen. None bila tidak ter-parse."""
    if v is None:
        return None
    s = str(v).replace(",", ".")
    m = re.search(r"(-?\d+\.?\d*)", s)
    return float(m.group(1)) if m else None


def parse_date(v):
    """ISO '2005-05-25T00:00:00' → '2005-05-25'. '18-08-2023' → '2023-08-18'."""
    if not v:
        return None
    s = str(v)[:10]
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", s):
        return s
    # DD-MM-YYYY (DataLastUpdate)
    m = re.fullmatch(r"(\d{2})-(\d{2})-(\d{4})", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    return s   # simpan apa adanya bila format tak dikenal


def latest_nav_date(snap: dict) -> str | None:
    """Tanggal NAV terakhir di snapshot ini - jadi acuan as_of_date untuk
    fund_performance/fund_ranking. period_code cuma jenis rentang waktu
    (mis. "1 Tahun"), bukan tanggal - tanpa ini, ranking hari berbeda yang
    di-scrape ulang akan saling menimpa (lihat diskusi desain as_of_date)."""
    dates = [parse_date(n.get("Date")) for n in safe_list(snap, "NetAssetValues")]
    dates = [d for d in dates if d]
    return max(dates) if dates else None


def end_of_month(record_date: str) -> str:
    """Akhir bulan kalender dari record_date (YYYY-MM-DD) - dipakai sbg
    published_date. AUM pasardana selalu dipublikasikan per akhir bulan
    (terverifikasi: 100% AumPublishedDate di fund_index.json jatuh di hari
    terakhir bulan, dan UI fund menampilkan "As of 30 Juni 2026" utk
    periode "Juni 2026"). Dihitung per baris, bukan disalin dari
    fund_index_map - nilai itu cuma "kapan fund ini terakhir di-refresh
    keseluruhan", sama untuk semua bulan histori (bug: lihat diskusi
    published_date)."""
    y, m, _ = map(int, record_date.split("-"))
    last_day = calendar.monthrange(y, m)[1]
    return f"{y:04d}-{m:02d}-{last_day:02d}"


def load_raw(name: str) -> Any:
    """Muat satu file JSON dari raw/. None bila hilang (dicatat sbg warning)."""
    p = RAW_DIR / name
    if not p.exists():
        log.warning("file raw hilang: %s", name)
        return None
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def load_raw_dir(sub, key_fn=None):
    """Muat semua file JSON di raw/{sub}/. Lewati file _error / null."""
    d = RAW_DIR / sub
    if not d.exists():
        return {}
    out = {}
    for f in sorted(d.iterdir()):
        if f.suffix != ".json":
            continue
        try:
            with open(f, encoding="utf-8") as fh:
                data = json.load(fh)
        except Exception as e:
            log.warning("unreadable %s: %s", f.name, e)
            continue
        if isinstance(data, dict) and "_error" in data:
            continue                      # fetch gagal (audit Tahap 1) - skip
        if data is None:
            continue                      # snapshot null (fund 5229 matured)
        k = key_fn(f.stem) if key_fn else f.stem
        out[k] = data
    return out


def save(name: str, rows: list) -> None:
    """Tulis rows sbg JSON ke data/{name} (buat folder bila belum ada)."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / name, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False)
    log.info("  → data/%s : %s baris", name, f"{len(rows):,}")


# ════════════════════════════════════════════════════════════════════════════
# PHASE A: MASTER (investment_manager, personnel, shareholder, manager_aum,
#                   custodian_bank, sales_company)
# ════════════════════════════════════════════════════════════════════════════

def transform_investment_manager(managers: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    im, personnel, shareholders = [], [], []
    for m in managers:
        im.append({
            "manager_id":      m["Id"],
            "name":            m["Name"],
            "ojk_code":        m["OjkCode"],
            "mi_permit_num":   parse_str_or_none(m.get("MiPermitNum")),
            "ppe_permit_num":  parse_str_or_none(m.get("PpePermitNum")),
            "pee_permit_num":  parse_str_or_none(m.get("PeePermitNum")),
            "description":     m.get("Description"),
            "address":         m.get("Address"),
            "telephone":       parse_str_or_none(m.get("TelephoneNumber")),
            "fax":             parse_str_or_none(m.get("FaxNumber")),
            "email":           parse_str_or_none(m.get("Email")),
            "website_url":     parse_str_or_none(m.get("WebsiteUrl")),
            "capital":         parse_int(m.get("Capital")),
            "paid_in_capital": parse_int(m.get("PaidInCapital")),
            "is_active":       bool(m.get("IsActive", True)),
            "data_last_update": parse_date(m.get("DataLastUpdate")),
        })
        for p in safe_list(m, "Personnel"):
            personnel.append({
                "manager_id": m["Id"],
                "name":       p["Name"],
                "title":      p["Title"],
            })
        for sh in safe_list(m, "Share"):
            shareholders.append({
                "manager_id":      m["Id"],
                "shareholder_name": sh["Name"],
                "share_amount":    parse_int(sh.get("Share")),
            })
    return im, personnel, shareholders


def transform_manager_aum(manager_aum_dir: dict) -> list[dict]:
    rows = []
    for mgr_id, data in manager_aum_dir.items():
        for r in data:
            rows.append({
                "manager_id":  r.get("fkFundManager") or int(mgr_id),
                "record_date": parse_date(r.get("Date")),
                "aum_value":   float(r["Aum"]) if r.get("Aum") is not None else None,
                "total_units": float(r["TotalUnit"]) if r.get("TotalUnit") is not None else None,
            })
    # validasi (§11.7)
    rows = [r for r in rows if r["record_date"] and r["aum_value"] is not None and r["aum_value"] >= 0]
    return rows


def transform_custodian_bank(banks: list[dict]) -> list[dict]:
    rows = []
    for b in banks:
        rows.append({
            "bank_id":           b["Id"],
            "name":              b["Name"],
            "ojk_code":          parse_str_or_none(b.get("OjkCode")),
            "description":       b.get("Description"),
            "address":           b.get("Address"),
            "telephone":         parse_str_or_none(b.get("TelephoneNumber")),
            "fax":               parse_str_or_none(b.get("FaxNumber")),
            "email":             parse_str_or_none(b.get("Email")),
            "website_url":       parse_str_or_none(b.get("WebsiteUrl")),
            "niu_bank_umum":     parse_str_or_none(b.get("NiuBankUmum")),
            "niu_bk":            parse_str_or_none(b.get("NiuBk")),
            "date_start_sk":     parse_str_or_none(b.get("DateStartSk")),
            "ownership_status":  parse_str_or_none(b.get("OwnershipStatus")),
            "activity_status":   parse_str_or_none(b.get("ActivityStatus")),
            "is_active":         bool(b.get("IsActive", True)),
            "data_last_update":  parse_date(b.get("DataLastUpdate")),
        })
    return rows


def transform_sales_company(sales: list[dict]) -> list[dict]:
    rows = []
    for s in sales:
        rows.append({
            "company_id":      s["Id"],
            "name":            s["Name"],
            "aperd_id":        s["AperdId"],
            "npwp":            parse_str_or_none(s.get("Npwp")),
            "no_sttd_sk":      parse_str_or_none(s.get("NoSttdSk")),
            "date_sttd_sk":    parse_str_or_none(s.get("DateSttdSk")),
            "address":         s.get("Address"),
            "telephone":       parse_str_or_none(s.get("TelephoneNumber")),
            "fax":             parse_str_or_none(s.get("Fax")),
            "email":           parse_str_or_none(s.get("Email")),
            "website_url":      parse_str_or_none(s.get("WebsiteUrl")),
            "contact_person":  parse_str_or_none(s.get("ContactPerson")),
        })
    return rows


# ════════════════════════════════════════════════════════════════════════════
# PHASE B: fund_class (KD-3: FkClassFundId otoritatif) + mutual_fund
# ════════════════════════════════════════════════════════════════════════════

CLASS_RE = re.compile(r"\s+(kelas\s+.+)$", re.IGNORECASE)


def split_class(name: str) -> tuple[str, str | None]:
    """'Ashmore Dana Obligasi Nusantara Kelas A'
        → ('Ashmore Dana Obligasi Nusantara', 'Kelas A')"""
    m = CLASS_RE.search(name or "")
    if not m:
        return (name or "").strip(), None
    raw_class = m.group(1).strip()
    class_name = re.sub(r"^kelas\s+", "Kelas ", raw_class, flags=re.IGNORECASE)
    base_name = (name[:m.start()]).strip()
    return base_name, class_name


def build_class_map(products_dir: dict) -> dict:
    """fund_id → FkClassFundId dari raw/products/*.json (sumber otoritatif KD-3)."""
    class_map = {}
    for mgr_id, data in products_dir.items():
        if not isinstance(data, list):
            continue
        for item in data:
            f = item.get("Fund") or {}
            fid = f.get("Id")
            gid = f.get("FkClassFundId")
            if fid and gid:
                class_map[fid] = gid
    return class_map


def expected_label(fund_type: int | None, is_index: bool, is_etf: bool) -> str:
    """Aturan derivasi conservative_label (KD-7).
    Dipakai HANYA untuk sanity check vs ConservativeCategory API -
    bukan ditulis sebagai kolom (DBMS yang generate)."""
    if is_index:
        return "Indeks"
    if fund_type == FUND_TYPE_GLOBAL:
        return "Exchange Traded Fund" if is_etf else "Reksadana Global"
    return {
        FUND_TYPE_MIXED: "Campuran",
        FUND_TYPE_EQUITY: "Saham",
        FUND_TYPE_FIXED_INCOME: "Pendapatan Tetap",
        FUND_TYPE_MONEY_MARKET: "Pasar Uang",
        FUND_TYPE_PROTECTED: "Terproteksi",
    }.get(fund_type, "Lainnya")


def transform_funds(fund_index: list[dict], snapshots: dict, class_map: dict) -> tuple[list[dict], list[dict], int]:
    """Bangun mutual_fund + fund_class. Filter Id=0 (placeholder indeks, audit Tahap 1)."""
    funds = []
    fund_classes = {}        # class_group_id → base_name
    mismatch = 0
    checked = 0

    for f in fund_index:
        fid = f["Id"]
        if fid == 0:                     # placeholder indeks (IHSG, LQ45, …) - BUKAN fund
            continue
        snap = snapshots.get(fid) or {}
        det = snap.get("Detail") or {}
        gid = class_map.get(fid)         # None bila bukan multi-kelas
        base, cls = split_class(f["Name"])

        is_index = bool(f.get("Index"))
        is_etf = bool(f.get("ExchangeTradedFund"))
        fund_type = f.get("Type")

        # sanity check conservative_label (§11.2)
        if fund_type is not None:
            checked += 1
            exp = expected_label(fund_type, is_index, is_etf)
            if exp != f.get("ConservativeCategory"):
                mismatch += 1

        if gid and gid not in fund_classes:
            fund_classes[gid] = base

        funds.append({
            "fund_id":                  fid,
            "manager_id":               f["InvestmentManagerId"],
            "bank_id":                  f["CustodianBankId"],
            "class_group_id":           gid,
            "name":                     f["Name"],
            "class_name":               cls,
            "isin_code":                parse_str_or_none(f.get("IsinCode")),
            "bloomberg_quote":          parse_str_or_none(f.get("BloombergQuote")),
            "fund_type":                fund_type,
            "currency":                 f.get("Currency", 0),
            "is_sharia":                bool(f.get("Sharia", False)),
            "is_etf":                   is_etf,
            "is_index":                 is_index,
            "has_dividend":             bool(f.get("Dividend", False)),
            "is_active":                bool(det.get("IsActive", True)),
            "ipo_date":                 parse_date(det.get("IpoDate") or f.get("IpoDate")),
            "description":              det.get("Description"),
            "official_benchmark":       det.get("OfficialBenchmark"),
            "min_subscription":         parse_int(det.get("MinSubNum")),
            "min_next_subscription":    parse_int(det.get("MinNextSubNum")),
            "min_redemption":           parse_int(det.get("MinRedNum")),
            "min_balance":              parse_int(det.get("MinBalanceNum")),
            "sub_fee_max_pct":          parse_fee_pct(det.get("MaxSubscriptionFee")),
            "red_fee_max_pct":          parse_fee_pct(det.get("MaxRedemptionFee")),
            "switching_fee_max_pct":    parse_fee_pct(det.get("MaxSwitchingFee")),
            "manager_fee_max_pct":      parse_fee_pct(det.get("MaxInvestmentManagerFee")),
            "custodian_fee_max_pct":    parse_fee_pct(det.get("MaxCustodianBankFee")),
            "policy_bond_pct":          parse_float(det.get("InvestmentBond")),
            "policy_equity_pct":        parse_float(det.get("InvestmentEquity")),
            "policy_money_market_pct": parse_float(det.get("InvestmentMoneyMarket")),
            "last_update":              parse_date(f.get("LastUpdate")),
            # conservative_label TIDAK ditulis - GENERATED column (KD-7)
        })

    pct = (mismatch / checked * 100) if checked else 0
    log.info("  conservative_label sanity: %d/%d mismatch (%.1f%%) - %s",
             mismatch, checked, pct,
             "aturan OK" if pct <= 5 else "PERLU TINJAUAN (>5%)")
    fund_class_rows = [{"class_group_id": g, "base_name": n}
                       for g, n in sorted(fund_classes.items())]
    return funds, fund_class_rows, mismatch


# ════════════════════════════════════════════════════════════════════════════
# PHASE C: TIME SERIES (nav_record, aum_record)
# ════════════════════════════════════════════════════════════════════════════

def transform_nav(snapshots: dict) -> list[dict]:
    rows = []
    rejected = 0
    for fid, snap in snapshots.items():
        if fid == 0:
            continue
        for n in safe_list(snap, "NetAssetValues"):
            val = n.get("Value")
            if val is None or val <= 0:        # §11.7: nav_value > 0
                rejected += 1
                continue
            rows.append({
                "fund_id":          fid,
                "record_date":      parse_date(n.get("Date")),
                "nav_value":        float(val),
                "class_total_value": (float(n["ClassTotalValue"])
                                      if n.get("ClassTotalValue") is not None else None),
                # daily_return TIDAK disimpan (KD-1)
            })
    rows = [r for r in rows if r["record_date"]]
    rejects.append(("nav_value", rejected))
    return rows


def transform_aum(snapshots: dict) -> list[dict]:
    """aum_record (§4.10): record_date = AUM[].Date (label periode, awal bulan),
    published_date = end_of_month(record_date) - dihitung per baris, bukan
    disalin dari AumPublishedDate (fund_index), yang cuma satu nilai per fund
    dan sama untuk semua bulan histori (bug lama, lihat diskusi
    published_date). aum_value dari AssetUnderManagements[].Value,
    total_units dari TotalUnits[].Value (array terpisah, dicocokkan per
    Date)."""
    rows = []
    rejected = 0
    for fid, snap in snapshots.items():
        if fid == 0:
            continue
        aums = safe_list(snap, "AssetUnderManagements")
        units = {parse_date(u.get("Date")): u.get("Value")
                 for u in safe_list(snap, "TotalUnits")}
        for a in aums:
            rdate = parse_date(a.get("Date"))
            val = a.get("Value")
            if val is None or val < 0:        # §11.7
                rejected += 1
                continue
            rows.append({
                "fund_id":          fid,
                "record_date":      rdate,
                "published_date":   end_of_month(rdate),
                "aum_value":        int(val),
                "total_units":      (float(units[rdate]) if rdate in units else None),
                "class_total_value": (int(a["ClassTotalValue"])
                                      if a.get("ClassTotalValue") is not None else None),
            })
    rows = [r for r in rows if r["record_date"]]
    rejects.append(("aum_value", rejected))
    return rows


# ════════════════════════════════════════════════════════════════════════════
# PHASE D: PORTFOLIO (snapshot, allocation Type 0, holding Type 1/2)
#            + master asset_category, security
# ════════════════════════════════════════════════════════════════════════════

def transform_portfolio(portfolios_dir: dict, valid_fund_ids: set) -> tuple[list, list, list, list, list]:
    """Pass 1: kumpulkan master asset_category + security dari seluruh snapshot.
    Pass 2: split Assets[] → portfolio_snapshot + allocation + holding.
    Dedup security by code (Id API = 0, tidak reliable).

    Catatan kualitas data sumber (§17.5): pasardana tidak menjamin konsistensi
    aritmatika disclosure - sebagian snapshot punya allocation ≠100% (mis.
    87% parsial) atau holding >100% (mis. 105% akibat pembulatan/overlap).
    Tidak ada baris individual yang bisa di-drop dgn benar (semua 0-100 valid),
    jadi disimpan apa adanya; anomali dicatat (opsi A) & dibatasi DBMS CHECK
    per-baris. Daftar lengkap: docs/snapshot-anomali.md."""
    asset_categories = {}     # category_id → name
    securities = {}           # code → {code,name,security_type,source_stock_id}
    snapshots = []
    allocations = []
    holdings = []
    anomaly_alloc = 0         # snapshot dgn allocation Type0 ≠100% (§17.5)
    anomaly_hold = 0          # snapshot dgn holding >100% (§17.5)

    # Pass 0: flatten
    all_snaps = []
    for fid, snaps in portfolios_dir.items():
        if fid not in valid_fund_ids:
            continue
        if not isinstance(snaps, list):
            continue
        for s in snaps:
            date_based = parse_date(s.get("DateBased"))
            if not date_based:
                continue
            all_snaps.append({
                "fund_id":    fid,
                "date_based": date_based,
                "domestic":   s.get("DomesticAllocation"),
                "foreign":    s.get("ForeignAllocation"),
                "assets":     safe_list(s, "Assets"),
            })

    # Pass 1: master
    for snap in all_snaps:
        for a in snap["assets"]:
            t = a.get("Type")
            if t == 0:
                cid = a.get("SpesificType")
                if cid is not None and cid not in asset_categories:
                    asset_categories[cid] = a.get("Name")
            elif t in (1, 2):
                if t == 1:
                    stock = a.get("Stock") or {}
                    code = stock.get("Code")
                    name = stock.get("Name") or a.get("Name")
                    src = a.get("fkStockId")
                else:
                    code = a.get("Name")
                    name = a.get("Name")
                    src = None
                if code and code not in securities:
                    securities[code] = {
                        "code": code, "name": name,
                        "security_type": t, "source_stock_id": src,
                    }

    # security_id berurutan setelah dedup
    for i, code in enumerate(sorted(securities), start=1):
        securities[code]["security_id"] = i

    # Pass 2: split
    for snap in all_snaps:
        key = (snap["fund_id"], snap["date_based"])
        snapshots.append({
            "fund_id": snap["fund_id"],
            "date_based": snap["date_based"],
            "domestic_allocation_pct": parse_float(snap["domestic"]),
            "foreign_allocation_pct":  parse_float(snap["foreign"]),
        })
        alloc_sum = 0.0          # Type 0 yang lolos validasi (§17.5 anomaly check)
        hold_sum = 0.0
        for a in snap["assets"]:
            t = a.get("Type")
            val = a.get("Value")
            if val is None or not (0 <= val <= 100):    # §11.7
                continue
            if t == 0 and a.get("SpesificType") is not None:
                allocations.append({
                    "snapshot_ref": key,
                    "category_id":  a["SpesificType"],
                    "value_pct":     float(val),
                })
                alloc_sum += val
            elif t in (1, 2):
                code = (a.get("Stock") or {}).get("Code") if t == 1 else a.get("Name")
                if code and code in securities:
                    holdings.append({
                        "snapshot_ref": key,
                        "security_id":  securities[code]["security_id"],
                        "value_pct":    float(val),
                    })
                    hold_sum += val
        # catat anomali sumber (§17.5) - bukan di-drop, hanya didokumentasikan
        if abs(alloc_sum - 100) > ALLOCATION_SUM_TOLERANCE_PCT:
            anomaly_alloc += 1
        if hold_sum > 100:
            anomaly_hold += 1

    asset_cat_rows = [{"category_id": cid, "name": nm}
                      for cid, nm in sorted(asset_categories.items())]
    security_rows = [securities[c] for c in sorted(securities)]
    log.info("  anomali sumber (§17.5, disimpan bukan di-drop): "
             "allocation≠100%%=%d snapshot, holding>100%%=%d snapshot "
             "(detail: docs/snapshot-anomali.md)", anomaly_alloc, anomaly_hold)
    return snapshots, asset_cat_rows, security_rows, allocations, holdings


# ════════════════════════════════════════════════════════════════════════════
# PHASE E: fund_performance, fund_ranking, benchmark, fund_benchmark
# ════════════════════════════════════════════════════════════════════════════

def transform_performance(snapshots: dict) -> list[dict]:
    rows = []
    for fid, snap in snapshots.items():
        if fid == 0:
            continue
        as_of = latest_nav_date(snap)
        for p in safe_list(snap, "Performances"):
            rows.append({
                "fund_id":                fid,
                "period_code":             p.get("Period"),
                "as_of_date":            as_of,
                "return_pct":             p.get("Return"),
                "std_dev":                p.get("StandardDeviation"),
                "beta":                  p.get("Beta"),
                "sharpe_ratio":          p.get("SharpeRatio"),
                "modified_sharpe_ratio": p.get("ModifiedSharpeRatio"),
                "treynor_ratio":         p.get("TreynorRatio"),
                "sortino_ratio":         p.get("SortinoRatio"),
                "tracking_error":        p.get("TrackingError"),
                "max_drawdown":          p.get("MaxDrawdown"),
                "cagr":                  p.get("Cagr"),
                "jensen_alpha":          p.get("JensenAlpha"),
            })
    rows = [r for r in rows if r["period_code"] is not None and r["as_of_date"]]
    return rows


def transform_ranking(snapshots: dict) -> list[dict]:
    rows = []
    for fid, snap in snapshots.items():
        if fid == 0:
            continue
        as_of = latest_nav_date(snap)
        for r in safe_list(snap, "Rankings"):
            rows.append({
                "fund_id":          fid,
                "period_code":      r.get("Period"),
                "category_code":    r.get("Category", 0),
                "as_of_date":       as_of,
                "risk_rank":        r.get("RiskRank"),
                "rating_rank":      r.get("RatingRank"),
                "all_risk_rank":    r.get("AllRiskRank"),
                "pasardana_rating": r.get("PasardanaRating"),
                "risk_rating":      r.get("RiskRating"),
                "all_risk_rating":  r.get("AllRiskRating"),
            })
    rows = [r for r in rows if r["period_code"] is not None and r["as_of_date"]]
    return rows


def transform_benchmark(snapshots: dict) -> tuple[list[dict], list[dict], list[dict]]:
    """benchmark (master) + benchmark_data_point + fund_benchmark (junction).
    Benchmarks[] tiap snapshot berisi data historis benchmark acuan fund tsb."""
    bench = {}          # benchmark_id → name
    data_points = []    # (benchmark_id, record_date) → value  (dedup dulu)
    dp_seen = set()
    fund_bench = []     # (fund_id, benchmark_id) → is_official
    fb_seen = set()

    for fid, snap in snapshots.items():
        if fid == 0:
            continue
        for b in safe_list(snap, "Benchmarks"):
            bid = b.get("Id")
            if bid is None:
                continue
            bench[bid] = b.get("Name")
            for d in safe_list(b, "Data"):
                rdate = parse_date(d.get("Date"))
                if not rdate:
                    continue
                key = (bid, rdate)
                if key in dp_seen:
                    continue
                dp_seen.add(key)
                data_points.append({
                    "benchmark_id": bid,
                    "record_date":  rdate,
                    "value":       float(d["Value"]) if d.get("Value") is not None else None,
                })
            # fund_benchmark: tiap benchmark di snapshot fund ini adalah acuan
            key = (fid, bid)
            if key not in fb_seen:
                fb_seen.add(key)
                # benchmark resmi = top.Benchmark (singular) id, bila ada
                official_id = (snap.get("Benchmark") or {}).get("Id")
                fund_bench.append({
                    "fund_id":      fid,
                    "benchmark_id": bid,
                    "is_official":  (bid == official_id),
                })

    bench_rows = [{"benchmark_id": k, "name": v} for k, v in sorted(bench.items())]
    data_points.sort(key=lambda r: (r["benchmark_id"], r["record_date"]))
    return bench_rows, data_points, fund_bench


# ════════════════════════════════════════════════════════════════════════════
# PHASE F: fund_quarterly_return (skip Value null)
# ════════════════════════════════════════════════════════════════════════════

def transform_quarterly(quarterly_dir: dict, valid_fund_ids: set) -> tuple[list[dict], int]:
    rows = []
    skipped_null = 0
    # quarterly_dir: key="1887_2026" → data (list). Iterasi per file.
    for stem, data in quarterly_dir.items():
        fid = int(stem.split("_")[0])
        if fid not in valid_fund_ids or not isinstance(data, list):
            continue
        for q in data:
            val = q.get("Value")
            if val is None:                 # kuartal belum berjalan → skip (§4.21)
                skipped_null += 1
                continue
            rdate = parse_date(q.get("Date"))
            if not rdate:
                continue
            rows.append({
                "fund_id":       fid,
                "quarter_start": rdate,
                "return_pct":    float(val),
            })
    return rows, skipped_null


# ════════════════════════════════════════════════════════════════════════════
# PHASE G: fund_sales_company (flatten nested)
# ════════════════════════════════════════════════════════════════════════════

def transform_fund_sales(sales_dir: dict, valid_fund_ids: set) -> list[dict]:
    """Panen SELURUH relasi dari FundSalesCompanyFunds[] (nested).
    Hanya simpan relasi ke fund_id yang valid (FK integrity)."""
    fund_sales = {}   # (fund_id, company_id) → commission_fee
    for stem, resp in sales_dir.items():
        if not isinstance(resp, list):
            continue
        for item in resp:
            fsc = item.get("FundSalesCompany") or {}
            for link in safe_list(fsc, "FundSalesCompanyFunds"):
                key = (link.get("fkFundId"), link.get("fkFundSalesCompanyId"))
                if key[0] in valid_fund_ids:
                    fund_sales[key] = link.get("CommissionFee")
    rows = [{"fund_id": k[0], "company_id": k[1], "commission_fee": v}
            for k, v in fund_sales.items()]
    return rows


# ════════════════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════════════════

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subset", type=int, default=None,
                    help="uji hanya N fund pertama (validasi sebelum full)")
    args = ap.parse_args()

    log.info("=" * 64)
    log.info("TRANSFORM: raw/ → data/")
    log.info("=" * 64)

    # load raw master
    managers    = load_raw("managers.json") or []
    banks       = load_raw("banks.json") or []
    sales       = load_raw("sales.json") or []
    fund_index  = load_raw("fund_index.json") or []

    # filter placeholder Id=0 (audit Tahap 1)
    real_funds_idx = [f for f in fund_index if f["Id"] != 0]
    if args.subset:
        real_funds_idx = real_funds_idx[:args.subset]
        log.info("MODE SUBSET: %d fund pertama", args.subset)
    subset_ids = {f["Id"] for f in real_funds_idx}

    log.info("raw dimuat: %d MI, %d bank, %d APERD, %d fund (real)",
             len(managers), len(banks), len(sales), len(subset_ids))

    # load raw per-fund dirs (hanya fund di subset)
    snapshots = load_raw_dir("snapshot", key_fn=lambda s: int(s))
    snapshots = {k: v for k, v in snapshots.items() if k in subset_ids}
    portfolios = load_raw_dir("portfolio", key_fn=lambda s: int(s))
    portfolios = {k: v for k, v in portfolios.items() if k in subset_ids}
    quarterly = load_raw_dir("quarterly", key_fn=lambda s: s)   # key "fid_year"
    manager_aum = load_raw_dir("manager_aum", key_fn=lambda s: int(s))
    products = load_raw_dir("products", key_fn=lambda s: int(s))
    sales_companies = load_raw_dir("sales_companies", key_fn=lambda s: int(s))

    log.info("raw per-fund: snapshot=%d portfolio=%d quarterly-files=%d",
             len(snapshots), len(portfolios), len(quarterly))

    # A. master
    log.info("\n[1/10] Master: investment_manager + personnel + shareholder")
    im, personnel, shareholders = transform_investment_manager(managers)
    save("investment_managers.json", im)
    save("manager_personnel.json", personnel)
    save("manager_shareholders.json", shareholders)

    log.info("[2/10] Master: manager_aum_record")
    save("manager_aum_records.json", transform_manager_aum(manager_aum))

    log.info("[3/10] Master: custodian_bank + sales_company")
    save("custodian_banks.json", transform_custodian_bank(banks))
    save("sales_companies.json", transform_sales_company(sales))

    # B. fund_class + mutual_fund
    log.info("\n[4/10] fund_class (KD-3) + mutual_fund")
    class_map = build_class_map(products)
    log.info("  class_map: %d fund punya FkClassFundId", len(class_map))
    funds, fund_classes, _ = transform_funds(real_funds_idx, snapshots, class_map)
    save("fund_classes.json", fund_classes)
    save("funds.json", funds)
    valid_fund_ids = {f["fund_id"] for f in funds}

    # C. time series
    log.info("\n[5/10] nav_record + aum_record")
    save("nav_records.json", transform_nav(snapshots))
    save("aum_records.json", transform_aum(snapshots))

    # D. portfolio
    log.info("\n[6/10] portfolio_snapshot + asset_category + security + allocation + holding")
    snaps, cats, secs, allocs, holds = transform_portfolio(portfolios, valid_fund_ids)
    save("portfolio_snapshots.json", snaps)
    save("asset_categories.json", cats)
    save("securities.json", secs)
    save("portfolio_allocations.json", allocs)
    save("portfolio_holdings.json", holds)

    # E. performance, ranking, benchmark
    log.info("\n[7/10] fund_performance + fund_ranking")
    save("fund_performances.json", transform_performance(snapshots))
    save("fund_rankings.json", transform_ranking(snapshots))

    log.info("[8/10] benchmark + benchmark_data_point + fund_benchmark")
    bmk, bdp, fb = transform_benchmark(snapshots)
    save("benchmarks.json", bmk)
    save("benchmark_data_points.json", bdp)
    save("fund_benchmarks.json", fb)

    # F. quarterly
    log.info("\n[9/10] fund_quarterly_return")
    qrows, qnull = transform_quarterly(quarterly, valid_fund_ids)
    log.info("  quarterly: %d baris, %d kuartal-null di-skip (§4.21)", len(qrows), qnull)
    save("fund_quarterly_returns.json", qrows)

    # G. junction fund↔APERD
    log.info("\n[10/10] fund_sales_company (flatten nested)")
    save("fund_sales_companies.json",
         transform_fund_sales(sales_companies, valid_fund_ids))

    # rejects + checkpoint
    if rejects:
        log.info("\nbaris ditolak validasi (§11.7)")
        for name, n in rejects:
            log.info("  %s: %d", name, n)

    print_checkpoints(snaps, allocs, holds)

    log.info("\n" + "=" * 64)
    log.info("TRANSFORM SELESAI - 22 file di data/")
    log.info("=" * 64)


def print_checkpoints(snaps, allocs, holds):
    """Checkpoint panduan Tahap 2 - angka, bukan cuma 'tidak error'."""
    log.info("\nCHECKPOINT (panduan Tahap 2)")
    # (1) allocation per snapshot ≈ 100%
    from collections import defaultdict
    alloc_sum = defaultdict(float)
    for a in allocs:
        alloc_sum[tuple(a["snapshot_ref"])] += a["value_pct"]
    if alloc_sum:
        vals = list(alloc_sum.values())
        off100 = sum(1 for v in vals if abs(v - 100) > ALLOCATION_SUM_TOLERANCE_PCT)
        log.info("  [1] allocation SUM per snapshot: n=%d, ≈100%%: %d, "
                 "meleset>5%%: %d (sisanya: anomali sumber §17.5, bukan bug split)",
                 len(vals), len(vals) - off100, off100)
    # (2) holding parsial (jauh < 100%)
    hold_sum = defaultdict(float)
    for h in holds:
        hold_sum[tuple(h["snapshot_ref"])] += h["value_pct"]
    if hold_sum:
        hv = list(hold_sum.values())
        log.info("  [2] holding SUM per snapshot: n=%d, min=%.1f max=%.1f "
                 "(parsial, BUKAN harus 100%%; yg >100%% = anomali sumber §17.5)",
                 len(hv), min(hv), max(hv))
    log.info("  [3] total_units checksum: jalankan di DB via v_aum_integrity (§7.2)")


if __name__ == "__main__":
    main()
