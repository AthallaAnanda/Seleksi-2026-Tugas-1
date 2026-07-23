"""
endpoints.py: Fungsi scraping per endpoint pasardana.id
"""
import asyncio
from session import fetch_json, fetch_json_with_retry


# Phase 1: Master (3 call)

async def get_investment_managers(page):
    """Endpoint 1: semua MI aktif + Personnel[] + Share[]."""
    return await fetch_json(page, "/api/FundInvestmentManager/GetAll?Active=YES")


async def get_custodian_banks(page):
    """Endpoint 3: semua Bank Kustodian (~23 bank)."""
    return await fetch_json(page, "/api/FundCustodianBank/GetAll")


async def get_sales_companies(page):
    """Endpoint 4: semua APERD (~50 perusahaan)."""
    return await fetch_json(page, "/api/FundSalesCompany/GetAll")


# Phase 2: Fund List (paginated, ~16 call)

async def get_fund_list(page, page_length: int = 100):
    """Endpoint 5: daftar semua fund + metadata dasar, paginated."""
    all_funds = []
    page_begin = 1
    while True:
        path = (
            f"/api/FundSearchResult/GetAll"
            f"?pageBegin={page_begin}&pageLength={page_length}"
            "&sortField=Name&sortOrder=ASC"
        )
        batch = await fetch_json_with_retry(page, path)
        if not batch:
            break
        all_funds.extend(batch)
        print(f"    halaman {page_begin}: +{len(batch)} fund "
              f"(total: {len(all_funds)})")
        if len(batch) < page_length:
            break
        page_begin += 1
    return all_funds


# Phase 3: AUM level MI (~100 call)

async def get_manager_aum(page, manager_id: int):
    """Endpoint 2: AUM & TotalUnit agregat seluruh produk MI, bulanan."""
    return await fetch_json_with_retry(
        page, f"/api/FundInvestmentManager/GetData?id={manager_id}"
    )


# Phase 4: Fund Class per MI (~100 call)

async def get_products_data(page, manager_id: int):
    """Endpoint 6: fund per MI + FkClassFundId (sumber otoritatif KD-3)."""
    return await fetch_json_with_retry(
        page,
        f"/api/FundInvestmentManager/GetProductsData?imId={manager_id}&byDate=null"
    )


# Phase 5: Snapshot per fund (~1.540 call)

async def get_snapshot(page, fund_id: int):
    """Endpoint 7: NAV[240] + AUM[11] + Performances + Rankings + Benchmarks + Detail."""
    return await fetch_json_with_retry(
        page,
        f"/api/FundService/GetSnapshot"
        f"?fundId={fund_id}&snapshotTimestamp=undefined&username=anonymous"
    )


# Phase 6: Portfolio historis (~1.540 call)

async def get_historical_portfolios(page, fund_id: int,
                                    start: str = "2025-06-01",
                                    end: str   = "2026-07-31"):
    """Endpoint 8: SELURUH 12 snapshot portofolio dalam 1 call (KD-6).
    Hemat 92% call vs GetFundPortfolioAssetsByMonth (per bulan).
    """
    return await fetch_json_with_retry(
        page,
        f"/api/FundService/GetHistoricalFundPortfolios"
        f"?fkFundId={fund_id}&startDate={start}&endDate={end}"
    )


# Phase 7: Return kuartalan (async pool, ~7.700 call)

async def get_quarterly_return(page, fund_id: int, year: int):
    """Endpoint 9: return per kuartal satu tahun. GetSnapshot.QuarterlyReturns
    selalu kosong - endpoint ini satu-satunya sumber.
    """
    return await fetch_json_with_retry(
        page,
        f"/api/FundService/GetQuarterlyReturn?fundId={fund_id}&year={year}"
    )


# Phase 8: Junction fund↔APERD (seed funds, ~15-20 call)

async def get_sales_companies_for_fund(page, fund_id: int):
    """Endpoint 10: APERD yang menjual fund ini + nested FundSalesCompanyFunds[]
    (seluruh relasi fund↔company untuk tiap APERD dalam 1 call).
    """
    return await fetch_json_with_retry(
        page,
        f"/api/FundService/GetSalesCompanies?fundId={fund_id}"
    )