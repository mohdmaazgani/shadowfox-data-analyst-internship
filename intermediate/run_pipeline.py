#!/usr/bin/env python3
"""Run the full analysis pipeline end to end, in order.

    python run_pipeline.py

Steps:
    1. src/clean.py    - clean the raw data into sales/returns/non-product tables
    2. src/analysis.py - compute every metric and table used in the report
    3. src/charts.py   - build all charts and the executive dashboard
    4. src/report.py   - assemble the final PDF report

Each step reads the previous step's saved output from disk, so any step can
also be re-run individually with `python src/<step>.py`.
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
STEPS = ["clean.py", "analysis.py", "charts.py", "report.py"]


def main():
    for step in STEPS:
        print(f"\n{'=' * 70}\n>>> Running src/{step}\n{'=' * 70}")
        t0 = time.time()
        result = subprocess.run([sys.executable, str(ROOT / "src" / step)], cwd=ROOT / "src")
        if result.returncode != 0:
            print(f"\nFAILED at src/{step} (exit code {result.returncode}). Stopping.")
            sys.exit(result.returncode)
        print(f"--- src/{step} finished in {time.time() - t0:.1f}s")
    print("\nPipeline complete. See reports/, outputs/, and dashboard/ for results.")


if __name__ == "__main__":
    main()
