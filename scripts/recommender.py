"""
scripts/recommender.py — Fund Recommender Entry Point
======================================================
Bluestock MF Analytics Capstone Project

CLI fund recommender. Filters funds by risk appetite and ranks by
composite score (Sharpe, CAGR, Alpha, TER, Max Drawdown).

This script delegates to recommender.py at the project root.

Usage
-----
    python scripts/recommender.py
    python scripts/recommender.py --risk Low
    python scripts/recommender.py --risk Moderate --top 5
    python scripts/recommender.py --risk aggressive
"""

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from recommender import main

if __name__ == "__main__":
    main()
