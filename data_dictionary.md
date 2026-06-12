# Data Dictionary — Bluestock Mutual Fund Analytics

**Project:** Bluestock MF Analytics  
**Database:** `bluestock_mf.db` (SQLite)  
**Last Updated:** Day 2

---

## Table of Contents

1. [dim_fund](#dim_fund)
2. [dim_date](#dim_date)
3. [fact_nav](#fact_nav)
4. [fact_transactions](#fact_transactions)
5. [fact_performance](#fact_performance)
6. [fact_aum](#fact_aum)
7. [Source File Reference](#source-file-reference)

---

## dim_fund

**Description:** Dimension table holding master data for each mutual fund scheme.  
**Source:** `data/raw/01_fund_master.csv` → `data/processed/01_fund_master_cleaned.csv`  
**Grain:** One row per AMFI scheme code.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `amfi_code` | INTEGER PK | Unique AMFI registration number for the scheme | `119551` |
| `fund_house` | TEXT | Asset Management Company name | `SBI Mutual Fund` |
| `scheme_name` | TEXT | Full scheme name as registered with SEBI | `SBI Bluechip Fund - Regular Plan - Growth` |
| `category` | TEXT | Broad asset class: Equity, Debt, Hybrid | `Equity` |
| `sub_category` | TEXT | SEBI sub-category: Large Cap, Mid Cap, Small Cap, Gilt, Liquid, etc. | `Large Cap` |
| `plan` | TEXT | Plan type: Regular or Direct | `Regular` |
| `launch_date` | TEXT | Scheme inception date (ISO 8601) | `2006-02-14` |
| `benchmark` | TEXT | Official benchmark index | `NIFTY 100 TRI` |
| `expense_ratio` | REAL | Annual Total Expense Ratio in % | `1.54` |
| `exit_load_pct` | REAL | Exit load charged on redemption in % | `1.0` |
| `min_sip_amount` | REAL | Minimum SIP instalment amount in INR | `500` |
| `fund_manager` | TEXT | Lead fund manager name | `Sohini Andani` |
| `risk_category` | TEXT | Risk level: Low / Moderate / Moderately High / High / Very High | `Moderate` |
| `sebi_category_code` | TEXT | SEBI internal category code | `EC01` |

---

## dim_date

**Description:** Date dimension table covering 2022–2026. Supports slicing by year, quarter, month, and weekend/month-end flags.  
**Source:** Generated programmatically in `notebooks/day2.ipynb`  
**Grain:** One row per calendar day.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `date_key` | TEXT PK | Date in YYYY-MM-DD format | `2024-03-31` |
| `year` | INTEGER | Calendar year | `2024` |
| `quarter` | INTEGER | Quarter of year (1–4) | `1` |
| `month` | INTEGER | Month number (1–12) | `3` |
| `month_name` | TEXT | Full month name | `March` |
| `day` | INTEGER | Day of month | `31` |
| `day_of_week` | INTEGER | Day of week (0=Monday, 6=Sunday) | `6` |
| `week_of_year` | INTEGER | ISO week number | `13` |
| `is_weekend` | INTEGER | 1 if Saturday or Sunday, else 0 | `0` |
| `is_month_end` | INTEGER | 1 if last day of calendar month, else 0 | `1` |

---

## fact_nav

**Description:** Daily NAV (Net Asset Value) for each fund scheme. Includes forward-filled values for non-trading days (holidays, weekends).  
**Source:** `data/raw/02_nav_history.csv` → `data/processed/02_nav_history_cleaned.csv`  
**Grain:** One row per fund per calendar day (after ffill expansion).

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `nav_id` | INTEGER PK | Auto-increment surrogate key | `1` |
| `amfi_code` | INTEGER FK | References `dim_fund.amfi_code` | `119551` |
| `date_key` | TEXT FK | References `dim_date.date_key` | `2024-01-15` |
| `nav` | REAL | Net Asset Value in INR (must be > 0) | `68.8876` |
| `is_trading_day` | INTEGER | 1 if original trading day, 0 if forward-filled | `1` |

**Cleaning rules applied:**
- Dates parsed to datetime; invalid dates dropped
- Rows with NAV ≤ 0 removed
- Duplicates on (amfi_code, date) removed; keep first
- Sorted by amfi_code, date
- Full date range expanded per fund; NAV forward-filled for gaps (holidays/weekends)

---

## fact_transactions

**Description:** Individual investor transaction records — SIP instalments, lump sum purchases, and redemptions.  
**Source:** `data/raw/08_investor_transactions.csv` → `data/processed/08_investor_transactions_cleaned.csv`  
**Grain:** One row per transaction.

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `txn_id` | INTEGER PK | Auto-increment surrogate key | `1` |
| `investor_id` | TEXT | Anonymised investor identifier | `INV003054` |
| `date_key` | TEXT FK | Transaction date; references `dim_date.date_key` | `2024-01-01` |
| `amfi_code` | INTEGER FK | Fund invested in; references `dim_fund.amfi_code` | `119092` |
| `transaction_type` | TEXT | Standardised type: `SIP`, `Lumpsum`, or `Redemption` | `SIP` |
| `amount_inr` | REAL | Transaction amount in Indian Rupees (must be > 0) | `1834` |
| `state` | TEXT | Indian state of the investor | `Telangana` |
| `city` | TEXT | Investor's city | `Hyderabad` |
| `city_tier` | TEXT | City classification: `T30` (top 30 cities) or `B30` (beyond top 30) | `T30` |
| `age_group` | TEXT | Investor age bracket | `56+` |
| `gender` | TEXT | Male / Female | `Female` |
| `annual_income_lakh` | REAL | Self-declared annual income in lakhs INR | `77.1` |
| `payment_mode` | TEXT | UPI / Mandate / Cheque / Net Banking | `UPI` |
| `kyc_status` | TEXT | KYC verification status: Verified / Pending / Rejected | `Verified` |

**Cleaning rules applied:**
- Dates parsed and invalid dates dropped
- `transaction_type` standardised to SIP / Lumpsum / Redemption (handles lowercase, aliases)
- Rows with amount ≤ 0 removed
- `kyc_status` trimmed and title-cased
- Exact duplicates removed

---

## fact_performance

**Description:** Point-in-time scheme performance snapshot — returns, risk ratios, AUM, expense ratio, and ratings.  
**Source:** `data/raw/07_scheme_performance.csv` → `data/processed/07_scheme_performance_cleaned.csv`  
**Grain:** One row per fund scheme (snapshot).

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `perf_id` | INTEGER PK | Auto-increment surrogate key | `1` |
| `amfi_code` | INTEGER FK | References `dim_fund.amfi_code` | `119551` |
| `return_1yr_pct` | REAL | 1-year trailing return in % | `12.42` |
| `return_3yr_pct` | REAL | 3-year CAGR in % | `12.36` |
| `return_5yr_pct` | REAL | 5-year CAGR in % | `14.45` |
| `benchmark_3yr_pct` | REAL | Benchmark 3-year CAGR in % | `11.49` |
| `alpha` | REAL | Jensen's alpha (excess return over benchmark) | `0.87` |
| `beta` | REAL | Portfolio sensitivity to market movements | `0.89` |
| `sharpe_ratio` | REAL | Risk-adjusted return (return / std dev) | `0.88` |
| `sortino_ratio` | REAL | Downside-risk-adjusted return | `1.29` |
| `std_dev_ann_pct` | REAL | Annualised standard deviation of returns % | `14.0` |
| `max_drawdown_pct` | REAL | Maximum peak-to-trough decline % (negative value) | `-21.7` |
| `aum_crore` | REAL | Assets Under Management in crore INR | `14288` |
| `expense_ratio_pct` | REAL | Total Expense Ratio % (valid range: 0.1–2.5%) | `1.54` |
| `morningstar_rating` | INTEGER | Morningstar star rating (1–5) | `4` |
| `risk_grade` | TEXT | Risk label: Low / Moderate / Moderately High / High / Very High | `Moderate` |
| `anomaly_flag` | INTEGER | 1 if return or expense ratio is outside expected range | `0` |

**Cleaning rules applied:**
- All numeric columns coerced to float; invalid values → NaN
- Returns outside –50% to +100% flagged as anomalies
- Expense ratios outside 0.1%–2.5% flagged as anomalies
- `anomaly_flag = 1` marks flagged rows (not dropped)

---

## fact_aum

**Description:** Quarterly AUM snapshot per fund house — total assets, number of schemes.  
**Source:** `data/raw/03_aum_by_fund_house.csv` → `data/processed/03_aum_by_fund_house_cleaned.csv`  
**Grain:** One row per fund house per reporting date (quarterly).

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `aum_id` | INTEGER PK | Auto-increment surrogate key | `1` |
| `date_key` | TEXT FK | Quarter-end date; references `dim_date.date_key` | `2024-03-31` |
| `fund_house` | TEXT | Asset Management Company name | `SBI Mutual Fund` |
| `aum_lakh_crore` | REAL | AUM in lakh crore INR | `10.0` |
| `aum_crore` | REAL | AUM in crore INR | `1000000` |
| `num_schemes` | INTEGER | Total number of active schemes | `186` |

---

## Source File Reference

| Processed File | Raw Source | Description |
|----------------|-----------|-------------|
| `01_fund_master_cleaned.csv` | `01_fund_master.csv` | Fund scheme master data |
| `02_nav_history_cleaned.csv` | `02_nav_history.csv` | Daily NAV with ffill for non-trading days |
| `03_aum_by_fund_house_cleaned.csv` | `03_aum_by_fund_house.csv` | Quarterly AUM by AMC |
| `04_monthly_sip_inflows_cleaned.csv` | `04_monthly_sip_inflows.csv` | Industry-level monthly SIP inflows |
| `05_category_inflows_cleaned.csv` | `05_category_inflows.csv` | Monthly inflows by fund category |
| `06_industry_folio_count_cleaned.csv` | `06_industry_folio_count.csv` | Monthly industry folio counts |
| `07_scheme_performance_cleaned.csv` | `07_scheme_performance.csv` | Scheme returns, ratios, ratings |
| `08_investor_transactions_cleaned.csv` | `08_investor_transactions.csv` | Investor-level buy/sell transactions |
| `09_portfolio_holdings_cleaned.csv` | `09_portfolio_holdings.csv` | Fund stock-level portfolio holdings |
| `10_benchmark_indices_cleaned.csv` | `10_benchmark_indices.csv` | Benchmark index daily values |

---

*Content was structured from source CSV column analysis and domain knowledge of Indian mutual funds.*
