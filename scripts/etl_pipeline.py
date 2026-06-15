"""
scripts/etl_pipeline.py — ETL Pipeline Entry Point
====================================================
Bluestock MF Analytics Capstone Project

Master ETL pipeline script. Runs all four stages:
  Stage 1: Live NAV fetch from mfapi.in
  Stage 2: EDA analysis — 15 exploratory charts
  Stage 3: Performance analytics — CAGR, Sharpe, Alpha, Scorecard
  Stage 4: Advanced analytics — VaR, Cohorts, HHI, Rolling Sharpe

This script delegates to run_pipeline.py at the project root,
which handles stage orchestration, error handling, and summary output.

Usage
-----
    python scripts/etl_pipeline.py
    python scripts/etl_pipeline.py --skip-fetch
    python scripts/etl_pipeline.py --stage eda
"""

import sys
import os

# Add project root to path so run_pipeline can be imported
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)   # ensure relative paths (data/, reports/) resolve correctly

from run_pipeline import main

if __name__ == "__main__":
    main()
