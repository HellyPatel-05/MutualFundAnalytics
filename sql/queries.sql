-- ============================================================
-- bluestock_mf.db  |  10 Analytical Queries
-- Day 2: Mutual Fund Analytics
-- ============================================================

-- Q1: Top 5 fund houses by latest total AUM
-- ──────────────────────────────────────────
SELECT fund_house,
       ROUND(aum_crore / 1e5, 2) AS aum_lakh_crore
FROM fact_aum
WHERE date_key = (SELECT MAX(date_key) FROM fact_aum)
ORDER BY aum_crore DESC
LIMIT 5;


-- Q2: Average NAV per month across all funds (trading days only)
-- ──────────────────────────────────────────────────────────────
SELECT d.year,
       d.month,
       d.month_name,
       ROUND(AVG(n.nav), 4) AS avg_nav,
       COUNT(*)             AS data_points
FROM fact_nav n
JOIN dim_date d ON n.date_key = d.date_key
WHERE n.is_trading_day = 1
GROUP BY d.year, d.month
ORDER BY d.year, d.month;


-- Q3: SIP inflow YoY growth by year
-- ──────────────────────────────────
SELECT strftime('%Y', month)       AS year,
       ROUND(SUM(sip_inflow_crore), 0) AS total_sip_crore,
       ROUND(AVG(yoy_growth_pct), 2)   AS avg_yoy_growth_pct
FROM fact_sip_inflows
WHERE yoy_growth_pct IS NOT NULL
GROUP BY year
ORDER BY year;


-- Q4: Total transaction count and value by state (top 10)
-- ─────────────────────────────────────────────────────────
SELECT state,
       COUNT(*)                               AS num_transactions,
       ROUND(SUM(amount_inr) / 1e7, 2)        AS total_amount_crore
FROM fact_transactions
GROUP BY state
ORDER BY total_amount_crore DESC
LIMIT 10;


-- Q5: Funds with expense_ratio < 1%
-- ───────────────────────────────────
SELECT f.scheme_name,
       f.fund_house,
       f.category,
       p.expense_ratio_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.expense_ratio_pct < 1.0
ORDER BY p.expense_ratio_pct ASC;


-- Q6: Top 5 funds by 5-year return
-- ──────────────────────────────────
SELECT f.scheme_name,
       f.fund_house,
       f.sub_category,
       p.return_5yr_pct,
       p.return_3yr_pct,
       p.return_1yr_pct
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
ORDER BY p.return_5yr_pct DESC
LIMIT 5;


-- Q7: Monthly SIP count and average ticket size
-- ───────────────────────────────────────────────
SELECT d.year,
       d.month,
       d.month_name,
       COUNT(*)                    AS sip_count,
       ROUND(AVG(t.amount_inr), 0) AS avg_sip_amount
FROM fact_transactions t
JOIN dim_date d ON t.date_key = d.date_key
WHERE t.transaction_type = 'SIP'
GROUP BY d.year, d.month
ORDER BY d.year, d.month;


-- Q8: Fund house AUM growth (first vs latest recorded period)
-- ────────────────────────────────────────────────────────────
WITH ranked AS (
    SELECT fund_house, aum_crore, date_key,
           RANK() OVER (PARTITION BY fund_house ORDER BY date_key ASC)  AS rk_asc,
           RANK() OVER (PARTITION BY fund_house ORDER BY date_key DESC) AS rk_desc
    FROM fact_aum
),
first_last AS (
    SELECT fund_house,
           MAX(CASE WHEN rk_asc  = 1 THEN aum_crore END) AS first_aum,
           MAX(CASE WHEN rk_desc = 1 THEN aum_crore END) AS last_aum
    FROM ranked
    GROUP BY fund_house
)
SELECT fund_house,
       ROUND(first_aum / 1e5, 2) AS first_aum_lakh_cr,
       ROUND(last_aum  / 1e5, 2) AS latest_aum_lakh_cr,
       ROUND((last_aum - first_aum) * 100.0 / first_aum, 1) AS growth_pct
FROM first_last
ORDER BY growth_pct DESC;


-- Q9: Redemption transactions — KYC status breakdown
-- ────────────────────────────────────────────────────
SELECT kyc_status,
       COUNT(*)                          AS redemption_count,
       ROUND(SUM(amount_inr) / 1e7, 2)  AS total_crore
FROM fact_transactions
WHERE transaction_type = 'Redemption'
GROUP BY kyc_status
ORDER BY redemption_count DESC;


-- Q10: Quality screen — alpha > 1 AND sharpe_ratio > 1
-- ──────────────────────────────────────────────────────
SELECT f.scheme_name,
       f.sub_category,
       p.alpha,
       p.sharpe_ratio,
       p.return_3yr_pct,
       p.expense_ratio_pct,
       p.morningstar_rating
FROM fact_performance p
JOIN dim_fund f ON p.amfi_code = f.amfi_code
WHERE p.alpha > 1
  AND p.sharpe_ratio > 1
ORDER BY p.sharpe_ratio DESC;
