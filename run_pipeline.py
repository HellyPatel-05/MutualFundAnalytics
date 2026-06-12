"""
run_pipeline.py — Master Execution Script
==========================================
Bluestock MF Analytics Capstone Project

Runs the entire analytics pipeline in sequence:
  Stage 1: Fetch live NAV data from mfapi.in
  Stage 2: EDA analysis — 15 exploratory charts
  Stage 3: Performance analytics — CAGR, Sharpe, Alpha/Beta, Scorecard
  Stage 4: Advanced analytics — VaR/CVaR, Rolling Sharpe, Cohorts, HHI

Usage:
    python run_pipeline.py                  # run all stages
    python run_pipeline.py --skip-fetch     # skip live NAV fetch (use cached data)
    python run_pipeline.py --stage eda      # run a single stage only
    python run_pipeline.py --stage perf
    python run_pipeline.py --stage advanced

Expected runtime: 3–8 minutes (Stage 1 depends on internet speed).
"""

import argparse
import importlib
import os
import sys
import time
import traceback


# ─────────────────────────────────────────────────────────────────────────────
# Stage definitions
# ─────────────────────────────────────────────────────────────────────────────
STAGES = [
    {
        "key":    "fetch",
        "label":  "Stage 1 — Live NAV Fetch",
        "module": "live_nav_fetch",
        "desc":   "Fetches real-time NAV data from mfapi.in for 6 key funds.",
    },
    {
        "key":    "eda",
        "label":  "Stage 2 — EDA Analysis",
        "module": "run_eda",
        "desc":   "Generates 15 exploratory charts into reports/charts/.",
    },
    {
        "key":    "perf",
        "label":  "Stage 3 — Performance Analytics",
        "module": "performance_analytics",
        "desc":   "Computes CAGR, Sharpe, Sortino, Alpha/Beta, Max Drawdown, Fund Scorecard.",
    },
    {
        "key":    "advanced",
        "label":  "Stage 4 — Advanced Analytics",
        "module": "advanced_analytics",
        "desc":   "Runs VaR/CVaR, Rolling Sharpe, Investor Cohort, SIP Continuity, Sector HHI.",
    },
]

# Required directories — created if missing
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "reports/charts",
]


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def banner(text: str, width: int = 65) -> None:
    """Print a formatted section banner to stdout."""
    print()
    print("=" * width)
    print(f"  {text}")
    print("=" * width)


def ensure_dirs() -> None:
    """Create required output directories if they do not exist."""
    for d in REQUIRED_DIRS:
        os.makedirs(d, exist_ok=True)


def run_stage(stage: dict) -> bool:
    """
    Dynamically import and execute a pipeline stage module.

    The function imports the module by name, then looks for a ``main()``
    function. If no ``main()`` exists the module-level code runs on import.

    Parameters
    ----------
    stage : dict
        Stage descriptor with keys: key, label, module, desc.

    Returns
    -------
    bool
        True if the stage completed without error, False otherwise.
    """
    banner(stage["label"])
    print(f"  {stage['desc']}")
    print()

    t0 = time.time()
    try:
        # Remove any cached import so code always re-executes
        if stage["module"] in sys.modules:
            del sys.modules[stage["module"]]

        mod = importlib.import_module(stage["module"])

        # If the module exposes a main() function, call it explicitly
        if hasattr(mod, "main") and callable(mod.main):
            mod.main()

        elapsed = time.time() - t0
        print(f"\n  ✓ {stage['label']} completed in {elapsed:.1f}s")
        return True

    except Exception:
        elapsed = time.time() - t0
        print(f"\n  ✗ {stage['label']} FAILED after {elapsed:.1f}s")
        print()
        traceback.print_exc()
        return False


# ─────────────────────────────────────────────────────────────────────────────
# CLI argument parsing
# ─────────────────────────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    """Parse command-line arguments for the pipeline runner."""
    parser = argparse.ArgumentParser(
        description="Bluestock MF Analytics — Master Pipeline Runner",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python run_pipeline.py                  # run all stages\n"
            "  python run_pipeline.py --skip-fetch     # skip live NAV fetch\n"
            "  python run_pipeline.py --stage eda      # EDA only\n"
            "  python run_pipeline.py --stage perf     # Performance analytics only\n"
            "  python run_pipeline.py --stage advanced # Advanced analytics only\n"
        ),
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        default=False,
        help="Skip Stage 1 (live NAV fetch). Use cached CSVs from data/raw/.",
    )
    parser.add_argument(
        "--stage",
        type=str,
        default=None,
        choices=["fetch", "eda", "perf", "advanced"],
        help="Run only a specific stage instead of the full pipeline.",
    )
    return parser.parse_args()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main() -> None:
    """Entry point — parse arguments, validate environment, run stages."""
    args = parse_args()

    banner("Bluestock MF Analytics — Master Pipeline", width=65)
    print("  Project : Bluestock Fintech MF Capstone")
    print("  Version : v1.0")
    print()

    # Ensure output directories exist
    ensure_dirs()

    # Determine which stages to run
    if args.stage:
        # Single-stage mode
        stages_to_run = [s for s in STAGES if s["key"] == args.stage]
    else:
        # Full pipeline mode
        stages_to_run = STAGES.copy()
        if args.skip_fetch:
            stages_to_run = [s for s in stages_to_run if s["key"] != "fetch"]
            print("  --skip-fetch: Stage 1 (NAV fetch) will be skipped.")

    if not stages_to_run:
        print("  ERROR: No stages selected. Check --stage argument.")
        sys.exit(1)

    print(f"  Stages to run: {[s['key'] for s in stages_to_run]}")

    # Execute stages
    wall_t0 = time.time()
    results = {}

    for stage in stages_to_run:
        success = run_stage(stage)
        results[stage["key"]] = success
        if not success:
            print(f"\n  Pipeline halted at {stage['label']}.")
            print("  Fix the error above and re-run, or skip this stage with --stage.")
            break

    # Summary
    banner("Pipeline Summary", width=65)
    total_elapsed = time.time() - wall_t0
    all_ok = True

    for key, success in results.items():
        label = next(s["label"] for s in STAGES if s["key"] == key)
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {status}  {label}")
        if not success:
            all_ok = False

    skipped = [s["label"] for s in stages_to_run if s["key"] not in results]
    for label in skipped:
        print(f"  ⊘ SKIPPED  {label}")

    print()
    print(f"  Total time : {total_elapsed:.1f}s")
    print(f"  Status     : {'ALL STAGES PASSED ✓' if all_ok else 'PIPELINE HAD ERRORS ✗'}")
    print()

    if all_ok:
        print("  Outputs ready:")
        print("    reports/charts/         — 30 PNG charts")
        print("    data/processed/         — cleaned CSVs + analytics outputs")
        print("    bluestock_mf.db         — SQLite database")
        print()
        print("  Next steps:")
        print("    • Open Power BI Desktop and follow dashboard/PowerBI_Build_Guide.md")
        print("    • Try the fund recommender: python recommender.py --risk Moderate")

    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
