-- load_dw.sql: ETL dari skema OLTP (public) ke skema DW (dw)
--
-- Aman dijalankan berkali-kali (idempotent):
--   · dim_date / dim_category: ON CONFLICT DO NOTHING (SCD Type 1)
--   · dim_fund / dim_manager / dim_custodian: SCD Type 2, menutup versi lama
--     hanya jika atribut yang dilacak benar-benar berbeda, lalu membuka versi
--     baru untuk fund/manager/bank yang belum memiliki baris is_current.
--   · fact table: ON CONFLICT (grain) DO NOTHING, karena grain natural
--     (fund_id/manager_id dan tanggal) tidak pernah berubah walau dimensinya SCD2.

BEGIN;

-- ========== dim_date (SCD1, kalender statis) ==========
-- Cakupan tanggal: seluruh rentang yang benar-benar dipakai nav_record,
-- aum_record, manager_aum_record (dilebarkan otomatis tiap refresh).
INSERT INTO dw.dim_date (date_id, full_date, day, day_name, week, month, month_name, quarter, year, is_weekday)
SELECT TO_CHAR(d, 'YYYYMMDD')::INT, d,
       EXTRACT(DAY FROM d), TRIM(TO_CHAR(d, 'Day')),
       EXTRACT(WEEK FROM d), EXTRACT(MONTH FROM d), TRIM(TO_CHAR(d, 'Month')),
       EXTRACT(QUARTER FROM d), EXTRACT(YEAR FROM d),
       EXTRACT(DOW FROM d) BETWEEN 1 AND 5
FROM generate_series(
    (SELECT LEAST(MIN(record_date), (SELECT MIN(record_date) FROM aum_record))
     FROM nav_record),
    (SELECT GREATEST(MAX(record_date), (SELECT MAX(record_date) FROM aum_record))
     FROM nav_record),
    '1 day'
) d
ON CONFLICT (date_id) DO NOTHING;

-- ========== dim_category (SCD1, atribut nyaris tidak pernah berubah) ==========
INSERT INTO dw.dim_category (label, fund_type_code)
SELECT DISTINCT conservative_label, fund_type FROM public.mutual_fund
ON CONFLICT (label, fund_type_code) DO NOTHING;

-- ========== dim_fund (SCD2) ==========
-- 1. Tutup versi current yang atributnya sudah beda dari OLTP
UPDATE dw.dim_fund d SET valid_to = CURRENT_DATE, is_current = FALSE
FROM public.mutual_fund f
WHERE d.fund_id = f.fund_id AND d.is_current
  AND (d.name, d.class_name, d.isin_code, d.currency_code, d.is_sharia,
       d.is_etf, d.is_index, d.official_benchmark)
      IS DISTINCT FROM
      (f.name, f.class_name, f.isin_code,
       CASE f.currency WHEN 0 THEN 'IDR' ELSE 'USD' END,
       f.is_sharia, f.is_etf, f.is_index, f.official_benchmark);

-- 2. Buka versi baru untuk fund yang barusan ditutup, atau yang belum pernah ada
INSERT INTO dw.dim_fund (fund_id, name, class_name, isin_code, currency_code,
                         is_sharia, is_etf, is_index, official_benchmark, ipo_date,
                         valid_from, valid_to, is_current)
SELECT f.fund_id, f.name, f.class_name, f.isin_code,
       CASE f.currency WHEN 0 THEN 'IDR' ELSE 'USD' END,
       f.is_sharia, f.is_etf, f.is_index, f.official_benchmark, f.ipo_date,
       CURRENT_DATE, NULL, TRUE
FROM public.mutual_fund f
WHERE NOT EXISTS (SELECT 1 FROM dw.dim_fund d WHERE d.fund_id = f.fund_id AND d.is_current);

-- ========== dim_manager (SCD2) ==========
UPDATE dw.dim_manager d SET valid_to = CURRENT_DATE, is_current = FALSE
FROM public.investment_manager m
WHERE d.manager_id = m.manager_id AND d.is_current
  AND (d.name, d.ojk_code, d.is_active) IS DISTINCT FROM (m.name, m.ojk_code, m.is_active);

INSERT INTO dw.dim_manager (manager_id, name, ojk_code, is_active, valid_from, valid_to, is_current)
SELECT m.manager_id, m.name, m.ojk_code, m.is_active, CURRENT_DATE, NULL, TRUE
FROM public.investment_manager m
WHERE NOT EXISTS (SELECT 1 FROM dw.dim_manager d WHERE d.manager_id = m.manager_id AND d.is_current);

-- ========== dim_custodian (SCD2) ==========
UPDATE dw.dim_custodian d SET valid_to = CURRENT_DATE, is_current = FALSE
FROM public.custodian_bank b
WHERE d.bank_id = b.bank_id AND d.is_current
  AND (d.name, d.ownership_status) IS DISTINCT FROM (b.name, b.ownership_status);

INSERT INTO dw.dim_custodian (bank_id, name, ownership_status, valid_from, valid_to, is_current)
SELECT b.bank_id, b.name, b.ownership_status, CURRENT_DATE, NULL, TRUE
FROM public.custodian_bank b
WHERE NOT EXISTS (SELECT 1 FROM dw.dim_custodian d WHERE d.bank_id = b.bank_id AND d.is_current);

-- ========== fact_nav_daily (grain: fund × hari) ==========
-- daily_return dari VIEW v_nav_return (atribut turunan, KD-1), dimaterialisasi
-- sebagai measure di DW; denormalisasi ini sah karena DW bersifat read-only (§13.1).
INSERT INTO dw.fact_nav_daily (date_id, fund_id, dim_fund_key, dim_manager_key,
                               category_id, dim_custodian_key, nav_value, daily_return)
SELECT TO_CHAR(n.record_date, 'YYYYMMDD')::INT, n.fund_id,
       df.dim_fund_key, dm.dim_manager_key, dc.category_id, dcust.dim_custodian_key,
       n.nav_value, n.daily_return
FROM public.v_nav_return n
JOIN public.mutual_fund f     ON n.fund_id = f.fund_id
JOIN dw.dim_fund df           ON df.fund_id = f.fund_id AND df.is_current
JOIN dw.dim_manager dm        ON dm.manager_id = f.manager_id AND dm.is_current
JOIN dw.dim_custodian dcust   ON dcust.bank_id = f.bank_id AND dcust.is_current
JOIN dw.dim_category dc       ON dc.label = f.conservative_label AND dc.fund_type_code = f.fund_type
ON CONFLICT (date_id, fund_id) DO NOTHING;

-- ========== fact_aum_monthly (grain: fund × bulan) ==========
INSERT INTO dw.fact_aum_monthly (date_id, fund_id, dim_fund_key, dim_manager_key,
                                 category_id, dim_custodian_key, aum_value, total_units)
SELECT TO_CHAR(a.record_date, 'YYYYMMDD')::INT, a.fund_id,
       df.dim_fund_key, dm.dim_manager_key, dc.category_id, dcust.dim_custodian_key,
       a.aum_value, a.total_units
FROM public.aum_record a
JOIN public.mutual_fund f     ON a.fund_id = f.fund_id
JOIN dw.dim_fund df           ON df.fund_id = f.fund_id AND df.is_current
JOIN dw.dim_manager dm        ON dm.manager_id = f.manager_id AND dm.is_current
JOIN dw.dim_custodian dcust   ON dcust.bank_id = f.bank_id AND dcust.is_current
JOIN dw.dim_category dc       ON dc.label = f.conservative_label AND dc.fund_type_code = f.fund_type
ON CONFLICT (date_id, fund_id) DO NOTHING;

-- ========== fact_manager_aum_monthly (grain: MI × bulan) ==========
INSERT INTO dw.fact_manager_aum_monthly (date_id, manager_id, dim_manager_key, aum_value, total_units)
SELECT TO_CHAR(m.record_date, 'YYYYMMDD')::INT, m.manager_id,
       dm.dim_manager_key, m.aum_value, m.total_units
FROM public.manager_aum_record m
JOIN dw.dim_manager dm ON dm.manager_id = m.manager_id AND dm.is_current
ON CONFLICT (date_id, manager_id) DO NOTHING;

COMMIT;
