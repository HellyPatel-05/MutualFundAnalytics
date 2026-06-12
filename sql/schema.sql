-- ============================================================
-- bluestock_mf.db  |  Star Schema DDL
-- Day 2: Mutual Fund Analytics SQLite Database
-- ============================================================

PRAGMA foreign_keys = ON;

-- ────────────────────────────────────────────
-- DIMENSION: Fund Master
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_fund (
    amfi_code          INTEGER PRIMARY KEY,
    fund_house         TEXT    NOT NULL,
    scheme_name        TEXT    NOT NULL,
    category           TEXT,                    -- Equity / Debt / Hybrid
    sub_category       TEXT,                    -- Large Cap / Mid Cap / etc.
    plan               TEXT,                    -- Regular / Direct
    launch_date        TEXT,                    -- ISO date string
    benchmark          TEXT,
    expense_ratio      REAL,                    -- Annual expense ratio %
    exit_load_pct      REAL,
    min_sip_amount     REAL,
    fund_manager       TEXT,
    risk_category      TEXT,                    -- Low / Moderate / High / Very High
    sebi_category_code TEXT
);

-- ────────────────────────────────────────────
-- DIMENSION: Date
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS dim_date (
    date_key     TEXT    PRIMARY KEY,           -- YYYY-MM-DD
    year         INTEGER NOT NULL,
    quarter      INTEGER NOT NULL,              -- 1–4
    month        INTEGER NOT NULL,              -- 1–12
    month_name   TEXT    NOT NULL,
    day          INTEGER NOT NULL,
    day_of_week  INTEGER NOT NULL,              -- 0=Monday … 6=Sunday
    week_of_year INTEGER,
    is_weekend   INTEGER NOT NULL DEFAULT 0,    -- 1 if Sat/Sun
    is_month_end INTEGER NOT NULL DEFAULT 0     -- 1 if last day of month
);

-- ────────────────────────────────────────────
-- FACT: NAV History
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_nav (
    nav_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code      INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    date_key       TEXT    NOT NULL REFERENCES dim_date(date_key),
    nav            REAL    NOT NULL CHECK(nav > 0),
    is_trading_day INTEGER NOT NULL DEFAULT 1   -- 0 = ffill'd holiday/weekend
);

CREATE INDEX IF NOT EXISTS idx_fact_nav_fund_date
    ON fact_nav(amfi_code, date_key);

-- ────────────────────────────────────────────
-- FACT: Investor Transactions
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_transactions (
    txn_id              INTEGER PRIMARY KEY AUTOINCREMENT,
    investor_id         TEXT    NOT NULL,
    date_key            TEXT    NOT NULL REFERENCES dim_date(date_key),
    amfi_code           INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    transaction_type    TEXT    NOT NULL CHECK(transaction_type IN ('SIP','Lumpsum','Redemption')),
    amount_inr          REAL    NOT NULL CHECK(amount_inr > 0),
    state               TEXT,
    city                TEXT,
    city_tier           TEXT,                   -- T30 / B30
    age_group           TEXT,                   -- 18-25 / 26-35 / 36-45 / 46-55 / 56+
    gender              TEXT,
    annual_income_lakh  REAL,
    payment_mode        TEXT,                   -- UPI / Mandate / Cheque / Net Banking
    kyc_status          TEXT                    -- Verified / Pending / Rejected
);

CREATE INDEX IF NOT EXISTS idx_txn_fund_date
    ON fact_transactions(amfi_code, date_key);
CREATE INDEX IF NOT EXISTS idx_txn_state
    ON fact_transactions(state);

-- ────────────────────────────────────────────
-- FACT: Scheme Performance (point-in-time snapshot)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_performance (
    perf_id            INTEGER PRIMARY KEY AUTOINCREMENT,
    amfi_code          INTEGER NOT NULL REFERENCES dim_fund(amfi_code),
    return_1yr_pct     REAL,
    return_3yr_pct     REAL,
    return_5yr_pct     REAL,
    benchmark_3yr_pct  REAL,
    alpha              REAL,
    beta               REAL,
    sharpe_ratio       REAL,
    sortino_ratio      REAL,
    std_dev_ann_pct    REAL,
    max_drawdown_pct   REAL,
    aum_crore          REAL,
    expense_ratio_pct  REAL,
    morningstar_rating INTEGER,
    risk_grade         TEXT,
    anomaly_flag       INTEGER NOT NULL DEFAULT 0
);

-- ────────────────────────────────────────────
-- FACT: AUM by Fund House (quarterly)
-- ────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS fact_aum (
    aum_id         INTEGER PRIMARY KEY AUTOINCREMENT,
    date_key       TEXT    NOT NULL REFERENCES dim_date(date_key),
    fund_house     TEXT    NOT NULL,
    aum_lakh_crore REAL,
    aum_crore      REAL,
    num_schemes    INTEGER
);
