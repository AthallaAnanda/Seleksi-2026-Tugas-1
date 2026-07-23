"""
session.py: Playwright session helper untuk scraping pasardana.id

Pasardana.id adalah SPA (AngularJS) yang memuat data via endpoint REST internal.
Endpoint ini TIDAK butuh API key, tapi butuh cookie sesi valid (mis.
__RequestVerificationToken) yang hanya bisa didapat dengan mengunjungi
halaman web asli lewat browser - karena itu kita pakai Playwright, bukan
httpx/requests biasa.
"""
import asyncio
from playwright.async_api import async_playwright

BASE_URL = "https://pasardana.id"


async def create_session():
    """Buka browser & kunjungi halaman pasardana.id untuk mendapat cookie sesi valid.

    Return (playwright, browser, page) - caller WAJIB panggil close_session()
    setelah selesai, idealnya dalam blok try/finally.
    """
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    page = await browser.new_page()
    await page.goto(f"{BASE_URL}/fund/search", wait_until="networkidle")
    return pw, browser, page


async def close_session(pw, browser):
    """Tutup browser & stop Playwright dengan rapi."""
    await browser.close()
    await pw.stop()


async def fetch_json(page, path: str):
    """Fetch endpoint internal dari DALAM konteks browser (cookie otomatis
    terbawa oleh `fetch()` bawaan browser, tidak perlu kita atur manual).

    `path` boleh path relatif ("/api/...") atau URL penuh.
    """
    url = path if path.startswith("http") else f"{BASE_URL}{path}"
    result = await page.evaluate(
        """
        async (url) => {
            const r = await fetch(url, { headers: { 'Accept': 'application/json' } });
            if (!r.ok) {
                throw new Error(`HTTP ${r.status} untuk ${url}`);
            }
            return await r.json();
        }
        """,
        url,
    )
    return result


async def fetch_json_with_retry(page, path: str, tries: int = 3, base_delay: float = 5.0):
    """Fetch dengan retry + exponential backoff.

    Retry HANYA untuk error transien (jaringan, timeout).
    HTTP 5xx = server error, tidak di-retry (tidak akan sembuh dengan tunggu).
    HTTP 4xx = client error, tidak di-retry (permintaan memang salah).

    Caller bertanggung jawab menangani exception yang di-raise setelah
    semua retry habis - gunakan try/except di level loop (run_phase_*).
    """
    last_err = None
    for attempt in range(tries):
        try:
            return await fetch_json(page, path)
        except Exception as e:
            err_str = str(e)
            # Deteksi HTTP status dari pesan error Playwright
            # Format: "Error: HTTP <status> untuk <url>"
            for prefix in ("HTTP 4", "HTTP 5"):
                if prefix in err_str:
                    # Client/server error - tidak ada gunanya retry
                    raise
            # Error lain (TimeoutError, jaringan, dll) - retry dengan backoff
            last_err = e
            if attempt < tries - 1:
                delay = base_delay * (attempt + 1)
                print(f"  [retry {attempt + 1}/{tries - 1}] {path} "
                      f"gagal: {e} - tunggu {delay:.0f}s")
                await asyncio.sleep(delay)
    raise last_err