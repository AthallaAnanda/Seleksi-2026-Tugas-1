"""
test_smoke.py: Smoke test Tahap 1

Menguji SATU endpoint termurah (FundCustodianBank/GetAll, 1 call, ~23 bank,
response kecil) sebelum membangun endpoints.py lengkap. Kalau ini gagal,
JANGAN lanjut ke endpoint lain dulu - perbaiki di sini.

Jalankan: python test_smoke.py
"""
import asyncio
import json

from session import create_session, close_session, fetch_json


async def main():
    print("=" * 60)
    print("SMOKE TEST: Tahap 1")
    print("=" * 60)

    print("\n[1/3] Membuka sesi browser (mendapat cookie valid)...")
    pw, browser, page = await create_session()
    print("      OK: sesi terbuka.")

    try:
        print("\n[2/3] Fetch: FundCustodianBank/GetAll ...")
        data = await fetch_json(page, "/api/FundCustodianBank/GetAll")

        print(f"      OK: {len(data)} bank kustodian diterima.")

        # Verifikasi struktur cocok dengan field yang diharapkan
        expected_keys = {"Id", "Name", "OjkCode", "IsActive"}
        first = data[0]
        missing = expected_keys - set(first.keys())

        print("\n[3/3] Verifikasi struktur response...")
        if missing:
            print(f"      PERINGATAN - field hilang dari yang diharapkan: {missing}")
            print("      Struktur API mungkin sudah berubah sejak dokumen dibuat.")
        else:
            print("      OK: semua field kunci ada (Id, Name, OjkCode, IsActive).")

        print("\nContoh item pertama:")
        print(json.dumps(first, indent=2, ensure_ascii=False)[:600])

        print("\n" + "=" * 60)
        print(f"SMOKE TEST LULUS: {len(data)} bank diterima dengan struktur benar.")
        print("Aman lanjut ke Phase 1-2 penuh.")
        print("=" * 60)

    except Exception as e:
        print(f"\nSMOKE TEST GAGAL: {type(e).__name__}: {e}")
        print("Jangan lanjut ke endpoint lain dulu - debug ini sampai lulus.")
        raise

    finally:
        await close_session(pw, browser)


if __name__ == "__main__":
    asyncio.run(main())