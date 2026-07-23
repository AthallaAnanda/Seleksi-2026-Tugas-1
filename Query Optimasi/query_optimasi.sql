- ============================================================
-- OPTIMASI 1: NAV terbaru per fund
-- ============================================================
-- Query ini butuh cari 1 baris NAV terbaru untuk tiap fund dari
-- nav_record (~340 ribu baris). Tanpa index, Postgres harus Seq Scan
-- lalu sort seluruh tabel per fund_id, record_date.


-- [SEBELUM]
EXPLAIN ANALYZE
SELECT DISTINCT ON (fund_id) fund_id, record_date, nav_value
FROM nav_record
ORDER BY fund_id, record_date DESC;

--[CREATE INDEX]
-- Index composite (fund_id, record_date DESC) memungkinkan Postgres
-- langsung Index Scan per fund tanpa sort tambahan (DISTINCT ON
-- bisa dipenuhi lewat "Index Scan + Unique" dibanding Seq Scan + Sort).
CREATE INDEX IF NOT EXISTS idx_nav_fund_date
    ON nav_record (fund_id, record_date DESC);

-- [SESUDAH]
EXPLAIN ANALYZE
SELECT DISTINCT ON (fund_id) fund_id, record_date, nav_value
FROM nav_record
ORDER BY fund_id, record_date DESC;

-- ============================================================
-- OPTIMASI 2: Fund mana saja yang memegang satu instrumen tertentu
-- ============================================================
-- Query ini filter portfolio_holding (~88 ribu baris) lewat security_id,
-- tapi security_id cuma dikenal setelah join ke security lewat kode saham.
-- Tanpa index di portfolio_holding.security_id, Postgres Seq Scan seluruh
-- tabel holding untuk tiap pencarian instrumen.

-- [SEBELUM]
EXPLAIN ANALYZE
SELECT f.name, ps.date_based, ph.value_pct
FROM portfolio_holding ph
JOIN security s            ON ph.security_id = s.security_id
JOIN portfolio_snapshot ps ON ph.snapshot_id = ps.snapshot_id
JOIN mutual_fund f         ON ps.fund_id     = f.fund_id
WHERE s.code = 'BBCA';

-- [CREATE INDEX]
-- Security_id di portfolio_holding dipakai untuk join ke security, 
-- sehingga index di kolom itu mempercepat pencarian holding per security.
CREATE INDEX IF NOT EXISTS idx_phold_security
    ON portfolio_holding (security_id);

-- [SESUDAH]
EXPLAIN ANALYZE
SELECT f.name, ps.date_based, ph.value_pct
FROM portfolio_holding ph
JOIN security s            ON ph.security_id = s.security_id
JOIN portfolio_snapshot ps ON ph.snapshot_id = ps.snapshot_id
JOIN mutual_fund f         ON ps.fund_id     = f.fund_id
WHERE s.code = 'BBCA';


-- ============================================================
-- OPTIMASI 3: Dashboard NAV + return terbaru per fund
-- ============================================================
-- daily_return dihitung lewat window function LAG() di view v_nav_return
-- (lihat ddl_oltp.sql). Dipanggil berulang untuk kebutuhan dashboard,
-- window function itu dihitung ulang setiap query, bukan hanya sekali.

-- [SEBELUM] 
EXPLAIN ANALYZE
SELECT DISTINCT ON (v.fund_id)
       v.fund_id, v.record_date, v.nav_value, v.daily_return
FROM v_nav_return v
ORDER BY v.fund_id, v.record_date DESC;

-- [CREATE MATERIALIZED VIEW]
-- Materialized view menyimpan hasil window function itu sekali,
-- query dashboard tinggal SELECT/lookup dari materialized view.
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_fund_latest_nav AS
SELECT DISTINCT ON (v.fund_id)
       v.fund_id, v.record_date, v.nav_value, v.daily_return
FROM v_nav_return v
ORDER BY v.fund_id, v.record_date DESC;

CREATE UNIQUE INDEX IF NOT EXISTS ux_mv_fund_latest_nav ON mv_fund_latest_nav (fund_id);

-- Refresh dipanggil ulang tiap kali nav_record bertambah (idealnya
-- ketika setelah DAG harian Airflow selesai).
REFRESH MATERIALIZED VIEW CONCURRENTLY mv_fund_latest_nav;

-- [SESUDAH]
EXPLAIN ANALYZE
SELECT fund_id, record_date, nav_value, daily_return
FROM mv_fund_latest_nav
ORDER BY fund_id;