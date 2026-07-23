-- ddl_dw.sql: Skema Data Warehouse (OLAP), skema `dw`
--
-- Fact constellation: 3 fact table dengan grain berbeda, tidak digabung (KD-2).
-- dim_fund/dim_manager/dim_custodian menggunakan SCD Type 2 (KD-11) karena
-- atributnya benar-benar berubah (fee, alamat, status izin); fact table
-- perlu mengetahui versi dimensi yang berlaku saat fact tersebut terjadi.
-- dim_date dan dim_category tetap menggunakan SCD Type 1 karena atributnya
-- nyaris tidak pernah berubah, sehingga kompleksitas SCD2 tidak diperlukan.

CREATE SCHEMA IF NOT EXISTS dw;

CREATE TABLE dw.dim_date (
    date_id     INT PRIMARY KEY,           -- YYYYMMDD
    full_date   DATE NOT NULL UNIQUE,
    day         SMALLINT,
    day_name    VARCHAR(10),
    week        SMALLINT,
    month       SMALLINT,
    month_name  VARCHAR(10),
    quarter     SMALLINT,
    year        SMALLINT,
    is_weekday  BOOLEAN NOT NULL
);

-- SCD Type 2: dim_fund_key surrogate jadi PK, fund_id natural key (boleh berulang antar versi)
CREATE TABLE dw.dim_fund (          -- hanya atribut intrinsik fund (KD-4)
    dim_fund_key        SERIAL PRIMARY KEY,
    fund_id             INT NOT NULL,
    name                VARCHAR(255) NOT NULL,
    class_name          VARCHAR(50),
    isin_code           VARCHAR(20),
    currency_code       VARCHAR(3) NOT NULL,
    is_sharia           BOOLEAN,
    is_etf              BOOLEAN,
    is_index            BOOLEAN,
    official_benchmark  VARCHAR(255),
    ipo_date            DATE,
    valid_from          DATE NOT NULL,
    valid_to            DATE,                       -- NULL = masih berlaku
    is_current          BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX ux_dim_fund_current ON dw.dim_fund (fund_id) WHERE is_current;

CREATE TABLE dw.dim_manager (
    dim_manager_key SERIAL PRIMARY KEY,
    manager_id      INT NOT NULL,
    name            VARCHAR(255) NOT NULL,
    ojk_code        VARCHAR(20),
    is_active       BOOLEAN,
    valid_from      DATE NOT NULL,
    valid_to        DATE,
    is_current      BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX ux_dim_manager_current ON dw.dim_manager (manager_id) WHERE is_current;

CREATE TABLE dw.dim_category (      -- SCD Type 1 karena atributnya nyaris tidak pernah berubah
    category_id     SERIAL PRIMARY KEY,
    label           VARCHAR(50) NOT NULL,
    fund_type_code  SMALLINT NOT NULL,
    UNIQUE (label, fund_type_code)
);

CREATE TABLE dw.dim_custodian (
    dim_custodian_key SERIAL PRIMARY KEY,
    bank_id           INT NOT NULL,
    name              VARCHAR(255) NOT NULL,
    ownership_status  VARCHAR(30),
    valid_from        DATE NOT NULL,
    valid_to          DATE,
    is_current        BOOLEAN NOT NULL DEFAULT TRUE
);
CREATE UNIQUE INDEX ux_dim_custodian_current ON dw.dim_custodian (bank_id) WHERE is_current;

-- Grain fact table tidak berubah (tetap fund_id/manager_id natural, KD-2).
-- Kolom dim_*_key ditambahkan di samping grain untuk menunjuk versi dimensi
-- yang berlaku saat fact di-insert, bukan sebagai pengganti grain.
CREATE TABLE dw.fact_nav_daily (
    date_id           INT NOT NULL REFERENCES dw.dim_date(date_id),
    fund_id           INT NOT NULL,
    dim_fund_key      INT NOT NULL REFERENCES dw.dim_fund(dim_fund_key),
    dim_manager_key   INT NOT NULL REFERENCES dw.dim_manager(dim_manager_key),
    category_id       INT NOT NULL REFERENCES dw.dim_category(category_id),
    dim_custodian_key INT NOT NULL REFERENCES dw.dim_custodian(dim_custodian_key),
    nav_value         NUMERIC(18,4) NOT NULL,
    daily_return      NUMERIC(12,8),
    PRIMARY KEY (date_id, fund_id)
);

CREATE TABLE dw.fact_aum_monthly (
    date_id           INT NOT NULL REFERENCES dw.dim_date(date_id),  -- awal bulan
    fund_id           INT NOT NULL,
    dim_fund_key      INT NOT NULL REFERENCES dw.dim_fund(dim_fund_key),
    dim_manager_key   INT NOT NULL REFERENCES dw.dim_manager(dim_manager_key),
    category_id       INT NOT NULL REFERENCES dw.dim_category(category_id),
    dim_custodian_key INT NOT NULL REFERENCES dw.dim_custodian(dim_custodian_key),
    aum_value         BIGINT NOT NULL,
    total_units       NUMERIC(18,4),
    PRIMARY KEY (date_id, fund_id)
);

CREATE TABLE dw.fact_manager_aum_monthly (   -- grain: MI × bulan
    date_id          INT NOT NULL REFERENCES dw.dim_date(date_id),
    manager_id       INT NOT NULL,
    dim_manager_key  INT NOT NULL REFERENCES dw.dim_manager(dim_manager_key),
    aum_value        NUMERIC(20,2) NOT NULL,
    total_units      NUMERIC(20,4),
    PRIMARY KEY (date_id, manager_id)
);

CREATE INDEX idx_fnav_date ON dw.fact_nav_daily (date_id);
CREATE INDEX idx_fnav_fund ON dw.fact_nav_daily (fund_id);
CREATE INDEX idx_faum_date ON dw.fact_aum_monthly (date_id);
CREATE INDEX idx_faum_fund ON dw.fact_aum_monthly (fund_id);
CREATE INDEX idx_fmaum_mgr ON dw.fact_manager_aum_monthly (manager_id);
