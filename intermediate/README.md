# Customer & Revenue Performance Analysis of a UK Online Retailer

**ShadowFox Data Analyst Internship — Intermediate Level submission.**

A business performance analysis of customer behaviour, revenue concentration,
seasonality and repeat purchasing for a real UK online gift wholesaler, built
entirely from raw transaction data with a fully reproducible Python pipeline.

📄 **[Read the full report](reports/Intermediate_Level_Customer_Revenue_Analysis.pdf)**
🖼️ **[View the executive dashboard](dashboard/executive_dashboard.png)**

## Headline findings

- **£9.77M** net revenue from **19,773 orders** and **4,334 identified customers** (AOV £518).
- **Seasonality**: Sep-Nov produced **37.5%** of full-year net revenue; November was **2.25x** the Jan-Aug monthly average, driven by more orders and customers, not bigger baskets.
- **Concentration**: the top **10%** of customers generate **60%** of net revenue; "Champions" (14% of customers) alone generate **50%**.
- **Retention**: **65%** of customers buy again and drive **94%** of revenue, but only **~20%** of new customers place a second order the following month.
- **Returns**: the headline 4.6% return rate is overstated — **61.5%** of "returns" value comes from two orders cancelled minutes after being placed. The genuine return rate is **1.8%**.
- **Geography**: the UK is **84.8%** of revenue; three of the next five markets (Netherlands, EIRE, Australia) each depend on just one or two large accounts.

## Why this dataset

The task brief allowed a free choice of dataset for a "customer, revenue, or
business performance analysis on a more realistic dataset." I used the
[UCI Online Retail dataset](https://archive.ics.uci.edu/dataset/352/online-retail)
(Chen, Sain & Guo, 2012, CC BY 4.0) — 541,909 real transactions from a UK
online gift wholesaler, Dec 2010–Dec 2011 — because it has customer IDs,
which the brief's retention, repeat-purchase and segment-performance
requirements need, and is large and messy enough for genuine cleaning
decisions rather than a toy dataset.

## Repository structure

```
online-retail-customer-analysis/
├── data/
│   ├── raw/                    # Raw dataset (as downloaded, gzip CSV)
│   └── processed/              # Cleaned sales / returns / non-product tables
├── src/                        # Reproducible analysis pipeline (see below)
│   ├── config.py                #   paths, business rules, colour palette
│   ├── 00_download_data.py      #   optional: re-fetch the raw dataset
│   ├── clean.py                 #   Step 1: cleaning, with an auditable log
│   ├── analysis.py              #   Step 2: every metric/table in the report
│   ├── charts.py                #   Step 3: all charts + executive dashboard
│   └── report.py                #   Step 4: assembles the final PDF
├── outputs/
│   ├── tables/                 # 22 CSV tables + kpis_and_facts.json
│   └── charts/                 # 13 PNG charts (full resolution)
├── dashboard/
│   └── executive_dashboard.png # One-page executive summary dashboard
├── reports/
│   └── Intermediate_Level_Customer_Revenue_Analysis.pdf   # Final report
├── docs/
│   ├── methodology.md          # Every analytical decision, explained
│   ├── data_dictionary.md      # Column-by-column reference for every file
│   └── video_script.md         # Outline for the required walkthrough video
├── notebooks/
│   └── exploration.ipynb       # Exploratory notebook (executed, with output)
├── run_pipeline.py             # Runs all 4 steps end to end
├── requirements.txt
└── README.md
```

## Reproducing this analysis

```bash
pip install -r requirements.txt
python run_pipeline.py
```

This regenerates, in order:
1. `data/processed/*.csv.gz` — cleaned sales, returns and non-product tables, plus `outputs/tables/data_cleaning_log.csv`
2. `outputs/tables/*.csv` and `kpis_and_facts.json` — every number quoted in the report
3. `outputs/charts/*.png` and `dashboard/executive_dashboard.png`
4. `reports/Intermediate_Level_Customer_Revenue_Analysis.pdf`

Each step can also be run on its own (`python src/clean.py`, etc.) since every
step reads its input from the previous step's saved output on disk.

The raw data is already included at `data/raw/online_retail_raw.csv.gz`, so
`00_download_data.py` only needs to be run if you want to rebuild it from
source (requires `pip install pyreadr`).

## Methodology highlights

Full detail in [`docs/methodology.md`](docs/methodology.md); the short
version:

- **Cleaning**: removed 5,268 exact duplicates, separated 2,910
  non-merchandise lines (postage, fees, vouchers) and 8,668 cancellations
  into their own tables, and dropped ~2,500 non-positive quantity/price
  lines — leaving 522,568 clean sales lines. Every rule is logged with row
  counts and £ impact.
- **Order-entry reversals**: returns are flagged as same-day reversals when
  a customer returns the exact product/quantity they bought within 24
  hours. This surfaced that 62% of "returns" value came from just two
  cancelled orders — a materially different (and more honest) return-rate
  story than the headline number.
- **RFM segmentation**: computed for the 4,320 identified customers with
  positive net revenue, using business-defined frequency bands (not raw
  quintiles) to avoid arbitrary tie-breaking on a heavily-repeated
  distribution.
- **Cohort retention**: the December 2010 cohort is excluded from the
  average retention calculation, since the dataset's start date artificially
  creates it by mixing genuinely new customers with pre-existing ones.
- **Full vs. partial months**: December 2011 (data stops 9 Dec) is shown
  but excluded from every trend and month-over-month comparison.

## Tools

Python (pandas, numpy), matplotlib + seaborn for charts, reportlab for the
PDF report. No BI tool license required — everything is code, so the whole
analysis is version-controllable and re-runs from raw data in under a minute.
