"""
live_nav_fetch.py — Live NAV Fetch from AMFI API
=================================================
Bluestock MF Analytics Capstone Project

Fetches current historical NAV data for 6 key mutual fund schemes
from the public mfapi.in REST API and saves each fund's data as a
CSV file in data/raw/.

Funds fetched
-------------
- HDFC Top 100 Direct     (AMFI code: 125497)
- SBI Bluechip Regular    (AMFI code: 119551)
- ICICI Bluechip Regular  (AMFI code: 120503)
- Nippon Large Cap Regular(AMFI code: 118632)
- Axis Bluechip Regular   (AMFI code: 119092)
- Kotak Bluechip Regular  (AMFI code: 120841)

API endpoint: https://api.mfapi.in/mf/{amfi_code}

Usage
-----
    python live_nav_fetch.py

Output
------
    data/raw/hdfc_top100_nav.csv
    data/raw/sbi_bluechip_nav.csv
    data/raw/icici_bluechip_nav.csv
    data/raw/nippon_large_cap_nav.csv
    data/raw/axis_bluechip_nav.csv
    data/raw/kotak_bluechip_nav.csv
"""

import os
import time

import pandas as pd
import requests

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────
RAW_DIR = "data/raw/"

FUNDS = {
    "hdfc_top100_nav":      125497,
    "sbi_bluechip_nav":     119551,
    "icici_bluechip_nav":   120503,
    "nippon_large_cap_nav": 118632,
    "axis_bluechip_nav":    119092,
    "kotak_bluechip_nav":   120841,
}

API_BASE_URL = "https://api.mfapi.in/mf/{amfi_code}"
REQUEST_TIMEOUT_SECONDS = 15
RETRY_DELAY_SECONDS = 2


# ─────────────────────────────────────────────────────────────────────────────
# Core fetch function
# ─────────────────────────────────────────────────────────────────────────────
def fetch_nav(amfi_code: int, retries: int = 3) -> pd.DataFrame:
    """
    Fetch historical NAV data for a single fund from mfapi.in.

    Parameters
    ----------
    amfi_code : int
        The AMFI registration number of the mutual fund scheme.
    retries : int, optional
        Number of retry attempts on network failure (default: 3).

    Returns
    -------
    pd.DataFrame
        DataFrame with columns ``date`` (str) and ``nav`` (float).

    Raises
    ------
    requests.RequestException
        If all retry attempts fail.
    ValueError
        If the API response does not contain a ``data`` key.
    """
    url = API_BASE_URL.format(amfi_code=amfi_code)

    for attempt in range(1, retries + 1):
        try:
            response = requests.get(url, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            payload = response.json()

            if "data" not in payload:
                raise ValueError(f"API response missing 'data' key for AMFI {amfi_code}")

            df = pd.DataFrame(payload["data"])
            df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
            df = df.dropna(subset=["nav"])
            return df

        except requests.RequestException as exc:
            if attempt < retries:
                time.sleep(RETRY_DELAY_SECONDS)
            else:
                raise exc


def save_nav(name: str, amfi_code: int, output_dir: str) -> int:
    """
    Fetch and save NAV data for one fund to CSV.

    Parameters
    ----------
    name : str
        Output file stem (e.g. ``"sbi_bluechip_nav"``).
    amfi_code : int
        AMFI registration number.
    output_dir : str
        Directory path where the CSV will be written.

    Returns
    -------
    int
        Number of rows written to the CSV.
    """
    df = fetch_nav(amfi_code)
    output_path = os.path.join(output_dir, f"{name}.csv")
    df.to_csv(output_path, index=False)
    return len(df)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    """Fetch NAV data for all configured funds and save to data/raw/."""
    os.makedirs(RAW_DIR, exist_ok=True)

    print("Live NAV Fetch — mfapi.in")
    print("-" * 40)

    total_rows = 0
    failed = []

    for name, amfi_code in FUNDS.items():
        try:
            rows = save_nav(name, amfi_code, RAW_DIR)
            total_rows += rows
            print(f"  Saved: {name}.csv  ({rows} rows)")
        except Exception as exc:
            failed.append(name)
            print(f"  FAILED: {name} — {exc}")

    print()
    print(f"  Total rows fetched : {total_rows:,}")
    print(f"  Files saved        : {len(FUNDS) - len(failed)} / {len(FUNDS)}")

    if failed:
        print(f"  Failed             : {failed}")


if __name__ == "__main__":
    main()
