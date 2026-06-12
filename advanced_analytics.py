"""
advanced_analytics.py — Advanced Analytics Engine
===================================================
Bluestock MF Analytics Capstone Project

Runs five advanced analytical modules on the cleaned mutual fund data:

1. Historical VaR & CVaR (95%)
   - Value-at-Risk: 5th percentile of daily returns
   - Conditional VaR: mean return below VaR threshold
   - Reported daily and annualised (×√252) for all 40 funds

2. Rolling 90-Day Sharpe Ratio
   - Computed for 5 key funds over the full date range
   - Annotated with 2023 bull run and 2024 market correction periods

3. Investor Cohort Analysis
   - Groups investors by first-transaction year (2022–2025)
   - Metrics: unique investors, total invested, avg SIP, top fund preference

4. SIP Continuity Analysis
   - Identifies investors with 6+ SIP transactions
   - Flags at-risk investors (avg gap between SIPs > 35 days)
   - Computes industry SIP continuity rate

5. Sector HHI Concentration
   - Herfindahl-Hirschman Index per equity fund by sector weights
   - Classified: Diversified (<0.15), Moderate (0.15–0.25), Concentrated (>0.25)

Outputs
-------
    data/processed/var_cvar_report.csv
    data/processed/investor_cohort_analysis.csv
    data/processed/sip_continuity_analysis.csv
    data/processed/sector_hhi_report.csv
    reports/charts/var_cvar_chart.png
    reports/charts/rolling_sharpe_chart.png
    reports/charts/investor_cohort_chart.png
    reports/charts/sip_continuity_chart.png
    reports/charts/sector_hhi_chart.png

Usage
-----
    python advanced_analytics.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import seaborn as sns
from scipy import stats
import warnings, os
warnings.filterwarnings('ignore')

PROCESSED = 'data/processed/'
RAW       = 'data/raw/'
CHARTS    = 'reports/charts/'
os.makedirs(CHARTS, exist_ok=True)

sns.set_theme(style='whitegrid', font_scale=1.1)
TRADING_DAYS = 252
RF_DAILY     = 0.065 / 252

print("=" * 65)
print("Advanced Analytics — Day 5")
print("=" * 65)

# ─────────────────────────────────────────────────────────────────
# Load Data
# ─────────────────────────────────────────────────────────────────
nav      = pd.read_csv(PROCESSED + '02_nav_history_cleaned.csv', parse_dates=['date'])
fund     = pd.read_csv(PROCESSED + '01_fund_master_cleaned.csv')
perf     = pd.read_csv(PROCESSED + '07_scheme_performance_cleaned.csv')
txn      = pd.read_csv(PROCESSED + '08_investor_transactions_cleaned.csv',
                        parse_dates=['transaction_date'])
holdings = pd.read_csv(RAW + '09_portfolio_holdings.csv')
scorecard = pd.read_csv(PROCESSED + 'fund_scorecard.csv')

nav_t     = nav[nav['is_trading_day'] == 1].sort_values(['amfi_code', 'date'])
nav_pivot = nav_t.pivot_table(index='date', columns='amfi_code', values='nav')
daily_ret = nav_pivot.pct_change().dropna(how='all')

equity_codes = fund[fund['category'] == 'Equity']['amfi_code'].tolist()
fund_map     = fund.set_index('amfi_code')['scheme_name'].to_dict()
risk_map     = fund.set_index('amfi_code')['risk_category'].to_dict()

print(f"  NAV pivot  : {nav_pivot.shape[1]} funds × {nav_pivot.shape[0]} days")
print(f"  Transactions: {len(txn):,} rows")
print(f"  Holdings   : {len(holdings)} rows across {holdings['amfi_code'].nunique()} funds")


# ═══════════════════════════════════════════════════════════════════
# 1. Historical VaR (95%) and CVaR for all 40 schemes
# ═══════════════════════════════════════════════════════════════════
print("\n[1] VaR (95%) and CVaR for all 40 schemes...")

var_rows = []
for code in daily_ret.columns:
    r = daily_ret[code].dropna()
    if len(r) < 30:
        continue
    var_95  = float(np.percentile(r, 5))          # 5th percentile (worst 5%)
    cvar_95 = float(r[r <= var_95].mean())         # mean of returns below VaR
    var_rows.append({
        'amfi_code'          : code,
        'scheme_name'        : fund_map.get(code, str(code)),
        'risk_grade'         : risk_map.get(code, ''),
        'var_95_daily_pct'   : round(var_95  * 100, 4),
        'cvar_95_daily_pct'  : round(cvar_95 * 100, 4),
        'var_95_annual_pct'  : round(var_95  * 100 * np.sqrt(TRADING_DAYS), 4),
        'cvar_95_annual_pct' : round(cvar_95 * 100 * np.sqrt(TRADING_DAYS), 4),
        'num_obs'            : len(r),
        'mean_daily_ret_pct' : round(r.mean() * 100, 4),
        'std_daily_ret_pct'  : round(r.std()  * 100, 4),
    })

var_df = pd.DataFrame(var_rows)
var_df['var_rank']  = var_df['var_95_daily_pct'].rank(ascending=True).astype(int)   # most negative = riskiest
var_df['cvar_rank'] = var_df['cvar_95_daily_pct'].rank(ascending=True).astype(int)
var_df = var_df.sort_values('var_95_daily_pct')

print("\n  VaR / CVaR Table (sorted riskiest first):")
print(var_df[['scheme_name', 'var_95_daily_pct', 'cvar_95_daily_pct',
              'var_95_annual_pct', 'risk_grade']].to_string(index=False))

var_df.to_csv(PROCESSED + 'var_cvar_report.csv', index=False)
print(f"\n  Saved → {PROCESSED}var_cvar_report.csv")

# VaR chart
fig, ax = plt.subplots(figsize=(13, 8))
colors = ['#E53935' if v < -1.0 else '#FB8C00' if v < -0.7 else '#43A047'
          for v in var_df['var_95_daily_pct']]
bars = ax.barh(var_df['scheme_name'].str[:35], var_df['var_95_daily_pct'],
               color=colors, edgecolor='white', height=0.7)
ax.barh(var_df['scheme_name'].str[:35], var_df['cvar_95_daily_pct'],
        color='none', edgecolor='#1565C0', linewidth=1.5, height=0.7, label='CVaR 95%')
ax.axvline(0, color='black', linewidth=0.8)
ax.axvline(-1.0, color='red', linestyle='--', linewidth=1, label='−1% threshold')
ax.set_title('Historical VaR (95%) & CVaR — All 40 Funds (Daily %)',
             fontsize=13, fontweight='bold')
ax.set_xlabel('Return (%)')
ax.legend(fontsize=9)
ax.tick_params(labelsize=8)
plt.tight_layout()
plt.savefig(CHARTS + 'var_cvar_chart.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Chart saved → {CHARTS}var_cvar_chart.png")


# ═══════════════════════════════════════════════════════════════════
# 2. Rolling 90-day Sharpe — 5 key funds
# ═══════════════════════════════════════════════════════════════════
print("\n[2] Rolling 90-day Sharpe for 5 key funds...")

KEY_FUNDS = {
    119551: 'SBI Bluechip Reg',
    120503: 'ICICI Bluechip Reg',
    100033: 'HDFC MidCap Opp',
    119092: 'Axis Bluechip Reg',
    148567: 'Mirae Large Cap',
}

fig, ax = plt.subplots(figsize=(15, 6))
palette = ['#1565C0', '#E53935', '#43A047', '#FB8C00', '#8E24AA']

for (code, label), color in zip(KEY_FUNDS.items(), palette):
    if code not in daily_ret.columns:
        continue
    r = daily_ret[code].dropna()
    roll_mean = r.rolling(90).mean()
    roll_std  = r.rolling(90).std()
    roll_sharpe = ((roll_mean - RF_DAILY) / roll_std) * np.sqrt(TRADING_DAYS)
    ax.plot(roll_sharpe.index, roll_sharpe.values,
            label=label, color=color, linewidth=2, alpha=0.9)

ax.axhline(0,   color='black',  linewidth=0.8, linestyle='-')
ax.axhline(1.0, color='grey',   linewidth=1,   linestyle='--', alpha=0.6, label='Sharpe=1.0')
ax.axhline(-0.5,color='grey',   linewidth=1,   linestyle=':',  alpha=0.4)
ax.set_title('Rolling 90-Day Sharpe Ratio — 5 Key Funds', fontsize=13, fontweight='bold')
ax.set_xlabel('Date')
ax.set_ylabel('Sharpe Ratio (annualised)')
ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax.grid(True, alpha=0.3)
ax.set_xlim(daily_ret.index.min(), daily_ret.index.max())

# Annotate 2023 bull run and 2024 correction
ax.axvspan(pd.Timestamp('2023-01-01'), pd.Timestamp('2023-12-31'),
           alpha=0.06, color='green', label='_2023 Bull Run')
ax.axvspan(pd.Timestamp('2024-09-01'), pd.Timestamp('2024-12-31'),
           alpha=0.06, color='red', label='_2024 Correction')
ax.text(pd.Timestamp('2023-04-01'), ax.get_ylim()[1]*0.92, '2023 Bull Run',
        fontsize=9, color='green', alpha=0.8)
ax.text(pd.Timestamp('2024-09-15'), ax.get_ylim()[1]*0.92, '2024 Correction',
        fontsize=9, color='red', alpha=0.8)

plt.tight_layout()
plt.savefig(CHARTS + 'rolling_sharpe_chart.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved → {CHARTS}rolling_sharpe_chart.png")


# ═══════════════════════════════════════════════════════════════════
# 3. Investor Cohort Analysis
# ═══════════════════════════════════════════════════════════════════
print("\n[3] Investor cohort analysis...")

txn['year'] = txn['transaction_date'].dt.year

# First transaction year per investor
first_year = (txn.groupby('investor_id')['transaction_date']
              .min().dt.year.rename('cohort_year').reset_index())
txn_cohort = txn.merge(first_year, on='investor_id', how='left')

# SIP transactions only for SIP metrics
sip_cohort = txn_cohort[txn_cohort['transaction_type'] == 'SIP']

cohort_stats = (txn_cohort.groupby('cohort_year').agg(
    num_investors   = ('investor_id', 'nunique'),
    total_txns      = ('investor_id', 'count'),
    total_invested  = ('amount_inr', 'sum'),
    avg_txn_amount  = ('amount_inr', 'mean'),
).reset_index())

sip_stats = (sip_cohort.groupby('cohort_year').agg(
    avg_sip_amount = ('amount_inr', 'mean'),
    sip_count      = ('investor_id', 'count'),
).reset_index())

cohort_stats = cohort_stats.merge(sip_stats, on='cohort_year', how='left')
cohort_stats['total_invested_cr'] = (cohort_stats['total_invested'] / 1e7).round(2)
cohort_stats['avg_sip_amount']    = cohort_stats['avg_sip_amount'].round(0)

# Top fund preference per cohort
top_fund_per_cohort = (txn_cohort.groupby(['cohort_year', 'amfi_code'])['amount_inr']
    .sum().reset_index()
    .sort_values('amount_inr', ascending=False)
    .groupby('cohort_year').first()
    .reset_index()[['cohort_year', 'amfi_code']])
top_fund_per_cohort['top_fund'] = top_fund_per_cohort['amfi_code'].map(fund_map)
cohort_stats = cohort_stats.merge(
    top_fund_per_cohort[['cohort_year', 'top_fund']], on='cohort_year', how='left')

print("\n  Investor Cohort Table:")
print(cohort_stats[['cohort_year', 'num_investors', 'total_txns',
                    'total_invested_cr', 'avg_sip_amount', 'top_fund']].to_string(index=False))
cohort_stats.to_csv(PROCESSED + 'investor_cohort_analysis.csv', index=False)
print(f"  Saved → {PROCESSED}investor_cohort_analysis.csv")

# Cohort bar chart
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].bar(cohort_stats['cohort_year'].astype(str),
            cohort_stats['total_invested_cr'],
            color='#1565C0', edgecolor='white')
axes[0].set_title('Total Invested by Cohort (₹ Cr)', fontweight='bold')
axes[0].set_xlabel('First Investment Year')
axes[0].set_ylabel('Total Invested (₹ Cr)')

axes[1].bar(cohort_stats['cohort_year'].astype(str),
            cohort_stats['avg_sip_amount'],
            color='#43A047', edgecolor='white')
axes[1].set_title('Avg SIP Amount by Cohort (₹)', fontweight='bold')
axes[1].set_xlabel('First Investment Year')
axes[1].set_ylabel('Avg SIP Amount (₹)')
axes[1].yaxis.set_major_formatter(mtick.FuncFormatter(lambda x, _: f'₹{x:,.0f}'))

plt.tight_layout()
plt.savefig(CHARTS + 'investor_cohort_chart.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Chart saved → {CHARTS}investor_cohort_chart.png")


# ═══════════════════════════════════════════════════════════════════
# 4. SIP Continuity Analysis
# ═══════════════════════════════════════════════════════════════════
print("\n[4] SIP continuity analysis...")

sip_txn = txn[txn['transaction_type'] == 'SIP'].copy()
sip_txn = sip_txn.sort_values(['investor_id', 'transaction_date'])

# Investors with 6+ SIP transactions
sip_counts = sip_txn.groupby('investor_id').size()
active_investors = sip_counts[sip_counts >= 6].index

sip_active = sip_txn[sip_txn['investor_id'].isin(active_investors)].copy()

# Compute avg gap between consecutive SIP dates per investor
def avg_gap(dates):
    dates = sorted(dates)
    if len(dates) < 2:
        return np.nan
    gaps = [(dates[i+1] - dates[i]).days for i in range(len(dates)-1)]
    return np.mean(gaps)

investor_gaps = (sip_active.groupby('investor_id')['transaction_date']
                 .apply(avg_gap).reset_index())
investor_gaps.columns = ['investor_id', 'avg_gap_days']
investor_gaps['sip_count'] = investor_gaps['investor_id'].map(sip_counts)
investor_gaps['at_risk'] = investor_gaps['avg_gap_days'] > 35

# Summary stats
total_active    = len(investor_gaps)
at_risk_count   = investor_gaps['at_risk'].sum()
continuity_rate = (1 - at_risk_count / total_active) * 100

print(f"\n  Investors with 6+ SIPs : {total_active:,}")
print(f"  At-risk (gap > 35 days): {at_risk_count:,} ({at_risk_count/total_active*100:.1f}%)")
print(f"  SIP Continuity Rate    : {continuity_rate:.1f}%")
print(f"  Avg gap — all investors: {investor_gaps['avg_gap_days'].mean():.1f} days")
print(f"  Median gap             : {investor_gaps['avg_gap_days'].median():.1f} days")

investor_gaps.to_csv(PROCESSED + 'sip_continuity_analysis.csv', index=False)
print(f"  Saved → {PROCESSED}sip_continuity_analysis.csv")

# Gap distribution chart
fig, axes = plt.subplots(1, 2, figsize=(13, 5))
axes[0].hist(investor_gaps['avg_gap_days'].dropna(), bins=40,
             color='#1565C0', edgecolor='white', alpha=0.85)
axes[0].axvline(35, color='red', linestyle='--', linewidth=2, label='35-day threshold')
axes[0].set_title('Distribution of Avg SIP Gap (Days)', fontweight='bold')
axes[0].set_xlabel('Avg Gap (Days)')
axes[0].set_ylabel('Number of Investors')
axes[0].legend()

risk_counts = investor_gaps['at_risk'].value_counts()
labels = ['On Track', 'At Risk']
colors_pie = ['#43A047', '#E53935']
axes[1].pie([risk_counts.get(False, 0), risk_counts.get(True, 0)],
            labels=labels, colors=colors_pie, autopct='%1.1f%%',
            startangle=90, wedgeprops=dict(edgecolor='white', linewidth=2))
axes[1].set_title(f'SIP Continuity Status\n(Continuity Rate: {continuity_rate:.1f}%)', fontweight='bold')

plt.tight_layout()
plt.savefig(CHARTS + 'sip_continuity_chart.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Chart saved → {CHARTS}sip_continuity_chart.png")


# ═══════════════════════════════════════════════════════════════════
# 5. Sector HHI Concentration
# ═══════════════════════════════════════════════════════════════════
print("\n[5] Sector HHI concentration...")

eq_holdings = holdings[holdings['amfi_code'].isin(equity_codes)].copy()

def hhi(weights):
    """HHI = sum of squared sector weights (normalised to sum=1)"""
    w = np.array(weights, dtype=float)
    w = w / w.sum()          # normalise
    return float((w ** 2).sum())

hhi_rows = []
for code, grp in eq_holdings.groupby('amfi_code'):
    # Aggregate by sector
    sector_wts = grp.groupby('sector')['weight_pct'].sum()
    h = hhi(sector_wts.values)
    hhi_rows.append({
        'amfi_code'     : code,
        'scheme_name'   : fund_map.get(code, str(code)),
        'hhi'           : round(h, 4),
        'num_sectors'   : len(sector_wts),
        'top_sector'    : sector_wts.idxmax(),
        'top_sector_wt' : round(sector_wts.max(), 2),
    })

hhi_df = pd.DataFrame(hhi_rows).sort_values('hhi', ascending=False)
hhi_df['concentration'] = pd.cut(hhi_df['hhi'],
    bins=[0, 0.15, 0.25, 1.0],
    labels=['Diversified (HHI<0.15)', 'Moderate (0.15-0.25)', 'Concentrated (>0.25)'])

print("\n  Sector HHI Table (most concentrated first):")
print(hhi_df[['scheme_name', 'hhi', 'num_sectors', 'top_sector',
              'top_sector_wt', 'concentration']].to_string(index=False))
hhi_df.to_csv(PROCESSED + 'sector_hhi_report.csv', index=False)
print(f"  Saved → {PROCESSED}sector_hhi_report.csv")

# HHI chart
fig, ax = plt.subplots(figsize=(11, 7))
color_map = {'Diversified (HHI<0.15)': '#43A047',
             'Moderate (0.15-0.25)'  : '#FB8C00',
             'Concentrated (>0.25)'  : '#E53935'}
bar_colors = [color_map.get(str(c), '#90CAF9') for c in hhi_df['concentration']]
ax.barh(hhi_df['scheme_name'].str[:35], hhi_df['hhi'],
        color=bar_colors, edgecolor='white')
ax.axvline(0.15, color='orange', linestyle='--', linewidth=1.5, label='Moderate threshold (0.15)')
ax.axvline(0.25, color='red',    linestyle='--', linewidth=1.5, label='Concentrated threshold (0.25)')
ax.set_title('Sector HHI Concentration — Equity Funds\n(Higher = More Concentrated)',
             fontsize=12, fontweight='bold')
ax.set_xlabel('HHI Score')
ax.legend(fontsize=9); ax.tick_params(labelsize=8)
# Legend for colours
from matplotlib.patches import Patch
legend_els = [Patch(color=c, label=l) for l, c in color_map.items()]
ax.legend(handles=legend_els, loc='lower right', fontsize=8)
plt.tight_layout()
plt.savefig(CHARTS + 'sector_hhi_chart.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Chart saved → {CHARTS}sector_hhi_chart.png")


# ═══════════════════════════════════════════════════════════════════
# Summary print
# ═══════════════════════════════════════════════════════════════════
print("\n" + "=" * 65)
print("OUTPUTS GENERATED")
print("=" * 65)
outputs = [
    'data/processed/var_cvar_report.csv',
    'data/processed/investor_cohort_analysis.csv',
    'data/processed/sip_continuity_analysis.csv',
    'data/processed/sector_hhi_report.csv',
    'reports/charts/var_cvar_chart.png',
    'reports/charts/rolling_sharpe_chart.png',
    'reports/charts/investor_cohort_chart.png',
    'reports/charts/sip_continuity_chart.png',
    'reports/charts/sector_hhi_chart.png',
]
for o in outputs:
    size = os.path.getsize(o) // 1024 if os.path.exists(o) else 0
    status = "OK" if os.path.exists(o) else "MISSING"
    print(f"  [{status}] {o} ({size} KB)")
print("=" * 65)
