"""OPTIONAL step: re-download the raw dataset.

The compressed raw file is already committed to the repo
(data/raw/online_retail_raw.csv.gz), so you only need this script if you want
to rebuild it from the public source.

Source
------
UCI Machine Learning Repository - "Online Retail" (Dr Daqing Chen, London South
Bank University), licence CC BY 4.0.
https://archive.ics.uci.edu/dataset/352/online-retail

This script fetches a public GitHub mirror of the same 541,909-row dataset
(the `onlineretail` R package data file) and converts it to a CSV.

Usage:  python src/00_download_data.py
Needs:  pip install pyreadr
"""
import tempfile
import urllib.request
from pathlib import Path

import pandas as pd

from config import DATA_RAW, DATA_URL, RAW_FILE


def main() -> None:
    try:
        import pyreadr  # noqa: WPS433 - optional dependency
    except ImportError as exc:  # pragma: no cover
        raise SystemExit("Please run: pip install pyreadr") from exc

    DATA_RAW.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        rda_path = Path(tmp) / "onlineretail.rda"
        print(f"Downloading {DATA_URL} ...")
        urllib.request.urlretrieve(DATA_URL, rda_path)
        df = next(iter(pyreadr.read_r(str(rda_path)).values())).copy()

    # Light type normalisation only - no values are changed.
    df["Quantity"] = df["Quantity"].astype("int64")
    df["CustomerID"] = df["CustomerID"].astype("Int64")
    df.to_csv(RAW_FILE, index=False, compression="gzip")
    print(f"Saved {len(df):,} rows -> {RAW_FILE}")


if __name__ == "__main__":
    main()
