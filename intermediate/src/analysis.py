"""Step 2 - Exploratory & business analysis.

Turns the cleaned tables into every metric used in the report:

    1. Headline KPIs
    2. Monthly revenue trend & seasonality
    3. Day-of-week / hour-of-day patterns
    4. Geography (country performance)
    5. Product performance, Pareto and seasonal products
    6. Customer table, RFM segmentation
    7. Revenue concentration
    8. Repeat purchase behaviour & new-vs-returning revenue
    9. Cohort retention
   10. Returns / cancellations

Definitions (also documented in docs/methodology.md)
----------------------------------------------------
Gross revenue = sum(Quantity x UnitPrice) over valid merchandise sales lines
Returns       = value of cancelled merchandise lines (invoice starts with "C")
Net revenue   = Gross revenue - Returns          <-- headline revenue metric
Order         = one invoice
AOV           = gross revenue / orders
Customer-level analyses use only lines with a CustomerID (~85% of revenue).

Usage:  python src/analysis.py
"""
import json

import numpy as np
import pandas as pd

from config import (
    FIRST_FULL_MONTH,
    LAST_FULL_MONTH,
    OUT_TABLES,
    PARTIAL_MONTH,
    RETURNS_FILE,
    SALES_FILE,
)

WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
SEGMENT_ORDER = [
    "Champions", "Loyal Customers", "Potential Loyalists", "New Customers", "Promising",
    "Need Attention", "About to Sleep", "At Risk", "Can't Lose Them", "Hibernating",
]
CHRISTMAS_PATTERN = r"CHRISTMAS|XMAS|SANTA|ADVENT|REINDEER"


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_clean():
    """Load the cleaned sales and returns tables."""
    dtypes = {"InvoiceNo": "string", "StockCode": "string", "Description": "string",
              "Country": "string", "CustomerID": "Int64", "InvoiceMonth": "string",
              "InvoiceDay": "string", "Weekday": "string"}
    sales = pd.read_csv(SALES_FILE, dtype=dtypes, parse_dates=["InvoiceDate"])
    returns = pd.read_csv(RETURNS_FILE, dtype=dtypes, parse_dates=["InvoiceDate"])
    return sales, returns


def _round(df: pd.DataFrame, n: int = 2) -> pd.DataFrame:
    """Round numeric columns only (datetime columns are left untouched)."""
    num = df.select_dtypes(include="number").columns
    df = df.copy()
    df[num] = df[num].round(n)
    return df


def flag_reversals(sales, returns) -> pd.Series:
    """Flag return lines that reverse an identical purchase made in the previous 24h.

    Same customer + same product + same quantity, returned within 24 hours of the
    sale. These are almost always order-entry corrections rather than genuine
    product returns, and they include the two largest orders in the dataset
    (invoices 581483 and 541431). They net to zero in net revenue but would
    badly distort return-rate metrics if left in.
    """
    s = (sales.dropna(subset=["CustomerID"])[["CustomerID", "StockCode", "Quantity", "InvoiceDate"]]
         .rename(columns={"InvoiceDate": "sale_time", "Quantity": "sale_qty"}))
    rr = returns.dropna(subset=["CustomerID"])[["CustomerID", "StockCode", "Quantity", "InvoiceDate"]].copy()
    rr["ret_id"] = rr.index
    rr["abs_qty"] = -rr["Quantity"]
    m = rr.merge(s, left_on=["CustomerID", "StockCode", "abs_qty"],
                 right_on=["CustomerID", "StockCode", "sale_qty"])
    m = m[(m["InvoiceDate"] >= m["sale_time"]) & (m["InvoiceDate"] - m["sale_time"] <= pd.Timedelta(hours=24))]
    return returns.index.to_series().isin(set(m["ret_id"]))


def full_months() -> list:
    return [str(p) for p in pd.period_range(FIRST_FULL_MONTH, LAST_FULL_MONTH, freq="M")]


# --------------------------------------------------------------------------- #
# 1-2. KPIs and monthly trend
# --------------------------------------------------------------------------- #
def build_monthly(sales, returns) -> pd.DataFrame:
    m = sales.groupby("InvoiceMonth").agg(
        gross_revenue=("Revenue", "sum"),
        orders=("InvoiceNo", "nunique"),
        active_customers=("CustomerID", "nunique"),
        units=("Quantity", "sum"),
    )
    m["returns_value"] = returns.groupby("InvoiceMonth")["ReturnValue"].sum()
    m["returns_value"] = m["returns_value"].fillna(0)
    m["reversal_value"] = returns[returns["is_reversal"]].groupby("InvoiceMonth")["ReturnValue"].sum()
    m["reversal_value"] = m["reversal_value"].fillna(0)
    m["net_revenue"] = m["gross_revenue"] - m["returns_value"]
    m["return_rate_pct"] = 100 * m["returns_value"] / m["gross_revenue"]
    # "Adjusted" removes same-day order reversals from both numerator and denominator
    m["return_rate_adj_pct"] = 100 * (m["returns_value"] - m["reversal_value"]) / (
        m["gross_revenue"] - m["reversal_value"])
    m["aov"] = m["gross_revenue"] / m["orders"]
    m["is_partial_month"] = m.index == PARTIAL_MONTH
    # Growth is only meaningful between two FULL months.
    m["net_revenue_mom_pct"] = np.nan
    fm = [x for x in m.index if x in full_months()]
    m.loc[fm, "net_revenue_mom_pct"] = 100 * m.loc[fm, "net_revenue"].pct_change()
    return _round(m).reset_index().rename(columns={"InvoiceMonth": "month"})


def build_kpis(sales, returns, monthly) -> dict:
    gross = sales["Revenue"].sum()
    ret = returns["ReturnValue"].sum()
    orders = sales["InvoiceNo"].nunique()
    ident = sales[sales["CustomerID"].notna()]
    fm = monthly[~monthly["is_partial_month"]]
    return {
        "date_start": str(sales["InvoiceDate"].min().date()),
        "date_end": str(sales["InvoiceDate"].max().date()),
        "gross_revenue": gross,
        "returns_value": ret,
        "net_revenue": gross - ret,
        "return_rate_pct": 100 * ret / gross,
        "orders": orders,
        "customers": ident["CustomerID"].nunique(),
        "aov": gross / orders,
        "units_sold": int(sales["Quantity"].sum()),
        "units_per_order": sales["Quantity"].sum() / orders,
        "lines_per_order": len(sales) / orders,
        "products_sold": sales["StockCode"].nunique(),
        "countries": sales["Country"].nunique(),
        "sales_lines": len(sales),
        "pct_revenue_identified_customers": 100 * ident["Revenue"].sum() / gross,
        "pct_lines_without_customer_id": 100 * (sales["CustomerID"].isna()).mean(),
        "avg_monthly_net_revenue_full_months": fm["net_revenue"].mean(),
    }


def seasonality(monthly) -> dict:
    """Quantify the autumn peak using FULL months only."""
    fm = monthly[monthly["month"].isin(full_months())].set_index("month")
    total = fm["net_revenue"].sum()
    sep_nov = fm.loc[["2011-09", "2011-10", "2011-11"], "net_revenue"].sum()
    jan_aug = fm.loc[[f"2011-{i:02d}" for i in range(1, 9)], "net_revenue"]
    peak_month = fm["net_revenue"].idxmax()
    low_month = fm["net_revenue"].idxmin()
    return {
        "sep_nov_share_pct": 100 * sep_nov / total,
        "sep_nov_months_share_of_year_pct": 100 * 3 / 12,
        "jan_aug_avg_monthly": jan_aug.mean(),
        "nov_vs_jan_aug_avg_x": fm.loc["2011-11", "net_revenue"] / jan_aug.mean(),
        "peak_month": peak_month,
        "peak_month_net_revenue": fm.loc[peak_month, "net_revenue"],
        "low_month": low_month,
        "low_month_net_revenue": fm.loc[low_month, "net_revenue"],
        "nov_vs_oct_pct": 100 * (fm.loc["2011-11", "net_revenue"] / fm.loc["2011-10", "net_revenue"] - 1),
        "nov_orders_vs_jan_aug_x": fm.loc["2011-11", "orders"] / fm.loc[jan_aug.index, "orders"].mean(),
        "nov_customers_vs_jan_aug_x": fm.loc["2011-11", "active_customers"] / fm.loc[jan_aug.index, "active_customers"].mean(),
        "nov_aov_vs_jan_aug_x": fm.loc["2011-11", "aov"] / fm.loc[jan_aug.index, "aov"].mean(),
        "jan_aug_avg_orders": fm.loc[jan_aug.index, "orders"].mean(),
        "jan_aug_avg_active_customers": fm.loc[jan_aug.index, "active_customers"].mean(),
        "jan_aug_avg_aov": fm.loc[jan_aug.index, "aov"].mean(),
        "nov_vs_dec10_pct": 100 * (fm.loc["2011-11", "net_revenue"] / fm.loc["2010-12", "net_revenue"] - 1),
    }


# --------------------------------------------------------------------------- #
# 3. Time-of-week patterns
# --------------------------------------------------------------------------- #
def time_patterns(sales):
    wd = sales.groupby("Weekday").agg(
        gross_revenue=("Revenue", "sum"), orders=("InvoiceNo", "nunique"))
    wd = wd.reindex(WEEKDAYS).fillna(0)
    wd["aov"] = (wd["gross_revenue"] / wd["orders"].replace(0, np.nan)).fillna(0)
    wd["share_pct"] = 100 * wd["gross_revenue"] / wd["gross_revenue"].sum()
    wd = wd.round(2).reset_index()

    hr = sales.groupby("Hour").agg(
        gross_revenue=("Revenue", "sum"), orders=("InvoiceNo", "nunique"))
    hr["share_pct"] = 100 * hr["gross_revenue"] / hr["gross_revenue"].sum()
    return wd, hr.round(2).reset_index()


# --------------------------------------------------------------------------- #
# 4. Geography
# --------------------------------------------------------------------------- #
def country_table(sales, returns) -> pd.DataFrame:
    c = sales.groupby("Country").agg(
        gross_revenue=("Revenue", "sum"), orders=("InvoiceNo", "nunique"),
        customers=("CustomerID", "nunique"), units=("Quantity", "sum"))
    c["returns_value"] = returns.groupby("Country")["ReturnValue"].sum()
    c["returns_value"] = c["returns_value"].fillna(0)
    c["net_revenue"] = c["gross_revenue"] - c["returns_value"]
    c["aov"] = c["gross_revenue"] / c["orders"]
    c["revenue_per_customer"] = c["net_revenue"] / c["customers"].replace(0, np.nan)
    c["share_of_net_pct"] = 100 * c["net_revenue"] / c["net_revenue"].sum()
    # Concentration inside each country: how much rides on the single biggest account?
    per_cust = (sales.dropna(subset=["CustomerID"]).groupby(["Country", "CustomerID"])["Revenue"]
                .sum().reset_index())
    top_share = per_cust.groupby("Country")["Revenue"].max() / per_cust.groupby("Country")["Revenue"].sum()
    c["top_customer_share_pct"] = 100 * top_share
    return _round(c.sort_values("net_revenue", ascending=False)).reset_index()


# --------------------------------------------------------------------------- #
# 5. Products
# --------------------------------------------------------------------------- #
def product_tables(sales, returns):
    p = sales.groupby("StockCode").agg(
        description=("Description", "first"), gross_revenue=("Revenue", "sum"),
        units=("Quantity", "sum"), orders=("InvoiceNo", "nunique"),
        customers=("CustomerID", "nunique"))
    r = returns.groupby("StockCode").agg(
        returns_value=("ReturnValue", "sum"), returns_units=("Quantity", lambda s: -s.sum()))
    p = p.join(r).fillna({"returns_value": 0, "returns_units": 0})
    p["reversal_value"] = returns[returns["is_reversal"]].groupby("StockCode")["ReturnValue"].sum()
    p["reversal_value"] = p["reversal_value"].fillna(0)
    p["net_revenue"] = p["gross_revenue"] - p["returns_value"]
    p["return_rate_pct"] = 100 * p["returns_value"] / p["gross_revenue"]
    denom = (p["gross_revenue"] - p["reversal_value"]).where(lambda d: d > 0)
    p["return_rate_adj_pct"] = 100 * (p["returns_value"] - p["reversal_value"]) / denom
    p["avg_unit_price"] = p["gross_revenue"] / p["units"]
    p = p.sort_values("net_revenue", ascending=False)
    p["cum_share_pct"] = 100 * p["net_revenue"].clip(lower=0).cumsum() / p["net_revenue"].clip(lower=0).sum()
    p["rank"] = np.arange(1, len(p) + 1)
    p = _round(p).reset_index()

    # Pareto facts
    pos = p[p["net_revenue"] > 0]
    n = len(pos)
    n80 = int((pos["cum_share_pct"] < 80).sum() + 1)
    pareto = {
        "products_with_positive_net": n,
        "products_for_80pct_revenue": n80,
        "products_for_80pct_share_of_range_pct": 100 * n80 / n,
        "top10_share_pct": float(pos.head(10)["net_revenue"].sum() / pos["net_revenue"].sum() * 100),
        "top20pct_products_share_pct": float(
            pos.head(int(n * 0.2))["net_revenue"].sum() / pos["net_revenue"].sum() * 100),
        "bottom50pct_products_share_pct": float(
            pos.tail(int(n * 0.5))["net_revenue"].sum() / pos["net_revenue"].sum() * 100),
    }

    # Product x month heatmap for the top 10 SKUs (full months only)
    top_codes = p.head(10)["StockCode"].tolist()
    heat = (sales[sales["StockCode"].isin(top_codes) & sales["InvoiceMonth"].isin(full_months())]
            .pivot_table(index="Description", columns="InvoiceMonth", values="Revenue",
                         aggfunc="sum", fill_value=0)
            .reindex(columns=full_months(), fill_value=0))
    order = p.head(10).set_index("StockCode").loc[top_codes, "description"].tolist()
    heat = heat.reindex(order)

    # Seasonal products: >=60% of their full-year revenue falls in Sep-Nov
    fy = sales[sales["InvoiceMonth"].isin(full_months())].copy()
    fy["is_autumn"] = fy["InvoiceMonth"].isin(["2011-09", "2011-10", "2011-11"])
    sp = fy.groupby("StockCode").apply(
        lambda g: pd.Series({
            "description": g["Description"].iloc[0],
            "revenue_12m": g["Revenue"].sum(),
            "autumn_share_pct": 100 * g.loc[g["is_autumn"], "Revenue"].sum() / g["Revenue"].sum(),
        }), include_groups=False).reset_index()
    seasonal = sp[(sp["revenue_12m"] >= 5000) & (sp["autumn_share_pct"] >= 60)]
    seasonal = seasonal.sort_values("revenue_12m", ascending=False).round(2)

    # Christmas-themed lines (keyword heuristic on product name)
    fy["is_xmas"] = fy["Description"].str.contains(CHRISTMAS_PATTERN, regex=True, na=False)
    xm = fy.groupby("InvoiceMonth").apply(
        lambda g: 100 * g.loc[g["is_xmas"], "Revenue"].sum() / g["Revenue"].sum(),
        include_groups=False).rename("christmas_themed_share_pct").round(2).reset_index()
    pareto["christmas_share_of_sep_nov_pct"] = float(
        100 * fy.loc[fy["is_xmas"] & fy["is_autumn"], "Revenue"].sum()
        / fy.loc[fy["is_autumn"], "Revenue"].sum())
    pareto["seasonal_products_count"] = int(len(seasonal))
    pareto["seasonal_products_revenue"] = float(seasonal["revenue_12m"].sum())
    return p, pareto, heat.round(2).rename_axis("Description").reset_index(), seasonal, xm


# --------------------------------------------------------------------------- #
# 6. Customer table + RFM
# --------------------------------------------------------------------------- #
def rfm_segment(r: int, f: int) -> str:
    """Classic R/F grid mapping (Putler-style). R,F in 1..5."""
    if r <= 2:
        if f <= 2:
            return "Hibernating"
        return "At Risk" if f <= 4 else "Can't Lose Them"
    if r == 3:
        if f <= 2:
            return "About to Sleep"
        return "Need Attention" if f == 3 else "Loyal Customers"
    if r == 4:
        if f == 1:
            return "Promising"
        return "Potential Loyalists" if f <= 3 else "Loyal Customers"
    if f == 1:
        return "New Customers"
    return "Potential Loyalists" if f <= 3 else "Champions"


def frequency_score(n_orders: int) -> int:
    """Business-defined frequency bands (avoids arbitrary tie-breaking)."""
    if n_orders == 1:
        return 1
    if n_orders == 2:
        return 2
    if n_orders == 3:
        return 3
    return 4 if n_orders <= 5 else 5


def customer_table(sales, returns) -> pd.DataFrame:
    ident = sales[sales["CustomerID"].notna()]
    snapshot = sales["InvoiceDate"].max().normalize() + pd.Timedelta(days=1)

    c = ident.groupby("CustomerID").agg(
        first_order=("InvoiceDate", "min"), last_order=("InvoiceDate", "max"),
        orders=("InvoiceNo", "nunique"), units=("Quantity", "sum"),
        gross_revenue=("Revenue", "sum"), country=("Country", lambda s: s.mode().iat[0]),
        distinct_products=("StockCode", "nunique"))
    c["returns_value"] = returns.dropna(subset=["CustomerID"]).groupby("CustomerID")["ReturnValue"].sum()
    c["returns_value"] = c["returns_value"].fillna(0)
    c["net_revenue"] = c["gross_revenue"] - c["returns_value"]
    c["aov"] = c["gross_revenue"] / c["orders"]
    c["recency_days"] = (snapshot - c["last_order"].dt.normalize()).dt.days
    c["tenure_days"] = (c["last_order"].dt.normalize() - c["first_order"].dt.normalize()).dt.days
    c["first_order_month"] = c["first_order"].dt.to_period("M").astype(str)

    # RFM is computed for customers whose net contribution is positive
    c["in_rfm"] = c["net_revenue"] > 0
    rf = c[c["in_rfm"]].copy()
    rf["R"] = pd.qcut(rf["recency_days"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]).astype(int)
    rf["F"] = rf["orders"].map(frequency_score)
    rf["M"] = pd.qcut(rf["net_revenue"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]).astype(int)
    rf["segment"] = [rfm_segment(r, f) for r, f in zip(rf["R"], rf["F"])]
    c = c.join(rf[["R", "F", "M", "segment"]])
    return _round(c).reset_index()


def rfm_summary(cust) -> pd.DataFrame:
    rf = cust[cust["in_rfm"]]
    s = rf.groupby("segment").agg(
        customers=("CustomerID", "count"), net_revenue=("net_revenue", "sum"),
        avg_recency_days=("recency_days", "mean"), avg_orders=("orders", "mean"),
        avg_net_revenue=("net_revenue", "mean"), median_aov=("aov", "median"))
    s["pct_customers"] = 100 * s["customers"] / s["customers"].sum()
    s["pct_net_revenue"] = 100 * s["net_revenue"] / s["net_revenue"].sum()
    s = s.reindex(SEGMENT_ORDER).dropna(how="all")
    return s.round(2).reset_index()


# --------------------------------------------------------------------------- #
# 7. Concentration
# --------------------------------------------------------------------------- #
def concentration(cust):
    rf = cust[cust["in_rfm"]].sort_values("net_revenue", ascending=False).reset_index(drop=True)
    total = rf["net_revenue"].sum()
    n = len(rf)
    cum = rf["net_revenue"].cumsum() / total

    def top_share(pct):
        k = int(np.ceil(n * pct))
        return 100 * rf["net_revenue"].head(k).sum() / total

    rf["decile"] = pd.qcut(rf.index, 10, labels=range(1, 11)).astype(int)
    dec = rf.groupby("decile").agg(customers=("CustomerID", "count"),
                                   net_revenue=("net_revenue", "sum"))
    dec["share_pct"] = 100 * dec["net_revenue"] / total
    dec["cum_share_pct"] = dec["share_pct"].cumsum()

    top10_customers = rf.head(10)[["CustomerID", "country", "orders", "net_revenue"]]
    facts = {
        "customers_in_rfm": n,
        "total_net_revenue_identified": float(total),
        "top1pct_share": top_share(0.01), "top5pct_share": top_share(0.05),
        "top10pct_share": top_share(0.10), "top20pct_share": top_share(0.20),
        "bottom50pct_share": float(100 * rf["net_revenue"].tail(n // 2).sum() / total),
        "customers_for_50pct": int((cum < 0.5).sum() + 1),
        "customers_for_80pct": int((cum < 0.8).sum() + 1),
        "top10_customers_share": float(100 * top10_customers["net_revenue"].sum() / total),
        "largest_customer_share": float(100 * rf["net_revenue"].iloc[0] / total),
    }
    curve = pd.DataFrame({"pct_customers": 100 * (np.arange(1, n + 1) / n),
                          "cum_revenue_pct": 100 * cum})
    return dec.round(2).reset_index(), facts, top10_customers.round(2), curve


# --------------------------------------------------------------------------- #
# 8. Repeat behaviour
# --------------------------------------------------------------------------- #
def repeat_behaviour(sales, cust):
    rf = cust[cust["in_rfm"]]
    # Only customers with positive net revenue (drops the handful whose every order was cancelled)
    ident = sales[sales["CustomerID"].isin(rf["CustomerID"])].copy()

    # Orders-per-customer distribution
    bands = pd.cut(rf["orders"], bins=[0, 1, 2, 3, 5, 10, 10_000],
                   labels=["1 order", "2 orders", "3 orders", "4-5 orders", "6-10 orders", "11+ orders"])
    dist = rf.groupby(bands, observed=False).agg(
        customers=("CustomerID", "count"), net_revenue=("net_revenue", "sum"))
    dist["pct_customers"] = 100 * dist["customers"] / dist["customers"].sum()
    dist["pct_net_revenue"] = 100 * dist["net_revenue"] / dist["net_revenue"].sum()
    dist = dist.round(2).reset_index().rename(columns={"orders": "orders_band"})

    repeaters = rf[rf["orders"] >= 2]
    facts = {
        "repeat_customer_rate_pct": 100 * len(repeaters) / len(rf),
        "one_time_customers": int((rf["orders"] == 1).sum()),
        "repeat_customers": int(len(repeaters)),
        "repeat_revenue_share_pct": 100 * repeaters["net_revenue"].sum() / rf["net_revenue"].sum(),
        "avg_orders_per_customer": float(rf["orders"].mean()),
        "median_orders_per_customer": float(rf["orders"].median()),
        "avg_revenue_repeat_vs_onetime_x": float(
            repeaters["net_revenue"].mean() / rf.loc[rf["orders"] == 1, "net_revenue"].mean()),
    }

    # Days between shopping days for repeat customers
    days = (ident[["CustomerID", "InvoiceDay"]].drop_duplicates()
            .assign(day=lambda d: pd.to_datetime(d["InvoiceDay"])).sort_values(["CustomerID", "day"]))
    gaps = days.groupby("CustomerID")["day"].diff().dt.days.dropna()
    facts["median_days_between_orders"] = float(gaps.median())
    facts["mean_days_between_orders"] = float(gaps.mean())

    # 90-day repeat rate among customers with >=90 days of follow-up
    cutoff = sales["InvoiceDate"].max() - pd.Timedelta(days=90)
    first = ident.groupby("CustomerID")["InvoiceDate"].min()
    # Only customers first seen from Jan-2011 (Dec-2010 arrivals may be long-standing customers)
    eligible = first[(first <= cutoff) & (first >= pd.Timestamp("2011-01-01"))].index
    order_times = (ident.groupby(["CustomerID", "InvoiceNo"])["InvoiceDate"].min()
                   .reset_index().sort_values(["CustomerID", "InvoiceDate"]))
    second = order_times.groupby("CustomerID")["InvoiceDate"].apply(
        lambda s: s.iloc[1] if len(s) > 1 else pd.NaT)
    within90 = ((second.loc[eligible] - first.loc[eligible]).dt.days <= 90) & second.loc[eligible].notna()
    facts["repeat_within_90d_pct"] = float(100 * within90.mean())
    facts["repeat_within_90d_eligible"] = int(len(eligible))

    # New vs returning revenue by month (Jan-Nov 2011: first month is baseline-biased)
    first_month = cust.set_index("CustomerID")["first_order_month"]
    ident["first_order_month"] = ident["CustomerID"].map(first_month)
    ident["type"] = np.where(ident["first_order_month"] == ident["InvoiceMonth"], "New", "Returning")
    nvr = ident.pivot_table(index="InvoiceMonth", columns="type", values="Revenue",
                            aggfunc="sum", fill_value=0)
    nvr = nvr.loc[[m for m in full_months() if m != FIRST_FULL_MONTH]]
    nvr["returning_share_pct"] = 100 * nvr["Returning"] / (nvr["New"] + nvr["Returning"])
    return dist, facts, gaps, nvr.round(2).reset_index()


# --------------------------------------------------------------------------- #
# 9. Cohort retention
# --------------------------------------------------------------------------- #
def cohort_retention(sales, cust):
    months = full_months()
    keep = cust.loc[cust["in_rfm"], "CustomerID"]
    ident = sales[sales["CustomerID"].isin(keep) & sales["InvoiceMonth"].isin(months)]
    first_month = cust.set_index("CustomerID")["first_order_month"]
    act = ident[["CustomerID", "InvoiceMonth"]].drop_duplicates()
    act["cohort"] = act["CustomerID"].map(first_month)
    act = act[act["cohort"].isin(months)]
    idx = {m: i for i, m in enumerate(months)}
    act["age"] = act["InvoiceMonth"].map(idx) - act["cohort"].map(idx)

    counts = act.pivot_table(index="cohort", columns="age", values="CustomerID",
                             aggfunc="nunique").reindex(months)
    size = counts[0]
    ret = counts.div(size, axis=0) * 100
    # Blank cells that lie beyond the observation window
    for i, m in enumerate(months):
        ret.loc[m, [a for a in ret.columns if a > (len(months) - 1 - i)]] = np.nan
    ret.insert(0, "cohort_size", size.astype(int))

    # Weighted average retention by age, excluding the Dec-2010 cohort
    # (it mixes brand-new and pre-existing customers, so it is not a true cohort)
    true = [m for m in months if m != FIRST_FULL_MONTH]
    avg = {}
    for a in range(1, len(months)):
        elig = [m for m in true if idx[m] + a <= len(months) - 1]
        if elig:
            avg[a] = 100 * counts.loc[elig, a].sum() / counts.loc[elig, 0].sum()
    avg = pd.Series(avg, name="avg_retention_pct").round(2)
    return ret.round(2).reset_index(), avg.reset_index().rename(columns={"index": "months_since_first_order"})


# --------------------------------------------------------------------------- #
# 10. Returns
# --------------------------------------------------------------------------- #
def returns_analysis(sales, returns, prod):
    """Returns diagnostics, separating order-entry reversals from genuine returns."""
    r = returns
    rev_value = r.loc[r["is_reversal"], "ReturnValue"].sum()
    total_ret = r["ReturnValue"].sum()

    top_inv = (r.groupby("InvoiceNo").agg(return_value=("ReturnValue", "sum"),
                                          customer=("CustomerID", "first"),
                                          date=("InvoiceDate", "min"),
                                          reversal_lines=("is_reversal", "sum"),
                                          lines=("is_reversal", "size"))
               .sort_values("return_value", ascending=False).head(10).reset_index())
    top_inv["return_value"] = top_inv["return_value"].round(2)

    cols = ["StockCode", "description", "gross_revenue", "returns_value", "reversal_value",
            "return_rate_adj_pct"]
    genuine_base = prod[(prod["gross_revenue"] - prod["reversal_value"]) >= 5000]
    top_rr = genuine_base.sort_values("return_rate_adj_pct", ascending=False).head(10)[cols]
    genuine = prod.assign(genuine_returns=prod["returns_value"] - prod["reversal_value"])
    top_rv = genuine.sort_values("genuine_returns", ascending=False).head(10)[
        cols + ["genuine_returns"]]

    facts = {
        "return_lines": int(len(r)),
        "return_invoices": int(r["InvoiceNo"].nunique()),
        "reversal_lines": int(r["is_reversal"].sum()),
        "reversal_value": float(rev_value),
        "reversal_share_of_returns_pct": float(100 * rev_value / total_ret),
        "genuine_returns_value": float(total_ret - rev_value),
        "adjusted_return_rate_pct": float(100 * (total_ret - rev_value) / (sales["Revenue"].sum() - rev_value)),
        "top2_invoices_share_pct": float(100 * top_inv["return_value"].head(2).sum() / total_ret),
        "customers_with_returns": int(r["CustomerID"].nunique()),
        "returns_missing_customer_id_pct": float(100 * r["CustomerID"].isna().mean()),
    }
    return top_inv, _round(top_rr), _round(top_rv), facts


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def _clean_json(obj):
    if isinstance(obj, dict):
        return {k: _clean_json(v) for k, v in obj.items()}
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating, float)):
        return None if np.isnan(obj) else round(float(obj), 4)
    return obj


def run(save: bool = True):
    sales, returns = load_clean()
    returns["is_reversal"] = flag_reversals(sales, returns)
    T, F = {}, {}  # tables, fact dictionaries

    T["monthly"] = build_monthly(sales, returns)
    F["kpis"] = build_kpis(sales, returns, T["monthly"])
    F["seasonality"] = seasonality(T["monthly"])
    mm = T["monthly"][~T["monthly"]["is_partial_month"]]
    F["monthly_extra"] = {
        "worst_month_adj_return_rate_month": str(mm.loc[mm["return_rate_adj_pct"].idxmax(), "month"]),
        "worst_month_adj_return_rate_pct": float(mm["return_rate_adj_pct"].max()),
        "best_month_adj_return_rate_pct": float(mm["return_rate_adj_pct"].min()),
        "biggest_mom_gain_month": str(mm.loc[mm["net_revenue_mom_pct"].idxmax(), "month"]),
        "biggest_mom_gain_pct": float(mm["net_revenue_mom_pct"].max()),
        "biggest_mom_drop_month": str(mm.loc[mm["net_revenue_mom_pct"].idxmin(), "month"]),
        "biggest_mom_drop_pct": float(mm["net_revenue_mom_pct"].min()),
        "dec2011_net_revenue_partial": float(T["monthly"].iloc[-1]["net_revenue"]),
    }
    T["weekday"], T["hourly"] = time_patterns(sales)
    T["country"] = country_table(sales, returns)
    uk = T["country"].loc[T["country"]["Country"] == "United Kingdom"].iloc[0]
    intl = T["country"][T["country"]["Country"] != "United Kingdom"]
    F["geography"] = {
        "uk_share_pct": float(uk["share_of_net_pct"]),
        "international_share_pct": float(100 - uk["share_of_net_pct"]),
        "uk_aov": float(uk["aov"]),
        "uk_customers": int(uk["customers"]),
        "intl_customers": int(intl["customers"].sum()),
        "intl_aov": float(intl["gross_revenue"].sum() / intl["orders"].sum()),
        "intl_revenue_per_customer": float(intl["net_revenue"].sum() / intl["customers"].sum()),
        "uk_revenue_per_customer": float(uk["revenue_per_customer"]),
        "n_countries": int(len(T["country"])),
        "top3_intl_countries": T["country"][T["country"]["Country"] != "United Kingdom"]
                               .head(3)["Country"].tolist(),
    }
    big_intl = intl[intl["customers"] >= 20]
    F["geography"]["broad_markets"] = big_intl.head(5)["Country"].tolist()
    F["geography"]["broad_markets_rev_per_customer"] = float(
        big_intl["net_revenue"].sum() / big_intl["customers"].sum())
    F["geography"]["broad_markets_customers"] = int(big_intl["customers"].sum())
    top3 = intl.head(3)
    F["geography"]["top3_intl_customers"] = int(top3["customers"].sum())
    F["geography"]["top3_intl_share_pct"] = float(top3["share_of_net_pct"].sum())
    (T["products"], F["products"], T["product_heatmap"], T["seasonal_products"],
     T["christmas_share"]) = product_tables(sales, returns)
    T["customers"] = customer_table(sales, returns)
    T["rfm_summary"] = rfm_summary(T["customers"])
    (T["customer_deciles"], F["concentration"], T["top10_customers"],
     T["lorenz_curve"]) = concentration(T["customers"])
    T["orders_distribution"], F["repeat"], gaps, T["new_vs_returning"] = repeat_behaviour(
        sales, T["customers"])
    T["gaps_days"] = gaps.rename("days_between_orders").reset_index(drop=True).to_frame()
    T["cohort_retention"], T["avg_retention"] = cohort_retention(sales, T["customers"])
    (T["top_return_invoices"], T["top_return_rate_products"], T["top_return_value_products"],
     F["returns"]) = returns_analysis(sales, returns, T["products"])

    # RFM headline facts used in the report
    seg = T["rfm_summary"].set_index("segment")
    def seg_val(name, col):
        return float(seg.loc[name, col]) if name in seg.index else 0.0
    at_risk = ["At Risk", "Can't Lose Them", "Hibernating"]
    F["rfm"] = {
        "champions_pct_customers": seg_val("Champions", "pct_customers"),
        "champions_pct_revenue": seg_val("Champions", "pct_net_revenue"),
        "champions_customers": seg_val("Champions", "customers"),
        "loyal_pct_revenue": seg_val("Loyal Customers", "pct_net_revenue"),
        "at_risk_group_customers": float(sum(seg_val(s, "customers") for s in at_risk)),
        "at_risk_group_pct_customers": float(sum(seg_val(s, "pct_customers") for s in at_risk)),
        "at_risk_group_pct_revenue": float(sum(seg_val(s, "pct_net_revenue") for s in at_risk)),
        "at_risk_group_revenue": float(sum(seg_val(s, "net_revenue") for s in at_risk)),
        "cant_lose_customers": seg_val("Can't Lose Them", "customers"),
        "cant_lose_revenue": seg_val("Can't Lose Them", "net_revenue"),
        "cant_lose_pct_revenue": seg_val("Can't Lose Them", "pct_net_revenue"),
        "new_customers": seg_val("New Customers", "customers"),
        "hibernating_customers": seg_val("Hibernating", "customers"),
        "hibernating_pct_customers": seg_val("Hibernating", "pct_customers"),
        "hibernating_pct_revenue": seg_val("Hibernating", "pct_net_revenue"),
    }

    avg = T["avg_retention"].set_index("months_since_first_order")["avg_retention_pct"]
    F["retention"] = {
        "month1_pct": float(avg.get(1, np.nan)), "month3_pct": float(avg.get(3, np.nan)),
        "month6_pct": float(avg.get(6, np.nan)),
        "min_after_m1_pct": float(avg.loc[2:].min()) if len(avg) > 2 else None,
    }

    if save:
        OUT_TABLES.mkdir(parents=True, exist_ok=True)
        for name, df in T.items():
            df.to_csv(OUT_TABLES / f"{name}.csv", index=False)
        with open(OUT_TABLES / "kpis_and_facts.json", "w") as fh:
            json.dump(_clean_json(F), fh, indent=2)
    return sales, returns, T, F


if __name__ == "__main__":
    _, _, tables, facts = run()
    print(json.dumps(_clean_json(facts), indent=2))
    print("\nTables saved:", ", ".join(tables))
