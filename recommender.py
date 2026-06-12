"""
recommender.py — CLI Fund Recommender
======================================
Bluestock MF Analytics Capstone Project

Recommends mutual funds based on an investor's stated risk appetite.
Loads the fund scorecard and VaR/CVaR report, filters by risk grade,
and ranks eligible funds by composite score (primary) then Sharpe (secondary).

Composite score weights (0–100 scale):
    30% — 3-year CAGR rank
    25% — Sharpe Ratio rank
    20% — Alpha (annualised) rank
    15% — Low expense ratio rank
    10% — Low max drawdown rank

Risk levels
-----------
Explicit:  Low | Moderate | Moderately High | High | Very High
Aliases:   conservative → Low
           balanced     → Moderate + Moderately High
           aggressive   → High + Very High

Usage
-----
    python recommender.py                        # interactive prompt
    python recommender.py --risk Low
    python recommender.py --risk Moderate --top 5
    python recommender.py --risk aggressive
"""

import pandas as pd
import argparse
import sys

PROCESSED = 'data/processed/'

RISK_MAPPING = {
    'low'            : ['Low'],
    'moderate'       : ['Moderate'],
    'moderately high': ['Moderately High'],
    'high'           : ['High'],
    'very high'      : ['Very High'],
    # aliases
    'conservative'   : ['Low'],
    'balanced'       : ['Moderate', 'Moderately High'],
    'aggressive'     : ['High', 'Very High'],
}

def load_data():
    fund      = pd.read_csv(PROCESSED + '01_fund_master_cleaned.csv')
    scorecard = pd.read_csv(PROCESSED + 'fund_scorecard.csv')
    perf      = pd.read_csv(PROCESSED + '07_scheme_performance_cleaned.csv')
    var_cvar  = pd.read_csv(PROCESSED + 'var_cvar_report.csv')

    # Merge all metrics
    merged = (scorecard
        .merge(fund[['amfi_code', 'fund_house', 'risk_category',
                      'sub_category', 'plan', 'fund_manager',
                      'expense_ratio_pct']], on='amfi_code', how='left',
               suffixes=('', '_fund'))
        .merge(perf[['amfi_code', 'return_1yr_pct', 'return_3yr_pct',
                      'morningstar_rating', 'risk_grade']], on='amfi_code', how='left')
        .merge(var_cvar[['amfi_code', 'var_95_daily_pct', 'cvar_95_daily_pct']],
               on='amfi_code', how='left')
    )
    # Use fund master risk_category as primary (more complete)
    merged['effective_risk'] = merged['risk_category'].fillna(merged['risk_grade'])
    return merged

def recommend(risk_input: str, top_n: int = 3) -> pd.DataFrame:
    df = load_data()
    risk_key = risk_input.strip().lower()

    if risk_key not in RISK_MAPPING:
        valid = list(RISK_MAPPING.keys())
        print(f"\n  ERROR: '{risk_input}' is not a valid risk level.")
        print(f"  Valid options: {valid}")
        sys.exit(1)

    risk_grades = RISK_MAPPING[risk_key]

    # Filter by matching risk grade
    filtered = df[df['effective_risk'].isin(risk_grades)].copy()

    if filtered.empty:
        print(f"  No funds found for risk level: {risk_input}")
        return pd.DataFrame()

    # Rank by composite score (primary) then Sharpe (secondary)
    filtered = filtered.sort_values(
        ['composite_score', 'sharpe_ratio_calc'],
        ascending=[False, False]
    )

    top = filtered.head(top_n)[
        ['scheme_name', 'fund_house', 'sub_category', 'plan',
         'composite_score', 'sharpe_ratio_calc', 'sortino_ratio_calc',
         'cagr_3yr_pct', 'cagr_5yr_pct', 'alpha_annualised',
         'max_dd_pct', 'expense_ratio_pct',
         'var_95_daily_pct', 'morningstar_rating', 'fund_manager',
         'effective_risk']
    ].copy()
    top.insert(0, 'recommendation_rank', range(1, len(top) + 1))
    return top

def print_recommendation(risk_input: str, top_n: int = 3):
    top = recommend(risk_input, top_n)
    if top.empty:
        return

    print("\n" + "=" * 70)
    print(f"  FUND RECOMMENDATIONS  |  Risk Appetite: {risk_input.title()}")
    print("=" * 70)

    for _, row in top.iterrows():
        print(f"\n  Rank #{int(row['recommendation_rank'])} — {row['scheme_name']}")
        print(f"  {'Fund House':<22}: {row['fund_house']}")
        print(f"  {'Category':<22}: {row['sub_category']} ({row['plan']} Plan)")
        print(f"  {'Fund Manager':<22}: {row['fund_manager']}")
        print(f"  {'Risk Grade':<22}: {row['effective_risk']}")
        print(f"  {'Composite Score':<22}: {row['composite_score']:.1f} / 100")
        print(f"  {'Sharpe Ratio':<22}: {row['sharpe_ratio_calc']:.3f}")
        print(f"  {'Sortino Ratio':<22}: {row['sortino_ratio_calc']:.3f}")
        print(f"  {'3yr CAGR':<22}: {row['cagr_3yr_pct']:.2f}%")
        print(f"  {'5yr CAGR':<22}: {row['cagr_5yr_pct']:.2f}%")
        print(f"  {'Alpha (ann.)':<22}: {row['alpha_annualised']:.2f}%")
        print(f"  {'Max Drawdown':<22}: {row['max_dd_pct']:.2f}%")
        print(f"  {'Expense Ratio':<22}: {row['expense_ratio_pct']:.2f}%")
        print(f"  {'VaR 95% (daily)':<22}: {row['var_95_daily_pct']:.4f}%")
        stars = "★" * int(row['morningstar_rating']) if not pd.isna(row['morningstar_rating']) else "N/A"
        print(f"  {'Morningstar':<22}: {stars}")
        print(f"  {'-'*50}")

    print("\n  WHY THESE FUNDS?")
    print(f"  Filtered to '{risk_input.title()}' risk grade, then ranked by")
    print("  composite score (30% 3yr-return + 25% Sharpe + 20% Alpha +")
    print("  15% low-expense + 10% low-drawdown).\n")

def main():
    parser = argparse.ArgumentParser(
        description='Bluestock MF Fund Recommender',
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        '--risk', type=str, default=None,
        help='Risk appetite: Low / Moderate / Moderately High / High / Very High\n'
             'Aliases: conservative / balanced / aggressive'
    )
    parser.add_argument(
        '--top', type=int, default=3,
        help='Number of funds to recommend (default: 3)'
    )
    args = parser.parse_args()

    if args.risk is None:
        # Interactive mode
        print("\n  Bluestock MF Fund Recommender")
        print("  ─────────────────────────────────────────────")
        print("  Risk Levels: Low | Moderate | Moderately High | High | Very High")
        print("  Aliases    : conservative | balanced | aggressive")
        risk_input = input("\n  Enter your risk appetite: ").strip()
    else:
        risk_input = args.risk

    print_recommendation(risk_input, args.top)

if __name__ == '__main__':
    main()
