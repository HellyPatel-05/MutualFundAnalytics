"""
scripts/live_nav_fetch.py — Live NAV Fetch Entry Point
=======================================================
Bluestock MF Analytics Capstone Project

Fetches current historical NAV data for 6 key mutual fund schemes
from the public mfapi.in REST API and saves each as a CSV in data/raw/.

This script delegates to live_nav_fetch.py at the project root.

Usage
-----
    python scripts/live_nav_fetch.py
"""

import sys
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
os.chdir(ROOT)

from live_nav_fetch import main

if __name__ == "__main__":
    main()
