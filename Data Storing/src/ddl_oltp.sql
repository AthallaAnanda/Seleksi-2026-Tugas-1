--  DDL Utama
CREATE TABLE investment_manager (
    manager_id        INT PRIMARY KEY,
    name              VARCHAR(255) NOT NULL,
    ojk_code          VARCHAR(20) UNIQUE NOT NULL,
    mi_permit_num     VARCHAR(150),
    ppe_permit_num    VARCHAR(150),
    pee_permit_num    VARCHAR(150),
    description       TEXT,
    address           TEXT,
    telephone         VARCHAR(50),
    fax               VARCHAR(50),
    email             VARCHAR(100),
    website_url       VARCHAR(255),
    capital           BIGINT CHECK (capital >= 0),
    paid_in_capital   BIGINT CHECK (paid_in_capital >= 0),
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    data_last_update  DATE,
    scraped_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE manager_personnel (
    personnel_id  SERIAL PRIMARY KEY,
    manager_id    INT NOT NULL REFERENCES investment_manager(manager_id) ON DELETE CASCADE,
    name          VARCHAR(255) NOT NULL,
    title         VARCHAR(100) NOT NULL
);

CREATE TABLE manager_shareholder (
    shareholder_id   SERIAL PRIMARY KEY,
    manager_id       INT NOT NULL REFERENCES investment_manager(manager_id) ON DELETE CASCADE,
    shareholder_name VARCHAR(255) NOT NULL,
    share_amount     BIGINT CHECK (share_amount >= 0)
);

CREATE TABLE manager_aum_record (          -- AUM untuk level Manager Investment (bulanan)
    manager_id      INT NOT NULL REFERENCES investment_manager(manager_id) ON DELETE CASCADE,
    record_date     DATE NOT NULL,
    aum_value       NUMERIC(20,2) NOT NULL CHECK (aum_value >= 0),
    total_units     NUMERIC(20,4) CHECK (total_units >= 0),
    scraped_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (manager_id, record_date)
);

CREATE TABLE custodian_bank (
    bank_id           INT PRIMARY KEY,
    name              VARCHAR(255) NOT NULL,
    ojk_code          VARCHAR(20) UNIQUE,
    description       TEXT,
    address           TEXT,
    telephone         VARCHAR(50),
    fax               VARCHAR(50),
    email             VARCHAR(100),
    website_url       VARCHAR(255),
    niu_bank_umum     VARCHAR(100),
    niu_bk            VARCHAR(100),
    date_start_sk     VARCHAR(50),
    ownership_status  VARCHAR(30),
    activity_status   VARCHAR(30),
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    data_last_update  DATE,
    scraped_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE sales_company (
    company_id     INT PRIMARY KEY,
    name           VARCHAR(255) NOT NULL,
    aperd_id       VARCHAR(20) UNIQUE NOT NULL,
    npwp           VARCHAR(30),
    no_sttd_sk     VARCHAR(100),
    date_sttd_sk   VARCHAR(50),
    address        TEXT,
    telephone      VARCHAR(50),
    fax            VARCHAR(50),
    email          VARCHAR(100),
    website_url    VARCHAR(255),
    contact_person VARCHAR(255),
    scraped_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE fund_class (
    class_group_id  INT PRIMARY KEY,            -- FkClassFundId diambil dari API
    base_name       VARCHAR(255) NOT NULL       -- derivasi: nama tanpa sufiks kelas
);

CREATE TABLE benchmark (
    benchmark_id  INT PRIMARY KEY,
    name          VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE asset_category (          -- dari SpesificType pada baris Type 0
    category_id  SMALLINT PRIMARY KEY, 
    name         VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE security (                -- hanya ada: saham + obligasi (supertype)
    security_id      SERIAL PRIMARY KEY,
    code             VARCHAR(255) NOT NULL UNIQUE,  -- "BBCA"/"FR0068" (saham pendek) ATAU deskripsi obligasi panjang (max 183 char, §4.13 catatan)
    name             VARCHAR(255) NOT NULL,
    security_type    SMALLINT NOT NULL CHECK (security_type IN (1,2)),  -- 1=saham, 2=obligasi
    source_stock_id  INT                            -- fkStockId dari API (hanya saham)
);

CREATE TABLE mutual_fund (
    fund_id                  INT PRIMARY KEY,
    manager_id               INT NOT NULL REFERENCES investment_manager(manager_id),
    bank_id                  INT NOT NULL REFERENCES custodian_bank(bank_id),
    class_group_id           INT REFERENCES fund_class(class_group_id),
    name                     VARCHAR(255) NOT NULL,
    class_name               VARCHAR(50),
    isin_code                VARCHAR(20) UNIQUE,
    bloomberg_quote          VARCHAR(50),
    fund_type                SMALLINT NOT NULL,
    currency                 SMALLINT NOT NULL DEFAULT 0,
    is_sharia                BOOLEAN NOT NULL DEFAULT FALSE,
    is_etf                   BOOLEAN NOT NULL DEFAULT FALSE,
    is_index                 BOOLEAN NOT NULL DEFAULT FALSE,
    has_dividend             BOOLEAN NOT NULL DEFAULT FALSE,
    is_active                BOOLEAN NOT NULL DEFAULT TRUE,
    ipo_date                 DATE,
    description              TEXT,
    official_benchmark       VARCHAR(255),
    min_subscription         BIGINT CHECK (min_subscription >= 0),
    min_next_subscription    BIGINT CHECK (min_next_subscription >= 0),
    min_redemption           BIGINT CHECK (min_redemption >= 0),
    min_balance              BIGINT CHECK (min_balance >= 0),
    sub_fee_max_pct          NUMERIC(6,4) CHECK (sub_fee_max_pct BETWEEN 0 AND 100),
    red_fee_max_pct          NUMERIC(6,4) CHECK (red_fee_max_pct BETWEEN 0 AND 100),
    switching_fee_max_pct    NUMERIC(6,4) CHECK (switching_fee_max_pct BETWEEN 0 AND 100),
    manager_fee_max_pct      NUMERIC(6,4) CHECK (manager_fee_max_pct BETWEEN 0 AND 100),
    custodian_fee_max_pct    NUMERIC(6,4) CHECK (custodian_fee_max_pct BETWEEN 0 AND 100),
    policy_bond_pct          NUMERIC(5,2) CHECK (policy_bond_pct BETWEEN 0 AND 100),
    policy_equity_pct        NUMERIC(5,2) CHECK (policy_equity_pct BETWEEN 0 AND 100),
    policy_money_market_pct  NUMERIC(5,2) CHECK (policy_money_market_pct BETWEEN 0 AND 100),
    last_update              DATE,
    scraped_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- ATRIBUT TURUNAN (KD-7): DBMS yang menegakkan, mustahil data drift
    conservative_label       VARCHAR(50) GENERATED ALWAYS AS (
        CASE
            WHEN is_index                  THEN 'Indeks'
            WHEN fund_type = 7 AND is_etf  THEN 'Exchange Traded Fund'
            WHEN fund_type = 7             THEN 'Reksadana Global'
            WHEN fund_type = 0             THEN 'Campuran'
            WHEN fund_type = 1             THEN 'Saham'
            WHEN fund_type = 2             THEN 'Pendapatan Tetap'
            WHEN fund_type = 3             THEN 'Pasar Uang'
            WHEN fund_type = 4             THEN 'Terproteksi'
            ELSE 'Lainnya'
        END
    ) STORED
);

-- ========== TIME-SERIES & DETAIL ==========
CREATE TABLE nav_record (
    fund_id           INT NOT NULL REFERENCES mutual_fund(fund_id) ON DELETE CASCADE,
    record_date       DATE NOT NULL,
    nav_value         NUMERIC(18,4) NOT NULL CHECK (nav_value > 0),
    class_total_value NUMERIC(18,4),
    scraped_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),   -- bukti scheduling
    PRIMARY KEY (fund_id, record_date)
    -- daily_return TIDAK disimpan (KD-1) → lihat VIEW v_nav_return
);

CREATE TABLE aum_record (
    fund_id            INT NOT NULL REFERENCES mutual_fund(fund_id) ON DELETE CASCADE,
    record_date        DATE NOT NULL,          -- label periode (awal bulan)
    published_date     DATE,                   -- tanggal nilai diukur (akhir bulan)
    aum_value          BIGINT NOT NULL CHECK (aum_value >= 0),
    total_units        NUMERIC(18,4) CHECK (total_units >= 0),
    class_total_value  BIGINT,
    scraped_at         TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (fund_id, record_date)
);

CREATE TABLE portfolio_snapshot (
    snapshot_id              SERIAL PRIMARY KEY,
    fund_id                  INT NOT NULL REFERENCES mutual_fund(fund_id) ON DELETE CASCADE,
    date_based               DATE NOT NULL,
    domestic_allocation_pct  NUMERIC(5,2) CHECK (domestic_allocation_pct BETWEEN 0 AND 100),
    foreign_allocation_pct   NUMERIC(5,2) CHECK (foreign_allocation_pct BETWEEN 0 AND 100),
    scraped_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (fund_id, date_based)
);

CREATE TABLE portfolio_allocation (    -- Type 0: rekap kelas aset, total 100%
    allocation_id  SERIAL PRIMARY KEY,
    snapshot_id    INT NOT NULL REFERENCES portfolio_snapshot(snapshot_id) ON DELETE CASCADE,
    category_id    SMALLINT NOT NULL REFERENCES asset_category(category_id),
    value_pct      NUMERIC(8,4) NOT NULL CHECK (value_pct BETWEEN 0 AND 100),
    UNIQUE (snapshot_id, category_id)
);

CREATE TABLE portfolio_holding (       -- Type 1 & 2: instrumen individual, parsial
    holding_id     BIGSERIAL PRIMARY KEY,
    snapshot_id    INT NOT NULL REFERENCES portfolio_snapshot(snapshot_id) ON DELETE CASCADE,
    security_id    INT NOT NULL REFERENCES security(security_id),
    value_pct      NUMERIC(8,4) NOT NULL CHECK (value_pct BETWEEN 0 AND 100),
    UNIQUE (snapshot_id, security_id)
);

CREATE TABLE fund_performance (
    fund_id                INT NOT NULL REFERENCES mutual_fund(fund_id) ON DELETE CASCADE,
    period_code            SMALLINT NOT NULL,
    as_of_date             DATE NOT NULL,     -- tanggal NAV terakhir jadi dasar rolling-window (period_code cuma jenis rentang, bukan tanggal)
    return_pct             NUMERIC(12,8),
    std_dev                NUMERIC(12,8),
    beta                   NUMERIC(12,8),
    sharpe_ratio           NUMERIC(12,8),
    modified_sharpe_ratio  NUMERIC(12,8),
    treynor_ratio          NUMERIC(12,8),
    sortino_ratio          NUMERIC(12,8),
    tracking_error         NUMERIC(12,8),
    max_drawdown           NUMERIC(12,8),
    cagr                   NUMERIC(12,8),
    jensen_alpha           NUMERIC(12,8),
    PRIMARY KEY (fund_id, period_code, as_of_date)
);

CREATE TABLE fund_ranking (
    fund_id           INT NOT NULL REFERENCES mutual_fund(fund_id) ON DELETE CASCADE,
    period_code       SMALLINT NOT NULL,
    category_code     SMALLINT NOT NULL DEFAULT 0,
    as_of_date        DATE NOT NULL,     -- tanggal NAV terakhir jadi dasar rolling-window (period_code cuma jenis rentang, bukan tanggal)
    risk_rank         INT CHECK (risk_rank > 0),
    rating_rank       INT CHECK (rating_rank > 0),
    all_risk_rank     INT CHECK (all_risk_rank > 0),
    pasardana_rating  NUMERIC(3,1) CHECK (pasardana_rating BETWEEN 1 AND 5),
    risk_rating       NUMERIC(3,1) CHECK (risk_rating BETWEEN 1 AND 5),
    all_risk_rating   NUMERIC(3,1) CHECK (all_risk_rating BETWEEN 1 AND 5),
    PRIMARY KEY (fund_id, period_code, category_code, as_of_date)
);

CREATE TABLE benchmark_data_point (
    benchmark_id  INT NOT NULL REFERENCES benchmark(benchmark_id) ON DELETE CASCADE,
    record_date   DATE NOT NULL,
    value         NUMERIC(18,8) NOT NULL,
    PRIMARY KEY (benchmark_id, record_date)
    -- daily_return TIDAK disimpan → lihat VIEW v_benchmark_return
);

CREATE TABLE fund_quarterly_return (
    fund_id        INT NOT NULL REFERENCES mutual_fund(fund_id) ON DELETE CASCADE,
    quarter_start  DATE NOT NULL,
    return_pct     NUMERIC(12,8),
    PRIMARY KEY (fund_id, quarter_start)
);

-- ========== JUNCTION / ASSOCIATIVE ==========
CREATE TABLE fund_benchmark (
    fund_id       INT NOT NULL REFERENCES mutual_fund(fund_id) ON DELETE CASCADE,
    benchmark_id  INT NOT NULL REFERENCES benchmark(benchmark_id) ON DELETE CASCADE,
    is_official   BOOLEAN NOT NULL DEFAULT FALSE,
    PRIMARY KEY (fund_id, benchmark_id)
);

CREATE TABLE fund_sales_company (          -- associative entity: punya atribut commission_fee
    fund_id         INT NOT NULL REFERENCES mutual_fund(fund_id) ON DELETE CASCADE,
    company_id      INT NOT NULL REFERENCES sales_company(company_id) ON DELETE CASCADE,
    commission_fee  NUMERIC(6,4) CHECK (commission_fee BETWEEN 0 AND 100),
    PRIMARY KEY (fund_id, company_id)
);

-- ========== AUDIT TRAIL ==========
-- Tabel generik, bukan tabel _history per master table. Menangkap SIAPA
-- yang berubah, KAPAN, dan nilai SEBELUM/SESUDAH -- beda kebutuhan dari
-- SCD2 di DW: audit trail menjawab "apa yang berubah", SCD2 menjawab
-- "versi mana yang berlaku pada tanggal fact tertentu".
-- BUKAN entity bisnis -> tidak digambar di ERD, murni infrastruktur.
CREATE TABLE audit_log (
    audit_id      BIGSERIAL PRIMARY KEY,
    table_name    VARCHAR(50) NOT NULL,
    record_pk     TEXT NOT NULL,          -- mis. '55' untuk fund_id=55
    changed_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    old_values    JSONB,                  -- snapshot baris sebelum UPDATE
    new_values    JSONB,                  -- snapshot baris sesudah UPDATE
    changed_by    VARCHAR(50) DEFAULT CURRENT_USER
);
CREATE INDEX idx_audit_table_pk ON audit_log (table_name, record_pk);

CREATE OR REPLACE FUNCTION fn_audit_row() RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_log (table_name, record_pk, old_values, new_values)
    VALUES (TG_TABLE_NAME, (row_to_json(OLD)->>TG_ARGV[0]), to_jsonb(OLD), to_jsonb(NEW));
    RETURN NEW;
END; $$ LANGUAGE plpgsql;

-- Dipasang di semua tabel Pola B (upsert via ON CONFLICT DO UPDATE).
-- WHEN mengecualikan scraped_at dari perbandingan: tanpa ini, re-run loader
-- dengan data identik tetap tercatat sebagai "perubahan" tiap kali scraped_at
-- di-refresh, membanjiri audit_log dengan noise.
CREATE TRIGGER trg_audit_investment_manager AFTER UPDATE ON investment_manager
    FOR EACH ROW WHEN (to_jsonb(OLD) - 'scraped_at' IS DISTINCT FROM to_jsonb(NEW) - 'scraped_at')
    EXECUTE FUNCTION fn_audit_row('manager_id');

CREATE TRIGGER trg_audit_custodian_bank AFTER UPDATE ON custodian_bank
    FOR EACH ROW WHEN (to_jsonb(OLD) - 'scraped_at' IS DISTINCT FROM to_jsonb(NEW) - 'scraped_at')
    EXECUTE FUNCTION fn_audit_row('bank_id');

CREATE TRIGGER trg_audit_sales_company AFTER UPDATE ON sales_company
    FOR EACH ROW WHEN (to_jsonb(OLD) - 'scraped_at' IS DISTINCT FROM to_jsonb(NEW) - 'scraped_at')
    EXECUTE FUNCTION fn_audit_row('company_id');

CREATE TRIGGER trg_audit_mutual_fund AFTER UPDATE ON mutual_fund
    FOR EACH ROW WHEN (to_jsonb(OLD) - 'scraped_at' IS DISTINCT FROM to_jsonb(NEW) - 'scraped_at')
    EXECUTE FUNCTION fn_audit_row('fund_id');

CREATE TRIGGER trg_audit_security AFTER UPDATE ON security
    FOR EACH ROW WHEN (to_jsonb(OLD) IS DISTINCT FROM to_jsonb(NEW))
    EXECUTE FUNCTION fn_audit_row('security_id');

CREATE TRIGGER trg_audit_fund_class AFTER UPDATE ON fund_class
    FOR EACH ROW WHEN (to_jsonb(OLD) IS DISTINCT FROM to_jsonb(NEW))
    EXECUTE FUNCTION fn_audit_row('class_group_id');

-- View untuk Atribut Turunan
-- v_nav_return: NAV + return harian (KD-1)
CREATE VIEW v_nav_return AS
SELECT
    n.fund_id,
    n.record_date,
    n.nav_value,
    LAG(n.nav_value) OVER w                                   AS prev_nav_value,
    (n.nav_value - LAG(n.nav_value) OVER w)
        / NULLIF(LAG(n.nav_value) OVER w, 0)                  AS daily_return
FROM nav_record n
WINDOW w AS (PARTITION BY n.fund_id ORDER BY n.record_date);

-- ── v_benchmark_return: nilai benchmark + return harian
CREATE VIEW v_benchmark_return AS
SELECT
    b.benchmark_id,
    b.record_date,
    b.value,
    (b.value - LAG(b.value) OVER w)
        / NULLIF(LAG(b.value) OVER w, 0)                      AS daily_return
FROM benchmark_data_point b
WINDOW w AS (PARTITION BY b.benchmark_id ORDER BY b.record_date);

-- ── v_fund_class_total: total AUM & unit per grup kelas
CREATE VIEW v_fund_class_total AS
SELECT
    f.class_group_id,
    a.record_date,
    SUM(a.aum_value)    AS class_total_aum,
    SUM(a.total_units)  AS class_total_unit,
    COUNT(*)            AS jumlah_kelas
FROM mutual_fund f
JOIN aum_record a ON a.fund_id = f.fund_id
WHERE f.class_group_id IS NOT NULL
GROUP BY f.class_group_id, a.record_date;

-- ── v_aum_integrity: checksum total_units vs aum/nav (§4.10)
CREATE VIEW v_aum_integrity AS
SELECT
    a.fund_id,
    a.record_date,
    a.published_date,
    a.total_units,
    a.aum_value / NULLIF(n.nav_value, 0)  AS derived_units,
    ABS(a.total_units - a.aum_value / NULLIF(n.nav_value, 0)) AS selisih
FROM aum_record a
LEFT JOIN nav_record n
       ON n.fund_id = a.fund_id
      AND n.record_date = a.published_date;