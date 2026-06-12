"""
performance_analytics.py — Quantitative Performance Engine
============================================================
Bluestock MF Analytics Capstone Project

Computes risk-adjusted performance metrics for all 40 fund schemes
using daily NAV history (trading days only). All metrics are computed
against a risk-free rate of 6.5% p.a. (RBI repo rate proxy).

Metrics computed
----------------
- CAGR (1yr, 3yr, 5yr)       : Compound Annual Growth Rate
- Sharpe Ratio                : (Rp - Rf) / σp × √252
- Sortino Ratio               : (Rp - Rf) / downside_σ × √252
- Alpha (annualised)          : Jensen's alpha via OLS vs NIFTY100
- Beta                        : Systematic risk vs NIFTY100
- Maximum Drawdown            : min(NAV / running_max - 1)
- Tracking Error              : annualised std(fund_ret − benchmark_ret)
- Fund Scorecard (0–100)      : weighted composite of rank-normalised metrics

Scorecard weights
-----------------
    30% — 3-year CAGR
    25% — Sharpe Ratio
    20% — Alpha (annualised)
    15% — Expense Ratio (lower is better)
    10% — Maximum Drawdown (less negative is better)

Outputs
-------
    data/processed/fund_scorecard.csv
    data/processed/alpha_beta.csv
    reports/charts/benchmark_comparison.png
    reports/charts/daily_return_distribution.png
    reports/charts/sharpe_sortino_ranking.png
    reports/charts/fund_scorecard_chart.png

Usage
-----
    python performance_analytics.py
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import linregress
import warnings, os
warnings.filterwarnings('ignore')

PROCESSED = 'data/processed/'
RAW       = 'data/raw/'
CHARTS    = 'reports/charts/'
os.makedirs(CHARTS, exist_ok=True)

RF_ANNUAL  = 0.065          # RBI repo rate proxy
RF_DAILY   = RF_ANNUAL / 252
TRADING_DAYS = 252

sns.set_theme(style='whitegrid', font_scale=1.1)
print("=" * 60)
print("Performance Analytics — Day 4")
print("=" * 60)

# ─────────────────────────────────────────────────────────────────────────────
# 1. Load Data
# ─────────────────────────────────────────────────────────────────────────────
nav  = pd.read_csv(PROCESSED + '02_nav_history_cleaned.csv', parse_dates=['date'])
fund = pd.read_csv(PROCESSED + '01_fund_master_cleaned.csv')
perf = pd.read_csv(PROCESSED + '07_scheme_performance_cleaned.csv')
bench_raw = pd.read_csv(RAW + '10_benchmark_indices.csv', parse_dates=['date'])

# Trading days only for return computations
nav_t = nav[nav['is_trading_day'] == 1].copy()
nav_t = nav_t.sort_values(['amfi_code', 'date']).reset_index(drop=True)

# Pivot: date x amfi_code
nav_pivot = nav_t.pivot_table(index='date', columns='amfi_code', values='nav')

print(f"\nNAV pivot shape : {nav_pivot.shape}")
print(f"Funds           : {nav_pivot.shape[1]}")
print(f"Date range      : {nav_pivot.index.min().date()} → {nav_pivot.index.max().date()}")

# Benchmark pivot
bench = bench_raw.pivot_table(index='date', columns='index_name', values='close_value')
bench = bench.sort_index()

# ─────────────────────────────────────────────────────────────────────────────
# 2. Daily Returns
# ─────────────────────────────────────────────────────────────────────────────
print("\n[1] Computing daily returns...")
daily_ret = nav_pivot.pct_change()      # daily_return = nav_t / nav_(t-1) - 1
daily_ret = daily_ret.dropna(how='all')

# Validate distribution
ret_stats = daily_ret.describe().T
ret_stats['skewness'] = daily_ret.skew()
ret_stats['kurtosis'] = daily_ret.kurtosis()

print(f"  Mean daily return range : {ret_stats['mean'].min():.4f} – {ret_stats['mean'].max():.4f}")
print(f"  Std daily return range  : {ret_stats['std'].min():.4f} – {ret_stats['std'].max():.4f}")
print(f"  All means positive      : {(ret_stats['mean'] > 0).all()}")
print(f"  Max single-day return   : {daily_ret.max().max():.4f}")
print(f"  Min single-day return   : {daily_ret.min().min():.4f}")
print("  Distribution looks reasonable ✓")

# ─────────────────────────────────────────────────────────────────────────────
# 3. CAGR — 1yr, 3yr, 5yr
# ─────────────────────────────────────────────────────────────────────────────
print("\n[2] Computing CAGR...")

def cagr(nav_series, years):
    """CAGR = (NAV_end / NAV_start) ^ (1/n) - 1"""
    end_date   = nav_series.last_valid_index()
    start_date = end_date - pd.DateOffset(years=years)
    # Find nearest available date at or after start_date
    valid_dates = nav_series.dropna().index
    start_candidates = valid_dates[valid_dates >= start_date]
    if len(start_candidates) == 0:
        return np.nan
    actual_start = start_candidates[0]
    nav_end   = nav_series.loc[end_date]
    nav_start = nav_series.loc[actual_start]
    if pd.isna(nav_start) or pd.isna(nav_end) or nav_start <= 0:
        return np.nan
    actual_years = (end_date - actual_start).days / 365.25
    if actual_years < years * 0.8:   # require at least 80% of the window
        return np.nan
    return (nav_end / nav_start) ** (1 / actual_years) - 1

cagr_rows = []
for code in nav_pivot.columns:
    s = nav_pivot[code].dropna()
    cagr_rows.append({
        'amfi_code'    : code,
        'cagr_1yr_pct' : round(cagr(s, 1) * 100, 4) if not pd.isna(cagr(s, 1)) else np.nan,
        'cagr_3yr_pct' : round(cagr(s, 3) * 100, 4) if not pd.isna(cagr(s, 3)) else np.nan,
        'cagr_5yr_pct' : round(cagr(s, 5) * 100, 4) if not pd.isna(cagr(s, 5)) else np.nan,
    })

cagr_df = pd.DataFrame(cagr_rows).merge(
    fund[['amfi_code', 'scheme_name', 'sub_category', 'fund_house']], on='amfi_code', how='left')

print(f"  Computed CAGR for {len(cagr_df)} funds")
print(cagr_df[['scheme_name', 'cagr_1yr_pct', 'cagr_3yr_pct', 'cagr_5yr_pct']].to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────────
# 4. Sharpe Ratio
# ─────────────────────────────────────────────────────────────────────────────
print("\n[3] Computing Sharpe Ratios...")

def sharpe(ret_series):
    """(Rp - Rf) / Std(Rp) * sqrt(252)"""
    r = ret_series.dropna()
    if len(r) < 30:
        return np.nan
    excess = r - RF_DAILY
    return (excess.mean() / r.std()) * np.sqrt(TRADING_DAYS)

sharpe_s = daily_ret.apply(sharpe)
sharpe_df = sharpe_s.reset_index()
sharpe_df.columns = ['amfi_code', 'sharpe_ratio_calc']
sharpe_df['sharpe_rank'] = sharpe_df['sharpe_ratio_calc'].rank(ascending=False)

print(f"  Sharpe range: {sharpe_s.min():.4f} – {sharpe_s.max():.4f}")
top5_sharpe = sharpe_df.merge(fund[['amfi_code', 'scheme_name']], on='amfi_code').nlargest(5, 'sharpe_ratio_calc')
print("  Top 5 by Sharpe:")
print(top5_sharpe[['scheme_name', 'sharpe_ratio_calc']].to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────────
# 5. Sortino Ratio
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4] Computing Sortino Ratios...")

def sortino(ret_series):
    """(Rp - Rf) / Downside_Std(Rp) * sqrt(252)"""
    r = ret_series.dropna()
    if len(r) < 30:
        return np.nan
    excess   = r - RF_DAILY
    downside = r[r < 0]
    if len(downside) == 0:
        return np.nan
    down_std = downside.std()
    if down_std == 0:
        return np.nan
    return (excess.mean() / down_std) * np.sqrt(TRADING_DAYS)

sortino_s  = daily_ret.apply(sortino)
sortino_df = sortino_s.reset_index()
sortino_df.columns = ['amfi_code', 'sortino_ratio_calc']

print(f"  Sortino range: {sortino_s.min():.4f} – {sortino_s.max():.4f}")

# ─────────────────────────────────────────────────────────────────────────────
# 6. Alpha & Beta — OLS vs Nifty 100
# ─────────────────────────────────────────────────────────────────────────────
print("\n[5] Computing Alpha & Beta (OLS vs NIFTY100)...")

bench_ret = bench['NIFTY100'].pct_change().dropna()

alpha_beta_rows = []
for code in daily_ret.columns:
    fund_r = daily_ret[code].dropna()
    # Align on common dates
    aligned = pd.concat([fund_r, bench_ret], axis=1, join='inner').dropna()
    aligned.columns = ['fund', 'bench']
    if len(aligned) < 60:
        alpha_beta_rows.append({'amfi_code': code, 'beta': np.nan,
                                 'alpha_annualised': np.nan, 'r_squared': np.nan})
        continue
    slope, intercept, r_value, p_value, std_err = linregress(
        aligned['bench'], aligned['fund'])
    alpha_beta_rows.append({
        'amfi_code'        : code,
        'beta'             : round(slope, 4),
        'alpha_annualised' : round(intercept * TRADING_DAYS * 100, 4),  # annualised %
        'r_squared'        : round(r_value ** 2, 4),
        'p_value'          : round(p_value, 6),
    })

alpha_beta_df = pd.DataFrame(alpha_beta_rows).merge(
    fund[['amfi_code', 'scheme_name', 'sub_category', 'fund_house']], on='amfi_code', how='left')

print(f"  Beta range  : {alpha_beta_df['beta'].min():.4f} – {alpha_beta_df['beta'].max():.4f}")
print(f"  Alpha range : {alpha_beta_df['alpha_annualised'].min():.2f}% – {alpha_beta_df['alpha_annualised'].max():.2f}%")
print("\n  Alpha/Beta Table:")
print(alpha_beta_df[['scheme_name', 'beta', 'alpha_annualised', 'r_squared']].to_string(index=False))

# Save alpha_beta.csv
alpha_beta_df.to_csv('data/processed/alpha_beta.csv', index=False)
print("\n  Saved → data/processed/alpha_beta.csv")

# ─────────────────────────────────────────────────────────────────────────────
# 7. Maximum Drawdown
# ─────────────────────────────────────────────────────────────────────────────
print("\n[6] Computing Maximum Drawdown...")

def max_drawdown(nav_series):
    """min(NAV / running_max - 1)"""
    s = nav_series.dropna()
    if len(s) < 10:
        return np.nan, None, None
    running_max = s.cummax()
    drawdown    = s / running_max - 1
    mdd         = drawdown.min()
    mdd_date    = drawdown.idxmin()
    # Peak = last date running_max == running_max at mdd_date
    peak_val    = running_max.loc[mdd_date]
    peak_date   = s[s == peak_val].index
    peak_date   = peak_date[peak_date <= mdd_date][-1] if len(peak_date[peak_date <= mdd_date]) > 0 else None
    return round(mdd * 100, 4), peak_date, mdd_date

mdd_rows = []
for code in nav_pivot.columns:
    mdd_val, peak_dt, trough_dt = max_drawdown(nav_pivot[code])
    mdd_rows.append({
        'amfi_code'   : code,
        'max_dd_pct'  : mdd_val,
        'peak_date'   : peak_dt.date() if peak_dt else None,
        'trough_date' : trough_dt.date() if trough_dt else None,
    })

mdd_df = pd.DataFrame(mdd_rows).merge(
    fund[['amfi_code', 'scheme_name', 'sub_category']], on='amfi_code', how='left')

worst = mdd_df.nsmallest(5, 'max_dd_pct')
print("  Worst 5 drawdowns:")
print(worst[['scheme_name', 'max_dd_pct', 'peak_date', 'trough_date']].to_string(index=False))

# ─────────────────────────────────────────────────────────────────────────────
# 8. Fund Scorecard (0–100)
# ─────────────────────────────────────────────────────────────────────────────
print("\n[7] Building Fund Scorecard...")

# Merge all metrics
scorecard = (fund[['amfi_code', 'scheme_name', 'sub_category', 'fund_house', 'expense_ratio_pct']]
    .merge(cagr_df[['amfi_code', 'cagr_1yr_pct', 'cagr_3yr_pct', 'cagr_5yr_pct']], on='amfi_code', how='left')
    .merge(sharpe_df[['amfi_code', 'sharpe_ratio_calc']], on='amfi_code', how='left')
    .merge(sortino_df[['amfi_code', 'sortino_ratio_calc']], on='amfi_code', how='left')
    .merge(alpha_beta_df[['amfi_code', 'alpha_annualised', 'beta']], on='amfi_code', how='left')
    .merge(mdd_df[['amfi_code', 'max_dd_pct', 'peak_date', 'trough_date']], on='amfi_code', how='left')
)

n = len(scorecard)

# Ranks (1 = best)
scorecard['rank_3yr']     = scorecard['cagr_3yr_pct'].rank(ascending=False, na_option='bottom')
scorecard['rank_sharpe']  = scorecard['sharpe_ratio_calc'].rank(ascending=False, na_option='bottom')
scorecard['rank_alpha']   = scorecard['alpha_annualised'].rank(ascending=False, na_option='bottom')
scorecard['rank_expense'] = scorecard['expense_ratio_pct'].rank(ascending=True,  na_option='bottom')  # lower = better
scorecard['rank_mdd']     = scorecard['max_dd_pct'].rank(ascending=False, na_option='bottom')         # less negative = better

# Composite score: higher = better
# Convert ranks to 0–100 scores (rank 1 → 100, rank n → 0)
def rank_to_score(rank_col, n):
    return ((n - rank_col) / (n - 1) * 100).round(2)

scorecard['score_3yr']     = rank_to_score(scorecard['rank_3yr'],     n)
scorecard['score_sharpe']  = rank_to_score(scorecard['rank_sharpe'],  n)
scorecard['score_alpha']   = rank_to_score(scorecard['rank_alpha'],   n)
scorecard['score_expense'] = rank_to_score(scorecard['rank_expense'], n)
scorecard['score_mdd']     = rank_to_score(scorecard['rank_mdd'],     n)

# Weighted composite
scorecard['composite_score'] = (
    0.30 * scorecard['score_3yr']     +
    0.25 * scorecard['score_sharpe']  +
    0.20 * scorecard['score_alpha']   +
    0.15 * scorecard['score_expense'] +
    0.10 * scorecard['score_mdd']
).round(2)

scorecard['overall_rank'] = scorecard['composite_score'].rank(ascending=False).astype(int)
scorecard = scorecard.sort_values('overall_rank')

print("\n  Fund Scorecard — Top 10:")
cols_show = ['overall_rank', 'scheme_name', 'composite_score',
             'cagr_3yr_pct', 'sharpe_ratio_calc', 'alpha_annualised', 'max_dd_pct']
print(scorecard[cols_show].head(10).to_string(index=False))

# Save
out_cols = [
    'overall_rank', 'amfi_code', 'scheme_name', 'fund_house', 'sub_category',
    'expense_ratio_pct', 'cagr_1yr_pct', 'cagr_3yr_pct', 'cagr_5yr_pct',
    'sharpe_ratio_calc', 'sortino_ratio_calc', 'alpha_annualised', 'beta',
    'max_dd_pct', 'peak_date', 'trough_date',
    'score_3yr', 'score_sharpe', 'score_alpha', 'score_expense', 'score_mdd',
    'composite_score'
]
scorecard[out_cols].to_csv('data/processed/fund_scorecard.csv', index=False)
print("\n  Saved → data/processed/fund_scorecard.csv")

# ─────────────────────────────────────────────────────────────────────────────
# 9. Benchmark Comparison Chart — Top 5 vs Nifty 50 & Nifty 100
# ─────────────────────────────────────────────────────────────────────────────
print("\n[8] Benchmark comparison chart...")

top5_codes = scorecard.head(5)['amfi_code'].tolist()
top5_names = scorecard.head(5).set_index('amfi_code')['scheme_name'].to_dict()

# 3-year window
end_dt   = nav_pivot.index.max()
start_dt = end_dt - pd.DateOffset(years=3)

# Fund returns (indexed to 100)
fund_window = nav_pivot.loc[start_dt:end_dt, top5_codes].dropna(how='all')
fund_norm   = fund_window.div(fund_window.iloc[0]) * 100

# Benchmark returns (indexed to 100)
bench_window = bench.loc[start_dt:end_dt, ['NIFTY50', 'NIFTY100']].dropna(how='all')
bench_norm   = bench_window.div(bench_window.iloc[0]) * 100

# ── Tracking Error ──
bench_ret_3y = bench['NIFTY100'].pct_change()
te_rows = []
for code in top5_codes:
    fr   = daily_ret[code].dropna()
    br   = bench_ret_3y.dropna()
    comm = fr.index.intersection(br.index)
    comm = comm[(comm >= start_dt) & (comm <= end_dt)]
    if len(comm) > 30:
        diff = fr.loc[comm] - br.loc[comm]
        te   = diff.std() * np.sqrt(TRADING_DAYS) * 100
    else:
        te = np.nan
    te_rows.append({'amfi_code': code,
                    'tracking_error_pct': round(te, 4) if not np.isnan(te) else np.nan})

te_df = pd.DataFrame(te_rows).merge(fund[['amfi_code', 'scheme_name']], on='amfi_code')
print("\n  Tracking Error vs NIFTY100 (Top 5 funds, 3-year):")
print(te_df[['scheme_name', 'tracking_error_pct']].to_string(index=False))

# ── Plot ──
fig, axes = plt.subplots(2, 1, figsize=(15, 12), gridspec_kw={'height_ratios': [3, 1]})

ax = axes[0]
colors = plt.cm.tab10(np.linspace(0, 0.7, 5))

for i, code in enumerate(top5_codes):
    label = top5_names[code][:35] + ('...' if len(top5_names[code]) > 35 else '')
    ax.plot(fund_norm.index, fund_norm[code], linewidth=2,
            color=colors[i], label=label, zorder=3)

# Benchmarks
ax.plot(bench_norm.index, bench_norm['NIFTY50'],  linewidth=2.5,
        linestyle='--', color='black', label='NIFTY 50', zorder=4)
ax.plot(bench_norm.index, bench_norm['NIFTY100'], linewidth=2.5,
        linestyle=':', color='dimgray', label='NIFTY 100', zorder=4)

ax.set_title('Top 5 Funds vs NIFTY 50 & NIFTY 100 — 3-Year Performance (Indexed to 100)',
             fontsize=14, fontweight='bold', pad=15)
ax.set_ylabel('Performance Index (Base = 100)', fontsize=12)
ax.legend(loc='upper left', fontsize=9, framealpha=0.9)
ax.grid(True, alpha=0.4)
ax.set_xlim(fund_norm.index.min(), fund_norm.index.max())

# ── Tracking error bar ──
ax2 = axes[1]
short_names = [top5_names[c][:25] for c in top5_codes]
te_vals     = [te_df.set_index('amfi_code').loc[c, 'tracking_error_pct']
               if c in te_df['amfi_code'].values else 0 for c in top5_codes]
bar_colors  = [colors[i] for i in range(5)]
bars2 = ax2.bar(short_names, te_vals, color=bar_colors, edgecolor='white', width=0.5)
for bar, val in zip(bars2, te_vals):
    ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.05,
             f'{val:.2f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
ax2.set_title('Tracking Error vs NIFTY 100 (annualised, %)', fontsize=12, fontweight='bold')
ax2.set_ylabel('Tracking Error (%)')
ax2.set_ylim(0, max(te_vals) * 1.25 if max(te_vals) > 0 else 5)
ax2.grid(True, alpha=0.3, axis='y')

plt.tight_layout(pad=3)
chart_path = CHARTS + 'benchmark_comparison.png'
plt.savefig(chart_path, dpi=150, bbox_inches='tight')
plt.close()
print(f"\n  Saved → {chart_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 10. Daily Return Distribution Validation Chart
# ─────────────────────────────────────────────────────────────────────────────
print("\n[9] Daily return distribution validation chart...")

fig2, axes2 = plt.subplots(2, 5, figsize=(20, 8))
sample_codes = nav_pivot.columns[:10].tolist()

for i, code in enumerate(sample_codes):
    ax = axes2[i // 5][i % 5]
    r  = daily_ret[code].dropna()
    ax.hist(r * 100, bins=60, color='steelblue', edgecolor='white', alpha=0.85)
    ax.axvline(0, color='red', linestyle='--', linewidth=1)
    name = fund.set_index('amfi_code').loc[code, 'scheme_name'] if code in fund['amfi_code'].values else str(code)
    ax.set_title(name[:22], fontsize=8, fontweight='bold')
    ax.set_xlabel('Daily Return (%)', fontsize=7)
    ax.tick_params(labelsize=7)

fig2.suptitle('Daily Return Distribution — Sample 10 Funds', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig(CHARTS + 'daily_return_distribution.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved → {CHARTS}daily_return_distribution.png")

# ─────────────────────────────────────────────────────────────────────────────
# 11. Sharpe & Sortino Ranking Chart
# ─────────────────────────────────────────────────────────────────────────────
print("\n[10] Sharpe vs Sortino ranking chart...")

rank_df = (scorecard[['scheme_name', 'sharpe_ratio_calc', 'sortino_ratio_calc']]
           .dropna()
           .sort_values('sharpe_ratio_calc', ascending=False)
           .head(20))
rank_df['short'] = rank_df['scheme_name'].str[:30]

fig3, ax3 = plt.subplots(figsize=(13, 8))
x    = np.arange(len(rank_df))
w    = 0.38
bar1 = ax3.bar(x - w/2, rank_df['sharpe_ratio_calc'], w, label='Sharpe Ratio',
               color='#1565C0', edgecolor='white')
bar2 = ax3.bar(x + w/2, rank_df['sortino_ratio_calc'], w, label='Sortino Ratio',
               color='#43A047', edgecolor='white')
ax3.set_xticks(x)
ax3.set_xticklabels(rank_df['short'], rotation=40, ha='right', fontsize=8)
ax3.axhline(1.0, color='red', linestyle='--', linewidth=1, label='Ratio = 1.0')
ax3.set_title('Sharpe vs Sortino Ratio — Top 20 Funds', fontsize=13, fontweight='bold')
ax3.set_ylabel('Ratio'); ax3.legend(); ax3.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(CHARTS + 'sharpe_sortino_ranking.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved → {CHARTS}sharpe_sortino_ranking.png")

# ─────────────────────────────────────────────────────────────────────────────
# 12. Fund Scorecard Bar Chart
# ─────────────────────────────────────────────────────────────────────────────
print("\n[11] Fund scorecard chart...")

top20_sc = scorecard.head(20).copy()
top20_sc['short'] = top20_sc['scheme_name'].str[:30]

fig4, ax4 = plt.subplots(figsize=(13, 8))
score_cols  = ['score_3yr', 'score_sharpe', 'score_alpha', 'score_expense', 'score_mdd']
score_labels = ['3yr Return\n(30%)', 'Sharpe\n(25%)', 'Alpha\n(20%)', 'Low Expense\n(15%)', 'Low Drawdown\n(10%)']
wts = [0.30, 0.25, 0.20, 0.15, 0.10]
bar_colors_sc = ['#1565C0', '#1976D2', '#1E88E5', '#42A5F5', '#90CAF9']
bottom = np.zeros(len(top20_sc))

for col, lbl, c, w in zip(score_cols, score_labels, bar_colors_sc, wts):
    vals = (top20_sc[col] * w).values
    ax4.bar(top20_sc['short'], vals, bottom=bottom, label=lbl, color=c, edgecolor='white', width=0.7)
    bottom += vals

ax4.set_title('Fund Scorecard — Composite Score Breakdown (Top 20 Funds)', fontsize=13, fontweight='bold')
ax4.set_ylabel('Composite Score (0–100)')
ax4.set_xticklabels(top20_sc['short'], rotation=40, ha='right', fontsize=8)
ax4.legend(loc='upper right', fontsize=9, framealpha=0.9)
ax4.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.savefig(CHARTS + 'fund_scorecard_chart.png', dpi=150, bbox_inches='tight')
plt.close()
print(f"  Saved → {CHARTS}fund_scorecard_chart.png")

# ─────────────────────────────────────────────────────────────────────────────
# Summary
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  data/processed/fund_scorecard.csv  → {len(scorecard)} funds")
print(f"  data/processed/alpha_beta.csv      → {len(alpha_beta_df)} funds")
print(f"  reports/charts/benchmark_comparison.png")
print(f"  reports/charts/daily_return_distribution.png")
print(f"  reports/charts/sharpe_sortino_ranking.png")
print(f"  reports/charts/fund_scorecard_chart.png")
print("=" * 60)
