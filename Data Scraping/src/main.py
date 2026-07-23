"""
main.py: Orchestrator Extract, semua Phase (1-8)

Jalankan: python main.py                     # full, semua 8 phase
          python main.py --phases 5 --force   # cuma phase 5, paksa re-fetch
                                               # (dipakai Airflow DAG, Tahap 6)

Resume-check: tiap file raw dicek duluan sebelum fetch - aman dihentikan
(Ctrl+C) dan dijalankan ulang tanpa mengulang call yang sudah berhasil.
--force melewati resume-check ini (re-fetch walau file sudah ada) - dipakai
untuk refresh incremental berkala, BUKAN initial load (yang justru butuh
resume-check untuk aman di-restart kalau crash di tengah jalan).

Konfigurasikan perilaku di blok KONFIGURASI di bawah sebelum menjalankan.
"""
import argparse
import asyncio
import json
from pathlib import Path

from session import create_session, close_session
import endpoints

# LOKASI RAW OUTPUT
# Relatif terhadap lokasi file ini - main.py ada di Data Scraping/src/,
# sehingga raw/ jadi Data Scraping/raw/ (satu level di atas src/).
RAW_DIR = Path(__file__).resolve().parent.parent / "raw"

# KONFIGURASI
# Set ke None untuk jalankan penuh; set ke angka untuk subset (validasi awal).
PHASE_4_SUBSET_SIZE   = None   # fund class per MI (~100 MI)
PHASE_5_SUBSET_SIZE   = None   # snapshot per fund - None setelah subset lulus
PHASE_6_SUBSET_SIZE   = None   # portfolio historis
PHASE_7_SUBSET_SIZE   = None   # return kuartalan
PHASE_8_SEED_FUND_IDS = None   # kalau None, pakai 20 fund pertama dari fund_index

QUARTERLY_YEARS       = [2022, 2023, 2024, 2025, 2026]
SLEEP_DEFAULT         = 1.0    # detik antar call (Phase 3, 4, 8)
SLEEP_SNAPSHOT        = 1.5    # detik antar call (Phase 5 - endpoint lebih berat)
SLEEP_PORTFOLIO       = 1.2    # detik antar call (Phase 6 - endpoint lebih berat)
SLEEP_QUARTERLY       = 0.5    # detik antar call per worker (Phase 7)
PROGRESS_LOG_EVERY    = 50     # cetak progres tiap N fetch (Phase 5, 6) - selain 5 pertama
PROGRESS_LOG_EVERY_QUARTERLY = 200  # cetak progres tiap N fetch (Phase 7) - selain 3 pertama


# HELPERS

def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


def load_json(name: str):
    with open(RAW_DIR / name, encoding="utf-8") as f:
        return json.load(f)


def already_scraped(path: Path) -> bool:
    return path.exists()


def load_fund_ids() -> list[int]:
    return [f["Id"] for f in load_json("fund_index.json")]


def load_manager_ids() -> list[int]:
    return [m["Id"] for m in load_json("managers.json")]


def apply_subset(items: list, size: int | None, label: str) -> list:
    if size is not None and size < len(items):
        print(f"  MODE SUBSET: {size}/{len(items)} {label} "
              f"(set ke None untuk jalankan penuh)")
        return items[:size]
    return items


async def _scrape_loop(page, items: list, out_dir: Path, fetch_fn, item_label: str,
                        sleep_s: float, force: bool, success_msg=None,
                        track_empty: bool = False) -> tuple[int, int, int]:
    """Loop generik dipakai Phase 3/4/5/6/8: skip-if-scraped → fetch → simpan
    → sleep. Tiap phase beda fetch_fn/pesan/jeda, tapi kerangkanya sama.

    success_msg(i, total, item_id, data, fetched, skipped) -> str | None,
    dipanggil sesudah fetch sukses (return None utk skip cetak baris itu).
    track_empty: True bila data=[] dihitung sbg "kosong" bukan "diambil"
    (Phase 6 - 1 call bisa balas array kosong utk fund yang belum delisting
    tapi belum ada histori portofolio)."""
    fetched = skipped = empty = 0
    total = len(items)
    for i, item_id in enumerate(items, 1):
        path = out_dir / f"{item_id}.json"
        if already_scraped(path) and not force:
            skipped += 1
            continue
        try:
            data = await fetch_fn(page, item_id)
        except Exception as e:
            print(f"  [{i}/{total}] {item_label} {item_id} "
                  f"GAGAL ({type(e).__name__}): {e} - skip.")
            save_json(path, {"_error": str(e)})
            await asyncio.sleep(sleep_s)
            continue
        save_json(path, data)
        if track_empty and not data:
            empty += 1
        else:
            fetched += 1
            if success_msg:
                msg = success_msg(i, total, item_id, data, fetched, skipped)
                if msg:
                    print(msg)
        await asyncio.sleep(sleep_s)

    if track_empty:
        print(f"  Selesai: {fetched} berisi data, {empty} kosong [], {skipped} skip.")
    else:
        print(f"  Selesai: {fetched} diambil, {skipped} skip.")
    return fetched, skipped, empty


# PHASE 1: Master (3 call)

async def run_phase_1(page, force: bool = False) -> None:
    print("\n=== PHASE 1: Master (3 call) ===")
    tasks = [
        ("managers.json", "FundInvestmentManager/GetAll", endpoints.get_investment_managers),
        ("banks.json",    "FundCustodianBank/GetAll",     endpoints.get_custodian_banks),
        ("sales.json",    "FundSalesCompany/GetAll",      endpoints.get_sales_companies),
    ]
    for filename, label, fn in tasks:
        path = RAW_DIR / filename
        if already_scraped(path) and not force:
            print(f"  {filename}: sudah ada, skip.")
        else:
            print(f"  Fetch: {label} ...")
            data = await fn(page)
            save_json(path, data)
            print(f"  disimpan: {filename} ({len(data)} item)")


# PHASE 2: Fund List

async def run_phase_2(page, force: bool = False) -> None:
    print("\n=== PHASE 2: Fund List (paginated) ===")
    path = RAW_DIR / "fund_index.json"
    if already_scraped(path) and not force:
        print(f"  fund_index.json: sudah ada, skip.")
        return
    data = await endpoints.get_fund_list(page)
    save_json(path, data)
    print(f"  disimpan: fund_index.json ({len(data)} fund)")


# PHASE 3: AUM level MI

async def run_phase_3(page, subset_size: int | None = None, force: bool = False) -> None:
    print("\n=== PHASE 3: AUM level MI ===")
    manager_ids = apply_subset(load_manager_ids(), subset_size, "MI")
    await _scrape_loop(
        page, manager_ids, RAW_DIR / "manager_aum", endpoints.get_manager_aum,
        item_label="manager", sleep_s=SLEEP_DEFAULT, force=force,
        success_msg=lambda i, total, mgr_id, data, fetched, skipped:
            f"  [{i}/{total}] manager {mgr_id}: {len(data)} baris AUM",
    )


# PHASE 4: Fund Class per MI

async def run_phase_4(page, subset_size: int | None = None, force: bool = False) -> None:
    print("\n=== PHASE 4: Fund Class per MI (FkClassFundId) ===")
    manager_ids = apply_subset(load_manager_ids(), subset_size, "MI")
    await _scrape_loop(
        page, manager_ids, RAW_DIR / "products", endpoints.get_products_data,
        item_label="manager", sleep_s=SLEEP_DEFAULT, force=force,
        success_msg=lambda i, total, mgr_id, data, fetched, skipped:
            f"  [{i}/{total}] manager {mgr_id}: {len(data)} produk",
    )


# PHASE 5: Snapshot per Fund

async def run_phase_5(page, subset_size: int | None = None, force: bool = False) -> None:
    print("\n=== PHASE 5: Snapshot per Fund ===")
    fund_ids = apply_subset(load_fund_ids(), subset_size, "fund")

    def success_msg(i, total, fund_id, data, fetched, skipped):
        if fetched % PROGRESS_LOG_EVERY == 0 or fetched <= 5:
            return f"  [{i}/{total}] fund {fund_id} OK ({fetched} baru, {skipped} skip)"
        return None

    await _scrape_loop(
        page, fund_ids, RAW_DIR / "snapshot", endpoints.get_snapshot,
        item_label="fund", sleep_s=SLEEP_SNAPSHOT, force=force, success_msg=success_msg,
    )


# PHASE 6: Portfolio Historis

async def run_phase_6(page, subset_size: int | None = None, force: bool = False) -> None:
    print("\n=== PHASE 6: Portfolio Historis (1 call = 12 snapshot, KD-6) ===")
    fund_ids = apply_subset(load_fund_ids(), subset_size, "fund")

    def success_msg(i, total, fund_id, data, fetched, skipped):
        if fetched % PROGRESS_LOG_EVERY == 0 or fetched <= 5:
            return f"  [{i}/{total}] fund {fund_id}: {len(data)} snapshot"
        return None

    await _scrape_loop(
        page, fund_ids, RAW_DIR / "portfolio", endpoints.get_historical_portfolios,
        item_label="fund", sleep_s=SLEEP_PORTFOLIO, force=force,
        success_msg=success_msg, track_empty=True,
    )


# PHASE 7: Return Kuartalan (async pool)

async def run_phase_7(page, subset_size: int | None = None, force: bool = False) -> None:
    """Sequential, satu page - lebih reliable dari async pool.

    Desain awal memakai async pool (5 worker × page baru). Masalahnya:
    page baru hasil browser.new_page() adalah halaman blank (about:blank)
    yang tidak bisa fetch ke pasardana.id tanpa navigasi dulu ke domain
    tersebut (kebijakan keamanan browser). Navigasi ulang per-worker
    menambah overhead dan kompleksitas tanpa manfaat nyata karena
    Playwright CDP tetap serializes page.evaluate() calls.
    Sequential dengan satu page lebih simpel dan lebih mudah di-debug.
    """
    print(f"\n=== PHASE 7: Return Kuartalan (sequential, {QUARTERLY_YEARS}) ===")
    out_dir = RAW_DIR / "quarterly"
    fund_ids = apply_subset(load_fund_ids(), subset_size, "fund")
    total_tasks = len(fund_ids) * len(QUARTERLY_YEARS)
    print(f"  Total tugas: {total_tasks} "
          f"({len(fund_ids)} fund × {len(QUARTERLY_YEARS)} tahun)")

    fetched = skipped = errors = 0
    task_num = 0
    for fund_id in fund_ids:
        for year in QUARTERLY_YEARS:
            task_num += 1
            path = out_dir / f"{fund_id}_{year}.json"
            if already_scraped(path) and not force:
                skipped += 1
                continue
            try:
                data = await endpoints.get_quarterly_return(page, fund_id, year)
            except Exception as e:
                errors += 1
                print(f"  [{task_num}/{total_tasks}] fund {fund_id} "
                      f"year {year} GAGAL: {e} - skip.")
                save_json(path, {"_error": str(e)})
                await asyncio.sleep(SLEEP_QUARTERLY)
                continue
            save_json(path, data)
            fetched += 1
            if fetched % PROGRESS_LOG_EVERY_QUARTERLY == 0 or fetched <= 3:
                print(f"  [{task_num}/{total_tasks}] fund {fund_id} "
                      f"year {year}: {len(data)} kuartal")
            await asyncio.sleep(SLEEP_QUARTERLY)

    print(f"  Selesai: {fetched} diambil, {skipped} skip, {errors} error.")


# PHASE 8: Junction Fund↔APERD (seed funds)

async def run_phase_8(page,
                      seed_fund_ids: list[int] | None = None,
                      force: bool = False) -> None:
    print("\n=== PHASE 8: Junction Fund↔APERD (seed funds) ===")

    if seed_fund_ids is None:
        # Default: 20 fund pertama - cukup untuk dapat seluruh ~50 APERD
        # (satu call fund 1887 saja sudah dapat 2.074 baris junction via
        # FundSalesCompanyFunds[]; 20 fund lebih dari cukup untuk coverage)
        all_ids = load_fund_ids()
        seed_fund_ids = all_ids[:20]

    print(f"  Seed funds: {len(seed_fund_ids)} fund")
    await _scrape_loop(
        page, seed_fund_ids, RAW_DIR / "sales_companies", endpoints.get_sales_companies_for_fund,
        item_label="fund", sleep_s=SLEEP_DEFAULT, force=force,
        success_msg=lambda i, total, fund_id, data, fetched, skipped:
            f"  [{i}/{total}] fund {fund_id}: {len(data)} APERD",
    )


# MAIN

async def main(phases: list[int] | None = None, force: bool = False) -> None:
    """phases=None → jalankan semua 8 (perilaku default, tidak berubah).
    phases=[5] dst. → cuma phase itu, dipakai Airflow DAG (Tahap 6) untuk
    refresh incremental per scope."""
    if phases is None:
        phases = list(range(1, 9))

    print("Membuka sesi browser (mendapat cookie valid)...")
    pw, browser, page = await create_session()

    try:
        if 1 in phases:
            await run_phase_1(page, force=force)
        if 2 in phases:
            await run_phase_2(page, force=force)
        if 3 in phases:
            await run_phase_3(page, force=force)
        if 4 in phases:
            await run_phase_4(page, PHASE_4_SUBSET_SIZE, force=force)
        if 5 in phases:
            await run_phase_5(page, PHASE_5_SUBSET_SIZE, force=force)
        if 6 in phases:
            await run_phase_6(page, PHASE_6_SUBSET_SIZE, force=force)
        if 7 in phases:
            await run_phase_7(page, PHASE_7_SUBSET_SIZE, force=force)
        if 8 in phases:
            await run_phase_8(page, PHASE_8_SEED_FUND_IDS, force=force)

        print("\n" + "=" * 60)
        print(f"EXTRACT SELESAI - phase {phases} selesai")
        print(f"Raw output: {RAW_DIR}")
        print("=" * 60)

    finally:
        await close_session(pw, browser)


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phases", type=str, default=None,
                     help="Comma-separated nomor phase, mis. '5' atau '3,4,6,7'. "
                          "Default: semua 8 phase.")
    ap.add_argument("--force", action="store_true",
                     help="Re-fetch walau file raw sudah ada (lewati resume-check). "
                          "Dipakai untuk refresh incremental (Airflow, Tahap 6), "
                          "BUKAN untuk initial load.")
    return ap.parse_args()


if __name__ == "__main__":
    args = parse_args()
    phases = [int(x) for x in args.phases.split(",")] if args.phases else None
    asyncio.run(main(phases=phases, force=args.force))