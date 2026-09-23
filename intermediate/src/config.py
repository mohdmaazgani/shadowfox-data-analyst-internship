"""Central configuration for the Online Retail customer & revenue analysis.

Every path, business rule and constant used by the pipeline lives here so that
the analysis is transparent and easy to change in one place.
"""
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUT_TABLES = ROOT / "outputs" / "tables"
OUT_CHARTS = ROOT / "outputs" / "charts"
REPORTS = ROOT / "reports"
DASHBOARD = ROOT / "dashboard"
DOCS = ROOT / "docs"

RAW_FILE = DATA_RAW / "online_retail_raw.csv.gz"
SALES_FILE = DATA_PROCESSED / "sales_clean.csv.gz"
RETURNS_FILE = DATA_PROCESSED / "returns_clean.csv.gz"
NONPRODUCT_FILE = DATA_PROCESSED / "non_product_lines.csv.gz"

# Source of the raw data (used only by src/00_download_data.py)
DATA_URL = (
    "https://raw.githubusercontent.com/allanvc/onlineretail/master/data/onlineretail.rda"
)

# --------------------------------------------------------------------------- #
# Business rules
# --------------------------------------------------------------------------- #
# Stock codes that are services / fees / manual adjustments rather than
# merchandise. They are kept aside (not deleted) and never mixed into product
# or merchandise-revenue analysis.
NON_PRODUCT_CODES = {
    "POST", "DOT", "M", "C2", "D", "S", "B", "PADS",
    "BANK CHARGES", "AMAZONFEE", "CRUK",
}
NON_PRODUCT_PREFIXES = ("gift_",)  # gift vouchers

# The source data stops on 9 Dec 2011, so December 2011 is a PARTIAL month and
# must never be compared with full months.
FIRST_FULL_MONTH = "2010-12"
LAST_FULL_MONTH = "2011-11"
PARTIAL_MONTH = "2011-12"

# RFM settings
RFM_BINS = 5

# Report author (leave blank to omit from the PDF cover page)
AUTHOR = ""

# --------------------------------------------------------------------------- #
# Visual identity (used by every chart so the report looks consistent)
# --------------------------------------------------------------------------- #
PALETTE = {
    "primary": "#1F4E79",    # deep blue  - main series
    "secondary": "#2E9CCA",  # sky blue   - supporting series
    "accent": "#E4572E",     # orange-red - highlights / warnings
    "positive": "#3BA55C",   # green      - good
    "muted": "#9AA5B1",      # grey       - context / partial data
    "dark": "#22303C",       # near black - text
    "light": "#EEF2F6",      # pale grey  - backgrounds
}
