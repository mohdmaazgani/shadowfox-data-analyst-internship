"""Step 1 - Data cleaning & preparation.

Reads the raw transactions and produces three analysis-ready tables:

* sales_clean        - genuine merchandise sales lines (the "fact" table)
* returns_clean      - cancelled / returned merchandise lines
* non_product_lines  - postage, fees, manual adjustments, vouchers (kept aside)

Every rule is logged with the number of rows and the money it affects, so the
cleaning is fully auditable (outputs/tables/data_cleaning_log.csv).

Usage:  python src/clean.py
"""
import pandas as pd

from config import (
    NON_PRODUCT_CODES,
    NON_PRODUCT_PREFIXES,
    NONPRODUCT_FILE,
    OUT_TABLES,
    RAW_FILE,
    RETURNS_FILE,
    SALES_FILE,
)


def load_raw() -> pd.DataFrame:
    """Load the raw CSV with explicit dtypes (invoice / stock codes are text)."""
    return pd.read_csv(
        RAW_FILE,
        dtype={"InvoiceNo": "string", "StockCode": "string", "Description": "string",
               "Country": "string", "CustomerID": "Int64"},
        parse_dates=["InvoiceDate"],
    )


def _money(df: pd.DataFrame) -> float:
    return float((df["Quantity"] * df["UnitPrice"]).sum())


def clean(raw: pd.DataFrame):
    """Apply the cleaning rules. Returns (sales, returns, non_product, log_df)."""
    log = []

    def record(step, rule, affected, remaining, value=None, note=""):
        log.append({
            "step": step, "rule": rule, "rows_affected": int(affected),
            "rows_remaining": int(remaining),
            "value_affected_gbp": None if value is None else round(value, 2),
            "note": note,
        })

    df = raw.copy()
    record(0, "Raw data loaded", 0, len(df), _money(df),
           "541,909 transaction lines, 8 columns")

    # ---- 1. Standardise text fields ------------------------------------- #
    for col in ["InvoiceNo", "StockCode", "Country"]:
        df[col] = df[col].str.strip()
    df["StockCode"] = df["StockCode"].str.upper()
    df["Description"] = df["Description"].str.strip().str.upper()

    # ---- 2. Exact duplicate rows ---------------------------------------- #
    dup_mask = df.duplicated(keep="first")
    record(1, "Remove exact duplicate rows (all 8 columns identical)",
           dup_mask.sum(), len(df) - dup_mask.sum(), _money(df[dup_mask]),
           "Same invoice, product, quantity, price, timestamp -> treated as double entry")
    df = df[~dup_mask].copy()

    # ---- 3. Non-product lines (postage, fees, adjustments, vouchers) ---- #
    is_nonprod = df["StockCode"].isin(NON_PRODUCT_CODES) | df["StockCode"].str.startswith(
        NON_PRODUCT_PREFIXES)
    non_product = df[is_nonprod].copy()
    record(2, "Separate non-product lines (POST, DOT, M, D, S, B, C2, BANK CHARGES, "
              "AMAZONFEE, CRUK, PADS, gift vouchers)",
           is_nonprod.sum(), len(df) - is_nonprod.sum(), _money(non_product),
           "Kept in non_product_lines file; excluded from merchandise revenue")
    df = df[~is_nonprod].copy()

    # ---- 4. Cancellations -> returns table ------------------------------ #
    is_cancel = df["InvoiceNo"].str.startswith("C")
    returns = df[is_cancel].copy()
    record(3, "Separate cancellations (InvoiceNo starts with 'C') into returns table",
           is_cancel.sum(), len(df) - is_cancel.sum(), _money(returns),
           "Analysed separately as returns; netted off in net-revenue metrics")
    df = df[~is_cancel].copy()

    # ---- 5. Invalid sales lines ----------------------------------------- #
    bad_qty = df["Quantity"] <= 0
    record(4, "Remove sales lines with Quantity <= 0 (stock write-offs / damages)",
           bad_qty.sum(), len(df) - bad_qty.sum(), _money(df[bad_qty]),
           "Non-customer stock adjustments, not real sales")
    df = df[~bad_qty].copy()

    bad_price = df["UnitPrice"] <= 0
    record(5, "Remove sales lines with UnitPrice <= 0 (free items / adjustments)",
           bad_price.sum(), len(df) - bad_price.sum(), _money(df[bad_price]),
           "Zero-priced lines carry no revenue and usually have no description")
    df = df[~bad_price].copy()

    # Same validity rule for returns (a return needs a positive price)
    bad_ret = (returns["UnitPrice"] <= 0) | (returns["Quantity"] >= 0)
    record(6, "Remove return lines with UnitPrice <= 0 or Quantity >= 0",
           bad_ret.sum(), len(returns) - bad_ret.sum(), _money(returns[bad_ret]),
           "Cannot value a return without a positive price")
    returns = returns[~bad_ret].copy()

    # ---- 6. Canonical product description -------------------------------- #
    # A StockCode can carry several description spellings. Use the most frequent
    # one as the canonical name so each product appears once.
    combined = pd.concat([df, returns])
    canon = (combined.dropna(subset=["Description"])
             .groupby("StockCode")["Description"]
             .agg(lambda s: s.value_counts().idxmax()))
    n_missing_before = int(df["Description"].isna().sum() + returns["Description"].isna().sum())
    n_changed = 0
    multi_name_codes = int((combined.dropna(subset=["Description"])
                            .groupby("StockCode")["Description"].nunique() > 1).sum())
    for frame in (df, returns):
        mapped = frame["StockCode"].map(canon)
        n_changed += int((mapped.notna() & (mapped != frame["Description"])).sum())
        frame["Description"] = mapped
    n_missing_after = int(df["Description"].isna().sum() + returns["Description"].isna().sum())
    record(7, "Standardise product names (one canonical description per StockCode)",
           n_changed, len(df), None,
           f"{multi_name_codes} StockCodes had >1 spelling; {n_changed:,} rows renamed. "
           f"Missing descriptions before: {n_missing_before}, after: {n_missing_after}")
    df = df.dropna(subset=["Description"]).copy()
    returns = returns.dropna(subset=["Description"]).copy()

    # ---- 7. Derived analysis columns ------------------------------------ #
    for frame, sign in ((df, 1), (returns, -1)):
        frame["Revenue"] = (frame["Quantity"] * frame["UnitPrice"] * sign).round(2)
        frame["InvoiceMonth"] = frame["InvoiceDate"].dt.to_period("M").astype(str)
        frame["InvoiceDay"] = frame["InvoiceDate"].dt.date.astype(str)
        frame["Weekday"] = frame["InvoiceDate"].dt.day_name()
        frame["Hour"] = frame["InvoiceDate"].dt.hour
        frame["HasCustomerID"] = frame["CustomerID"].notna()
    returns = returns.rename(columns={"Revenue": "ReturnValue"})

    record(8, "Add derived columns: Revenue, InvoiceMonth, InvoiceDay, Weekday, Hour, HasCustomerID",
           len(df), len(df), None,
           "Revenue = Quantity x UnitPrice (ReturnValue is positive for returns)")

    # ---- 8. Missing customer IDs: flagged, NOT dropped ------------------- #
    n_guest = int((~df["HasCustomerID"]).sum())
    record(9, "Flag lines without CustomerID (kept for revenue/product analysis)",
           n_guest, len(df), float(df.loc[~df["HasCustomerID"], "Revenue"].sum()),
           "Excluded only from customer-level analysis (RFM, cohorts, repeat behaviour)")

    record(10, "FINAL clean sales table", 0, len(df), float(df["Revenue"].sum()),
           f"Returns table: {len(returns):,} rows; non-product lines: {len(non_product):,} rows")

    df = df.sort_values(["InvoiceDate", "InvoiceNo"]).reset_index(drop=True)
    returns = returns.sort_values(["InvoiceDate", "InvoiceNo"]).reset_index(drop=True)
    return df, returns, non_product, pd.DataFrame(log)


def main() -> None:
    raw = load_raw()
    sales, returns, non_product, log = clean(raw)

    SALES_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUT_TABLES.mkdir(parents=True, exist_ok=True)
    sales.to_csv(SALES_FILE, index=False, compression="gzip")
    returns.to_csv(RETURNS_FILE, index=False, compression="gzip")
    non_product.to_csv(NONPRODUCT_FILE, index=False, compression="gzip")
    log.to_csv(OUT_TABLES / "data_cleaning_log.csv", index=False)

    print(log.to_string(index=False))
    print(f"\nSaved: {SALES_FILE.name} ({len(sales):,} rows), "
          f"{RETURNS_FILE.name} ({len(returns):,}), {NONPRODUCT_FILE.name} ({len(non_product):,})")


if __name__ == "__main__":
    main()
