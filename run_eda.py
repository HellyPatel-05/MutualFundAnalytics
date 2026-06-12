"""
run_eda.py — Exploratory Data Analysis
========================================
Bluestock MF Analytics Capstone Project

Generates 15 publication-quality PNG charts covering:

    1.  NAV Trend           — all 40 schemes indexed to 100 (2022–2026)
    2.  AUM Grouped Bar     — fund house AUM per year, SBI highlighted
    3.  SIP Inflow Series   — monthly inflows with ATH annotation
    4.  Category Heatmap    — monthly net inflows by fund category
    5a. Age Group Pie       — investor age distribution
    5b. SIP Boxplot (Age)   — SIP amount distribution by age group
    5c. Gender Split        — investor gender donut chart
    6a. SIP by State        — top 12 states by SIP value
    6b. T30 vs B30          — city-tier investment split
    7.  Folio Count Growth  — total, equity, debt, hybrid lines (2022–2025)
    8.  Correlation Matrix  — daily return correlations, 10 selected funds
    9.  Sector Allocation   — aggregate sector weights (equity funds)
    10. Return vs Drawdown  — 5-year return vs max drawdown scatter
    11. Expense Ratio       — distribution by sub-category (boxplot)
    12. Top 10 AUM          — bar chart, top funds by assets
    13. Annual SIP Bar      — yearly SIP inflow totals
    14. Sharpe Ratio        — top 15 equity funds
    15. Transaction Types   — count split and value by transaction type

All charts are saved to ``reports/charts/`` as high-resolution PNGs.

Usage
-----
    python run_eda.py
"""
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings, os, glob
warnings.filterwarnings('ignore')

RAW       = 'data/raw/'
PROCESSED = 'data/processed/'
CHARTS    = 'reports/charts/'
os.makedirs(CHARTS, exist_ok=True)

sns.set_theme(style='whitegrid', palette='muted', font_scale=1.1)
PLOTLY_TEMPLATE = 'plotly_white'

# ── Load ──────────────────────────────────────────────────────────────────────
nav        = pd.read_csv(PROCESSED + '02_nav_history_cleaned.csv', parse_dates=['date'])
fund       = pd.read_csv(PROCESSED + '01_fund_master_cleaned.csv', parse_dates=['launch_date'])
aum        = pd.read_csv(PROCESSED + '03_aum_by_fund_house_cleaned.csv', parse_dates=['date'])
sip        = pd.read_csv(PROCESSED + '04_monthly_sip_inflows_cleaned.csv', parse_dates=['month'])
cat_inflow = pd.read_csv(RAW + '05_category_inflows.csv', parse_dates=['month'])
folio      = pd.read_csv(RAW + '06_industry_folio_count.csv', parse_dates=['month'])
perf       = pd.read_csv(PROCESSED + '07_scheme_performance_cleaned.csv')
txn        = pd.read_csv(PROCESSED + '08_investor_transactions_cleaned.csv', parse_dates=['transaction_date'])
holdings   = pd.read_csv(RAW + '09_portfolio_holdings.csv')

equity_codes = fund[fund['category'] == 'Equity']['amfi_code'].tolist()
nav_trading  = nav[nav['is_trading_day'] == 1].copy()
perf_fund    = perf.merge(fund[['amfi_code', 'sub_category']], on='amfi_code', how='left')

# ── Chart 1: NAV Trend ────────────────────────────────────────────────────────
nav_pivot = nav_trading.pivot_table(index='date', columns='amfi_code', values='nav')
nav_norm  = nav_pivot.div(nav_pivot.iloc[0]) * 100
x_dates   = nav_norm.index.strftime('%Y-%m-%d').tolist()
fund_map  = fund.set_index('amfi_code')['scheme_name'].to_dict()

fig = go.Figure()
for col in nav_norm.columns:
    fname = fund_map.get(col, str(col))
    fig.add_trace(go.Scatter(
        x=x_dates, y=nav_norm[col].tolist(),
        mode='lines', name=str(col),
        line=dict(width=1), opacity=0.5,
        hovertemplate=f'<b>{fname[:40]}</b><br>%{{x}}<br>Idx: %{{y:.1f}}<extra></extra>'
    ))

fig.add_vrect(x0='2023-01-01', x1='2023-12-31', fillcolor='green', opacity=0.08,
    line_width=0, annotation_text='2023 Bull Run', annotation_position='top left',
    annotation_font=dict(color='green', size=12))
fig.add_vrect(x0='2024-09-01', x1='2024-12-31', fillcolor='red', opacity=0.08,
    line_width=0, annotation_text='2024 Correction', annotation_position='top left',
    annotation_font=dict(color='red', size=12))
fig.update_layout(title='NAV Trend - All 40 Schemes (Indexed to 100, 2022-2026)',
    xaxis_title='Date', yaxis_title='NAV Index (Base=100)',
    template=PLOTLY_TEMPLATE, height=550, showlegend=False, hovermode='x unified')
fig.write_image(CHARTS + '01_nav_trend_all_schemes.png', width=1400, height=550, scale=2)

# ── Chart 2: AUM Grouped Bar ──────────────────────────────────────────────────
print("Chart 2: AUM grouped bar...")
aum['year'] = aum['date'].dt.year
aum_yearly  = aum.groupby(['year', 'fund_house'])['aum_crore'].max().reset_index()
aum_yearly['aum_lakh_cr'] = aum_yearly['aum_crore'] / 1e5
pivot = aum_yearly.pivot(index='fund_house', columns='year', values='aum_lakh_cr').fillna(0)

fig2, ax2 = plt.subplots(figsize=(16, 7))
pivot.plot(kind='bar', ax=ax2, colormap='Blues', width=0.75, edgecolor='white')
fund_houses = pivot.index.tolist()
sbi_idx     = fund_houses.index('SBI Mutual Fund')
for i, bar in enumerate(ax2.patches):
    if i % len(fund_houses) == sbi_idx:
        bar.set_facecolor('crimson'); bar.set_alpha(0.9)

sbi_2025 = aum_yearly[(aum_yearly['fund_house'] == 'SBI Mutual Fund') & (aum_yearly['year'] == 2025)]
if not sbi_2025.empty:
    ax2.annotate('Rs.12.5L Cr', xy=(sbi_idx, sbi_2025['aum_lakh_cr'].values[0]),
        xytext=(sbi_idx + 2, sbi_2025['aum_lakh_cr'].values[0] + 0.5),
        arrowprops=dict(arrowstyle='->', color='crimson'),
        fontsize=11, color='crimson', fontweight='bold')

ax2.set_title('AUM by Fund House per Year (Rs. Lakh Crore) - SBI Dominance Highlighted',
    fontsize=14, fontweight='bold')
ax2.set_xlabel('Fund House'); ax2.set_ylabel('AUM (Rs. Lakh Crore)')
ax2.set_xticklabels(ax2.get_xticklabels(), rotation=30, ha='right')
ax2.legend(title='Year', bbox_to_anchor=(1.01, 1))
plt.tight_layout()
plt.savefig(CHARTS + '02_aum_grouped_bar.png', dpi=150, bbox_inches='tight')
plt.close()

# ── Chart 3: SIP Inflow Time-Series ──────────────────────────────────────────
print("Chart 3: SIP inflow timeseries...")
sip_x   = sip['month'].dt.strftime('%Y-%m-%d').tolist()
sip_y   = sip['sip_inflow_crore'].tolist()
ath_idx = int(sip['sip_inflow_crore'].idxmax())
ath_x   = sip.loc[ath_idx, 'month'].strftime('%Y-%m-%d')
ath_y   = float(sip.loc[ath_idx, 'sip_inflow_crore'])

fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=sip_x, y=sip_y, mode='lines+markers', name='SIP Inflow',
    line=dict(color='#2196F3', width=2.5), marker=dict(size=4),
    fill='tozeroy', fillcolor='rgba(33,150,243,0.08)'))
fig3.add_annotation(x=ath_x, y=ath_y, text=f'<b>ATH Rs.{ath_y:,.0f} Cr</b><br>Dec 2025',
    showarrow=True, arrowhead=2, arrowcolor='red',
    font=dict(color='red', size=12), ax=40, ay=-50)
fig3.add_hline(y=20000, line_dash='dot', line_color='orange',
    annotation_text='Rs.20,000 Cr milestone', annotation_position='bottom right')
fig3.update_layout(title='Monthly SIP Inflows (Jan 2022 - Dec 2025)',
    xaxis_title='Month', yaxis_title='SIP Inflow (Rs. Crore)',
    template=PLOTLY_TEMPLATE, height=480)
fig3.write_image(CHARTS + '03_sip_inflow_timeseries.png', width=1400, height=480, scale=2)

# ── Chart 4: Category Inflow Heatmap ─────────────────────────────────────────
print("Chart 4: Category heatmap...")
cat_inflow['month_str'] = cat_inflow['month'].dt.strftime('%Y-%m')
heat_pivot = cat_inflow.pivot_table(index='category', columns='month_str',
    values='net_inflow_crore', aggfunc='sum')

fig4, ax4 = plt.subplots(figsize=(18, 7))
sns.heatmap(heat_pivot, cmap='YlOrRd', annot=False, linewidths=0.3, linecolor='white',
    ax=ax4, cbar_kws={'label': 'Net Inflow (Rs. Crore)'})
ax4.set_title('Category Inflow Heatmap - Monthly Net Inflows (2024-2025)', fontsize=14, fontweight='bold')
ax4.set_xlabel('Month'); ax4.set_ylabel('Fund Category')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.savefig(CHARTS + '04_category_inflow_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()

# ── Chart 5: Investor Demographics ───────────────────────────────────────────
print("Chart 5: Demographics...")
age_counts = txn['age_group'].value_counts().reset_index()
age_counts.columns = ['age_group', 'count']
age_order = ['18-25', '26-35', '36-45', '46-55', '56+']
age_counts['age_group'] = pd.Categorical(age_counts['age_group'], categories=age_order, ordered=True)
age_counts = age_counts.sort_values('age_group')

fig5a = px.pie(age_counts, values='count', names='age_group',
    title='Investor Age Group Distribution',
    color_discrete_sequence=px.colors.sequential.Blues_r,
    template=PLOTLY_TEMPLATE, hole=0.35)
fig5a.update_traces(textposition='outside', textinfo='percent+label')
fig5a.write_image(CHARTS + '05a_age_group_pie.png', width=700, height=500, scale=2)

sip_txn = txn[txn['transaction_type'] == 'SIP']
fig5b, ax5b = plt.subplots(figsize=(10, 5))
sns.boxplot(data=sip_txn[sip_txn['age_group'].isin(age_order)],
    x='age_group', y='amount_inr', order=age_order,
    palette='Blues', showfliers=False, ax=ax5b)
ax5b.set_title('SIP Amount Distribution by Age Group', fontsize=13, fontweight='bold')
ax5b.set_xlabel('Age Group'); ax5b.set_ylabel('SIP Amount (Rs.)')
plt.tight_layout()
plt.savefig(CHARTS + '05b_sip_amount_boxplot_age.png', dpi=150, bbox_inches='tight')
plt.close()

gender_counts = txn['gender'].value_counts().reset_index()
gender_counts.columns = ['gender', 'count']
fig5c = px.pie(gender_counts, values='count', names='gender',
    title='Investor Gender Split',
    color_discrete_map={'Male': '#2196F3', 'Female': '#E91E63'},
    template=PLOTLY_TEMPLATE, hole=0.4)
fig5c.update_traces(textposition='outside', textinfo='percent+label')
fig5c.write_image(CHARTS + '05c_gender_split_pie.png', width=600, height=450, scale=2)

# ── Chart 6: Geographic ───────────────────────────────────────────────────────
print("Chart 6: Geographic...")
state_sip = (sip_txn.groupby('state')['amount_inr']
    .sum().sort_values(ascending=False).head(12).reset_index())
state_sip['amount_cr'] = state_sip['amount_inr'] / 1e7

fig6a, ax6a = plt.subplots(figsize=(10, 7))
colors6 = ['#1565C0' if s in ['Maharashtra', 'Delhi'] else '#90CAF9' for s in state_sip['state']]
bars6 = ax6a.barh(state_sip['state'][::-1], state_sip['amount_cr'][::-1],
    color=colors6[::-1], edgecolor='white')
ax6a.set_title('Total SIP Investment by State (Top 12)', fontsize=13, fontweight='bold')
ax6a.set_xlabel('Total SIP Amount (Rs. Crore)')
for bar, val in zip(bars6, state_sip['amount_cr'][::-1]):
    ax6a.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
        f'Rs.{val:.0f} Cr', va='center', fontsize=9)
plt.tight_layout()
plt.savefig(CHARTS + '06a_sip_by_state_bar.png', dpi=150, bbox_inches='tight')
plt.close()

tier_counts = txn['city_tier'].value_counts().reset_index()
tier_counts.columns = ['tier', 'count']
fig6b = px.pie(tier_counts, values='count', names='tier',
    title='T30 vs B30 City Tier Split',
    color_discrete_map={'T30': '#1565C0', 'B30': '#90CAF9'},
    template=PLOTLY_TEMPLATE, hole=0.4)
fig6b.update_traces(textposition='outside', textinfo='percent+label')
fig6b.write_image(CHARTS + '06b_t30_b30_pie.png', width=600, height=450, scale=2)

# ── Chart 7: Folio Count Growth ───────────────────────────────────────────────
print("Chart 7: Folio growth...")
fig7 = go.Figure()
for col, name, color in [
    ('total_folios_crore',  'Total',  '#1565C0'),
    ('equity_folios_crore', 'Equity', '#43A047'),
    ('debt_folios_crore',   'Debt',   '#FB8C00'),
    ('hybrid_folios_crore', 'Hybrid', '#8E24AA'),
]:
    fig7.add_trace(go.Scatter(
        x=folio['month'].dt.strftime('%Y-%m-%d').tolist(),
        y=folio[col].tolist(),
        mode='lines+markers', name=name, line=dict(color=color, width=2.5)
    ))
for dt, val, label in [('2023-01-01', 14.81, '15 Cr'), ('2024-01-01', 17.78, '18 Cr'), ('2025-12-01', 26.12, '26 Cr ATH')]:
    fig7.add_annotation(x=dt, y=val, text=f'<b>{label}</b>',
        showarrow=True, arrowhead=2, arrowcolor='#1565C0',
        font=dict(size=11, color='#1565C0'), ax=30, ay=-35)
fig7.update_layout(title='Industry Folio Count Growth (Jan 2022 - Dec 2025)',
    xaxis_title='Month', yaxis_title='Folios (Crore)',
    template=PLOTLY_TEMPLATE, height=480)
fig7.write_image(CHARTS + '07_folio_count_growth.png', width=1400, height=480, scale=2)

# ── Chart 8: NAV Return Correlation Matrix ────────────────────────────────────
print("Chart 8: Correlation matrix...")
selected = [119551, 119552, 120503, 120504, 100016, 125497, 118632, 119092, 120841, 148567]
labels   = ['SBI BC Reg', 'SBI BC Dir', 'ICICI BC Reg', 'ICICI BC Dir',
            'HDFC T100 Reg', 'HDFC T100 Dir', 'Nippon LC', 'Axis BC', 'Kotak BC', 'Mirae LC']
nav_sel  = nav_trading[nav_trading['amfi_code'].isin(selected)].pivot_table(
    index='date', columns='amfi_code', values='nav')
returns  = nav_sel.pct_change().dropna()
returns.columns = labels
corr     = returns.corr()

fig8, ax8 = plt.subplots(figsize=(11, 9))
mask = np.triu(np.ones_like(corr, dtype=bool))
sns.heatmap(corr, annot=True, fmt='.2f', cmap='RdYlGn', vmin=0.5, vmax=1.0,
    mask=mask, linewidths=0.5, ax=ax8, square=True,
    cbar_kws={'shrink': 0.8, 'label': 'Pearson Correlation'})
ax8.set_title('NAV Daily Return Correlation Matrix - 10 Selected Funds', fontsize=13, fontweight='bold')
plt.xticks(rotation=35, ha='right'); plt.yticks(rotation=0)
plt.tight_layout()
plt.savefig(CHARTS + '08_nav_return_correlation.png', dpi=150, bbox_inches='tight')
plt.close()

# ── Chart 9: Sector Allocation Donut ─────────────────────────────────────────
print("Chart 9: Sector donut...")
eq_holdings = holdings[holdings['amfi_code'].isin(equity_codes)]
sector_wt   = eq_holdings.groupby('sector')['weight_pct'].sum().sort_values(ascending=False)
sector_pct  = (sector_wt / sector_wt.sum() * 100).reset_index()
sector_pct.columns = ['sector', 'pct']
threshold   = 3.0
main        = sector_pct[sector_pct['pct'] >= threshold].copy()
others_val  = sector_pct[sector_pct['pct'] < threshold]['pct'].sum()
if others_val > 0:
    main = pd.concat([main, pd.DataFrame({'sector': ['Others'], 'pct': [others_val]})], ignore_index=True)

fig9 = px.pie(main, values='pct', names='sector',
    title='Aggregate Sector Allocation - All Equity Funds',
    template=PLOTLY_TEMPLATE, hole=0.45,
    color_discrete_sequence=px.colors.qualitative.Set2)
fig9.update_traces(textposition='outside', textinfo='percent+label')
fig9.update_layout(height=520, showlegend=True)
fig9.write_image(CHARTS + '09_sector_allocation_donut.png', width=900, height=520, scale=2)

# ── Chart 10: Return vs Drawdown ──────────────────────────────────────────────
print("Chart 10: Return vs drawdown...")
perf_eq = perf_fund[perf_fund['amfi_code'].isin(equity_codes)]
fig10   = px.scatter(perf_eq, x='max_drawdown_pct', y='return_5yr_pct',
    color='sub_category', size='aum_crore',
    hover_data=['scheme_name', 'expense_ratio_pct'],
    title='5-Year Return vs Max Drawdown by Sub-Category',
    labels={'max_drawdown_pct': 'Max Drawdown (%)', 'return_5yr_pct': '5-Year Return (%)'},
    template=PLOTLY_TEMPLATE, height=500)
fig10.update_traces(marker=dict(opacity=0.8, line=dict(width=1, color='white')))
fig10.write_image(CHARTS + '10_return_vs_drawdown.png', width=1100, height=500, scale=2)

# ── Chart 11: Expense Ratio Distribution ─────────────────────────────────────
print("Chart 11: Expense ratio boxplot...")
perf_m = perf.merge(fund[['amfi_code', 'sub_category']], on='amfi_code', how='left')
order11 = perf_m.groupby('sub_category')['expense_ratio_pct'].median().sort_values().index
fig11, ax11 = plt.subplots(figsize=(11, 5))
sns.boxplot(data=perf_m, x='sub_category', y='expense_ratio_pct',
    order=order11, palette='coolwarm', showfliers=True, ax=ax11)
ax11.axhline(1.0, color='orange', linestyle='--', label='1% threshold')
ax11.set_title('Expense Ratio Distribution by Sub-Category', fontsize=13, fontweight='bold')
ax11.set_xlabel('Sub-Category'); ax11.set_ylabel('Expense Ratio (%)')
plt.xticks(rotation=30, ha='right'); plt.legend()
plt.tight_layout()
plt.savefig(CHARTS + '11_expense_ratio_distribution.png', dpi=150, bbox_inches='tight')
plt.close()

# ── Chart 12: Top 10 Funds by AUM ────────────────────────────────────────────
print("Chart 12: Top 10 AUM bar...")
top10_aum = perf_fund.nlargest(10, 'aum_crore')[['scheme_name', 'aum_crore', 'sub_category']].copy()
top10_aum['aum_cr_k'] = top10_aum['aum_crore'] / 1000
top10_aum['short']    = top10_aum['scheme_name'].str[:35]
fig12, ax12 = plt.subplots(figsize=(11, 6))
colors12 = sns.color_palette('Blues_d', len(top10_aum))
ax12.barh(top10_aum['short'].tolist()[::-1], top10_aum['aum_cr_k'].tolist()[::-1],
    color=colors12, edgecolor='white')
for i, val in enumerate(top10_aum['aum_cr_k'].tolist()[::-1]):
    ax12.text(val + 100, i, f'Rs.{val:.0f}K Cr', va='center', fontsize=9)
ax12.set_title('Top 10 Funds by AUM (Rs. Thousand Crore)', fontsize=13, fontweight='bold')
ax12.set_xlabel('AUM (Rs. Thousand Crore)')
plt.tight_layout()
plt.savefig(CHARTS + '12_top10_aum.png', dpi=150, bbox_inches='tight')
plt.close()

# ── Chart 13: Annual SIP Bar ──────────────────────────────────────────────────
print("Chart 13: Annual SIP bar...")
sip['year'] = sip['month'].dt.year
sip_annual  = sip.groupby('year')['sip_inflow_crore'].sum().reset_index()
fig13 = px.bar(sip_annual, x='year', y='sip_inflow_crore',
    title='Annual Total SIP Inflows (Rs. Crore)',
    text='sip_inflow_crore', color='sip_inflow_crore',
    color_continuous_scale='Blues', template=PLOTLY_TEMPLATE)
fig13.update_traces(texttemplate='Rs.%{text:,.0f}', textposition='outside')
fig13.update_layout(height=430, coloraxis_showscale=False)
fig13.write_image(CHARTS + '13_annual_sip_bar.png', width=900, height=430, scale=2)

# ── Chart 14: Top 15 Sharpe Ratio ────────────────────────────────────────────
print("Chart 14: Sharpe ratio bar...")
top15_sharpe = perf_fund[perf_fund['amfi_code'].isin(equity_codes)]\
    .nlargest(15, 'sharpe_ratio')[['scheme_name', 'sharpe_ratio', 'sub_category']].copy()
top15_sharpe['short'] = top15_sharpe['scheme_name'].str[:35]
fig14, ax14 = plt.subplots(figsize=(11, 6))
pal14 = sns.color_palette('RdYlGn', len(top15_sharpe))
ax14.barh(top15_sharpe['short'].tolist()[::-1], top15_sharpe['sharpe_ratio'].tolist()[::-1],
    color=pal14, edgecolor='white')
ax14.axvline(1.0, color='red', linestyle='--', label='Sharpe = 1.0')
ax14.set_title('Top 15 Equity Funds by Sharpe Ratio', fontsize=13, fontweight='bold')
ax14.set_xlabel('Sharpe Ratio')
plt.legend(); plt.tight_layout()
plt.savefig(CHARTS + '14_sharpe_ratio_top15.png', dpi=150, bbox_inches='tight')
plt.close()

# ── Chart 15: Transaction Type Analysis ──────────────────────────────────────
print("Chart 15: Transaction type analysis...")
txn_count = txn['transaction_type'].value_counts().reset_index()
txn_count.columns = ['type', 'count']
txn_val = txn.groupby('transaction_type')['amount_inr'].sum().reset_index()
txn_val.columns = ['type', 'total_inr']
txn_val['total_cr'] = txn_val['total_inr'] / 1e7
type_colors = ['#1565C0', '#43A047', '#E53935']

fig15 = make_subplots(rows=1, cols=2,
    specs=[[{'type': 'pie'}, {'type': 'bar'}]],
    subplot_titles=['Transaction Count Split', 'Total Value by Type (Rs. Crore)'])
fig15.add_trace(go.Pie(labels=txn_count['type'].tolist(), values=txn_count['count'].tolist(),
    hole=0.4, marker_colors=type_colors), row=1, col=1)
fig15.add_trace(go.Bar(x=txn_val['type'].tolist(), y=txn_val['total_cr'].tolist(),
    marker_color=type_colors,
    text=[f'Rs.{v:,.0f}' for v in txn_val['total_cr'].tolist()],
    textposition='outside'), row=1, col=2)
fig15.update_layout(title='Transaction Type Analysis', template=PLOTLY_TEMPLATE,
    height=440, showlegend=False)
fig15.write_image(CHARTS + '15_transaction_type_analysis.png', width=1200, height=440, scale=2)

# ── Summary ───────────────────────────────────────────────────────────────────
charts = sorted(glob.glob(CHARTS + '*.png'))
print(f'\nAll done. {len(charts)} PNG charts saved to {CHARTS}')
for c in charts:
    print(f'  {os.path.basename(c)}')
