"""
scripts/compute_metrics.py — Performance Metrics Computation
=============================================================
Bluestock MF Analytics Capstone Project

Computes all quantitative performance metrics for 40 fund schemes:
  - CAGR (1yr, 3yr, 5yr)
  - Sharpe Ratio  : (Rp - Rf) / sigma_p * sqrt(252), Rf = 6.5%
  - Sortino Ratio : uses downside standard deviation only
  - Alpha & Beta  : OLS regression vs NIFTY 100
  - Maximum Drawdown
  - Fund Scorecard (composite 0-100)
  - Tracking Error vs benchmark

Also runs advanced analytics:
  - Historical VaR (95%) and CVaR
  - Rolling 90-day Sharpe
  - Investor cohort analysis
  - SIP continuity analysis
  - Sector HHI concentration

Outputs: fund_scorecard.csv, alpha_beta.csv, var_cvar_report.csv, charts.

This script delegates to performance_analytics.py and advanced_analytics.py
at the project root.

Usage
-----
    python scripts/compute_metrics.py
"""

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

import importlib

print("=" * 60)
print("compute_metrics.py — Performance + Advanced Analytics")
print("=" * 60)

for module_name in ["performance_analytics", "advanced_analytics"]:
    print(f"\nRunning {module_name}...")
    mod = importlib.import_module(module_name)
    if hasattr(mod, "main"):
        mod.main()
