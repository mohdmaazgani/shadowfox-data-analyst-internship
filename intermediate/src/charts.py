"""Step 3 - Visual reporting.

Builds every chart used in the report (outputs/charts/*.png) and a one-page
executive dashboard (dashboard/executive_dashboard.png).

All plotting functions take an `ax` so they can be reused both as standalone
charts and as panels of the dashboard.

Usage:  python src/charts.py
"""
import json
import string
import textwrap

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.patches import FancyBboxPatch

from analysis import SEGMENT_ORDER
from config import DASHBOARD, OUT_CHARTS, OUT_TABLES, PALETTE as C

# --------------------------------------------------------------------------- #
# Global style
# --------------------------------------------------------------------------- #
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.edgecolor": "#B8C2CC",
    "axes.labelcolor": C["dark"], "xtick.color": C["dark"], "ytick.color": C["dark"],
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
    "grid.color": "#E3E8ED", "grid.linewidth": 0.8, "axes.axisbelow": True,
    "figure.facecolor": "white", "axes.facecolor": "white", "savefig.dpi": 170,
    "axes.titleweight": "bold", "legend.frameon": False,
})

SEG_COLORS = {
    "Champions": "#1F4E79", "Loyal Customers": "#2E75B6", "Potential Loyalists": "#5FA8D3",
    "New Customers": "#7FC8A9", "Promising": "#A8D8B9", "Need Attention": "#F2C14E",
    "About to Sleep": "#F4A259", "At Risk": "#E4572E", "Can't Lose Them": "#B23A48",
    "Hibernating": "#5B6B7A",
}


def gbp(x, pos=None):
    if abs(x) >= 1e6:
        return f"£{x / 1e6:.1f}M"
    if abs(x) >= 1e3:
        return f"£{x / 1e3:.0f}k"
    return f"£{x:.0f}"


def nice(desc: str) -> str:
    """Title-case a product name without the "50'S" apostrophe problem."""
    return string.capwords(str(desc).lower())


def mlabel(months):
    return [pd.Period(m).strftime("%b-%y") for m in months]


def load_tables():
    T = {p.stem: pd.read_csv(p) for p in OUT_TABLES.glob("*.csv")}
    F = json.load(open(OUT_TABLES / "kpis_and_facts.json"))
    return T, F


def heading(ax, title, subtitle=None, size=13):
    ax.set_title(title, loc="left", fontsize=size, pad=24 if subtitle else 10, color=C["dark"])
    if subtitle:
        ax.text(0, 1.035, subtitle, transform=ax.transAxes, fontsize=9, color="#5B6B7A",
                va="bottom")


def save(fig, name, folder=OUT_CHARTS):
    folder.mkdir(parents=True, exist_ok=True)
    fig.savefig(folder / name, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print("  saved", folder.name + "/" + name)


# --------------------------------------------------------------------------- #
# Panels
# --------------------------------------------------------------------------- #
def draw_monthly(ax, T, F, compact=False):
    m = T["monthly"]
    x = np.arange(len(m))
    colors = [C["muted"] if p else C["primary"] for p in m["is_partial_month"]]
    bars = ax.bar(x, m["net_revenue"], color=colors, width=0.72, zorder=3)
    bars[-1].set_hatch("///")
    bars[-1].set_edgecolor("white")
    avg = F["seasonality"]["jan_aug_avg_monthly"]
    ax.axhline(avg, color=C["accent"], ls="--", lw=1.4, zorder=4,
               label=f"Jan-Aug 2011 monthly average: {gbp(avg)}")
    ax.legend(loc="upper left", fontsize=8.5 if compact else 9.5)
    top = m["net_revenue"].max()
    for xi, v, p in zip(x, m["net_revenue"], m["is_partial_month"]):
        if compact and not p and xi % 1 == 0:
            ax.text(xi, v + top * 0.012, f"{v / 1e3:,.0f}", ha="center", fontsize=7, color=C["dark"])
        elif not compact and not p:
            ax.text(xi, v + top * 0.012, f"£{v / 1e3:,.0f}k", ha="center", fontsize=8.5, color=C["dark"])
    pv = m.iloc[-1]["net_revenue"]
    ax.text(len(m) - 1, pv + top * 0.012, f"£{pv / 1e3:,.0f}k\n(partial, to 9 Dec)", ha="center",
            fontsize=7.5 if compact else 8.5, color="#5B6B7A", va="bottom")
    pk = int(m["net_revenue"].idxmax())
    ax.annotate(f"Peak: £{m.loc[pk, 'net_revenue'] / 1e6:.2f}M\n+{F['seasonality']['nov_vs_oct_pct']:.0f}% vs Oct",
                xy=(pk - 0.35, m.loc[pk, "net_revenue"] * 0.97),
                xytext=(pk - 3.3, m.loc[pk, "net_revenue"] * 0.93),
                fontsize=9.5, fontweight="bold", color=C["primary"], ha="center",
                arrowprops=dict(arrowstyle="->", color=C["primary"]))
    ax.set_xticks(x)
    ax.set_xticklabels(mlabel(m["month"]), rotation=45 if not compact else 60, ha="right")
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(gbp))
    ax.grid(axis="x", visible=False)
    ax.set_ylim(0, top * 1.18)


def draw_rfm(ax, T, F, compact=False):
    s = T["rfm_summary"].set_index("segment").reindex(SEGMENT_ORDER)[::-1]
    y = np.arange(len(s))
    h = 0.38
    ax.barh(y + h / 2, s["pct_customers"], h, color="#C9D1D9", label="% of customers", zorder=3)
    ax.barh(y - h / 2, s["pct_net_revenue"], h, color=[SEG_COLORS[i] for i in s.index],
            label="% of net revenue", zorder=3)
    for yi, (pc, pr) in enumerate(zip(s["pct_customers"], s["pct_net_revenue"])):
        fmt = (lambda v: f"{v:.1f}%" if v < 1 else f"{v:.0f}%")
        ax.text(pc + 0.6, yi + h / 2, fmt(pc), va="center", fontsize=8, color="#5B6B7A")
        ax.text(pr + 0.6, yi - h / 2, fmt(pr), va="center", fontsize=8.5, fontweight="bold",
                color=C["dark"])
    ax.set_yticks(y)
    ax.set_yticklabels(s.index, fontsize=9)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, max(s["pct_net_revenue"].max(), s["pct_customers"].max()) * 1.15)
    handles = [plt.Rectangle((0, 0), 1, 1, color="#C9D1D9"),
               plt.Rectangle((0, 0), 1, 1, color=C["primary"])]
    ax.legend(handles, ["% of customers", "% of net revenue (colour = segment)"],
              loc="center right", fontsize=8.5)


def draw_concentration(ax, T, F, compact=False):
    lc = T["lorenz_curve"]
    ax.plot(lc["pct_customers"], lc["cum_revenue_pct"], color=C["primary"], lw=2.6, zorder=3)
    ax.fill_between(lc["pct_customers"], lc["cum_revenue_pct"], color=C["primary"], alpha=0.08)
    ax.plot([0, 100], [0, 100], color=C["muted"], ls="--", lw=1, label="Perfect equality")
    k = F["concentration"]
    for pct, key in [(1, "top1pct_share"), (10, "top10pct_share"), (20, "top20pct_share")]:
        v = k[key]
        ax.scatter([pct], [v], color=C["accent"], zorder=5, s=36)
        ax.annotate(f"Top {pct}% of customers\n= {v:.0f}% of revenue", xy=(pct, v),
                    xytext=(pct + 9, v - 12 if pct != 1 else v - 18), fontsize=8.5,
                    fontweight="bold", color=C["dark"],
                    arrowprops=dict(arrowstyle="-", color=C["muted"]))
    ax.set_xlabel("Customers ranked by net revenue (cumulative %)")
    ax.set_ylabel("Cumulative % of net revenue")
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 102)


def draw_country(ax, T, F, compact=False, n=8):
    c = T["country"]
    c = c[c["Country"] != "United Kingdom"].head(n)[::-1]
    y = np.arange(len(c))
    colors = [C["accent"] if v >= 50 else C["primary"] for v in c["top_customer_share_pct"]]
    ax.barh(y, c["net_revenue"], color=colors, zorder=3, height=0.66)
    for yi, (v, cu, ts) in enumerate(zip(c["net_revenue"], c["customers"], c["top_customer_share_pct"])):
        ax.text(v + 4000, yi, f"{gbp(v)}  |  {cu} cust.  |  top acct {ts:.0f}%", va="center",
                fontsize=8 if compact else 8.5, color=C["dark"])
    ax.set_yticks(y)
    ax.set_yticklabels(c["Country"])
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(gbp))
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, c["net_revenue"].max() * 1.75)
    if not compact:
        handles = [plt.Rectangle((0, 0), 1, 1, color=C["primary"]),
                   plt.Rectangle((0, 0), 1, 1, color=C["accent"])]
        ax.legend(handles, ["Broad customer base", "Depends on a few accounts (top account \u2265 50% of sales)"],
                  loc="lower right", fontsize=8.5)


# --------------------------------------------------------------------------- #
# Standalone charts
# --------------------------------------------------------------------------- #
def chart_monthly(T, F):
    fig, ax = plt.subplots(figsize=(11, 5.2))
    draw_monthly(ax, T, F)
    s = F["seasonality"]
    heading(ax, "Net revenue by month: a strong autumn peak",
            f"Sep-Nov generated {s['sep_nov_share_pct']:.0f}% of full-year net revenue (25% would be flat). "
            "Dec-11 is incomplete and not comparable.")
    save(fig, "01_monthly_net_revenue.png")


def chart_drivers(T, F):
    m = T["monthly"]
    m = m[~m["is_partial_month"]].reset_index(drop=True)
    x = np.arange(len(m))
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.3))
    for ax, col, ttl, col_c in [
        (axes[0], "orders", "Orders per month", C["primary"]),
        (axes[1], "active_customers", "Active customers per month", C["secondary"]),
        (axes[2], "aov", "Average order value (AOV)", C["accent"]),
    ]:
        ax.plot(x, m[col], marker="o", color=col_c, lw=2.4, zorder=3)
        ax.set_xticks(x)
        ax.set_xticklabels(mlabel(m["month"]), rotation=60, ha="right", fontsize=8)
        ax.set_title(ttl, loc="left", fontsize=11)
        ax.grid(axis="x", visible=False)
        base = m.loc[m["month"].between("2011-01", "2011-08"), col].mean()
        ax.axhline(base, color=C["muted"], ls="--", lw=1.1, label="Jan-Aug 2011 average")
        ax.legend(loc="lower right", fontsize=8.5)
        if col == "aov":
            ax.yaxis.set_major_formatter(mtick.FuncFormatter(gbp))
            ax.set_ylim(0, m[col].max() * 1.25)
        else:
            ax.set_ylim(0, m[col].max() * 1.2)
        ax.annotate(f"{m[col].iloc[-1]:,.0f}" if col != "aov" else gbp(m[col].iloc[-1]),
                    xy=(x[-1], m[col].iloc[-1]), xytext=(-8, 8), textcoords="offset points",
                    fontsize=9, fontweight="bold", ha="right")
    s = F["seasonality"]
    fig.suptitle(
        f"What drove the November peak? More orders ({s['nov_orders_vs_jan_aug_x']:.1f}x) from more "
        f"customers ({s['nov_customers_vs_jan_aug_x']:.1f}x), not bigger baskets "
        f"(AOV only {100 * (s['nov_aov_vs_jan_aug_x'] - 1):+.0f}%)",
        x=0.01, ha="left", fontsize=12.5, fontweight="bold", y=1.03)
    fig.tight_layout()
    save(fig, "02_growth_drivers.png")


def chart_time(T, F):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.4), gridspec_kw={"width_ratios": [1, 1.25]})
    wd = T["weekday"]
    ax = axes[0]
    cols = [C["primary"] if v > 0 else C["muted"] for v in wd["share_pct"]]
    ax.bar([d[:3] for d in wd["Weekday"]], wd["share_pct"], color=cols, zorder=3)
    for i, v in enumerate(wd["share_pct"]):
        ax.text(i, v + 0.4, f"{v:.0f}%" if v > 0 else "no\ntrading", ha="center", fontsize=9,
                fontweight="bold" if v > 0 else "normal", color=C["dark"] if v > 0 else "#5B6B7A")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.grid(axis="x", visible=False)
    ax.set_ylim(0, wd["share_pct"].max() * 1.2)
    heading(ax, "Share of revenue by weekday", "No orders recorded on Saturdays; Sunday is the weakest day",
            size=11.5)
    hr = T["hourly"]
    hr = hr[(hr["Hour"] >= 7) & (hr["Hour"] <= 20)]
    ax = axes[1]
    peak = hr["Hour"].between(10, 15)
    ax.bar(hr["Hour"], hr["share_pct"], color=[C["primary"] if p else C["secondary"] for p in peak],
           zorder=3, alpha=0.95)
    share = hr.loc[peak, "share_pct"].sum()
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_xticks(hr["Hour"])
    ax.set_xticklabels([f"{h}h" for h in hr["Hour"]])
    ax.grid(axis="x", visible=False)
    heading(ax, "Share of revenue by hour of day",
            f"10:00-15:59 accounts for {share:.0f}% of revenue (dark bars)", size=11.5)
    fig.tight_layout()
    save(fig, "03_weekday_hour_patterns.png")


def chart_country(T, F):
    fig, ax = plt.subplots(figsize=(11, 4.8))
    draw_country(ax, T, F)
    g = F["geography"]
    heading(ax, "International revenue: three of the top five markets hinge on a handful of accounts",
            f"UK = {g['uk_share_pct']:.1f}% of net revenue. Netherlands, EIRE and Australia are each driven "
            "by 1-2 large accounts; Germany and France are broad-based.")
    save(fig, "04_country_performance.png")


def chart_products(T, F):
    p = T["products"].head(10)[::-1]
    fig, ax = plt.subplots(figsize=(11, 4.9))
    labels = [textwrap.shorten(nice(d), 34, placeholder="...") for d in p["description"]]
    ax.barh(labels, p["net_revenue"], color=C["primary"], zorder=3, height=0.68)
    for i, (v, cu) in enumerate(zip(p["net_revenue"], p["customers"])):
        ax.text(v + 1800, i, f"{gbp(v)}  ({cu} customers)", va="center", fontsize=8.8)
    ax.xaxis.set_major_formatter(mtick.FuncFormatter(gbp))
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, p["net_revenue"].max() * 1.3)
    heading(ax, "Top 10 products by net revenue",
            f"Together only {F['products']['top10_share_pct']:.1f}% of revenue: a long-tail range with no single-product dependency")
    save(fig, "05_top_products.png")


def chart_pareto(T, F):
    p = T["products"]
    p = p[p["net_revenue"] > 0].reset_index(drop=True)
    x = 100 * (np.arange(1, len(p) + 1) / len(p))
    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    ax.plot(x, p["cum_share_pct"], color=C["primary"], lw=2.6)
    ax.fill_between(x, p["cum_share_pct"], color=C["primary"], alpha=0.08)
    f = F["products"]
    xp = f["products_for_80pct_share_of_range_pct"]
    ax.plot([xp, xp], [0, 80], color=C["accent"], ls="--")
    ax.plot([0, xp], [80, 80], color=C["accent"], ls="--")
    ax.scatter([xp], [80], color=C["accent"], zorder=5)
    ax.annotate(f"{f['products_for_80pct_revenue']:,} products ({xp:.0f}% of range)\ngenerate 80% of revenue",
                xy=(xp, 80), xytext=(xp + 14, 58), fontsize=9.5, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=C["accent"]))
    ax.text(58, 22, f"Bottom 50% of products\n= only {f['bottom50pct_products_share_pct']:.1f}% of revenue",
            fontsize=9.5, fontweight="bold", color=C["dark"])
    ax.set_xlabel("Products ranked by net revenue (cumulative % of range)")
    ax.set_ylabel("Cumulative % of net revenue")
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 102)
    heading(ax, "Product revenue follows a classic 80/20 (Pareto) pattern",
            f"{f['products_with_positive_net']:,} products sold in total")
    save(fig, "06_product_pareto.png")


def chart_seasonality(T, F):
    h = T["product_heatmap"].set_index("Description")
    norm = h.div(h.max(axis=1), axis=0)
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.9), gridspec_kw={"width_ratios": [1.7, 1]})
    ax = axes[0]
    ylabels = [textwrap.shorten(nice(d), 32, placeholder="...") for d in norm.index]
    sns.heatmap(norm, ax=ax, cmap="Blues", cbar_kws={"label": "Monthly revenue as % of product's peak month",
                                                    "format": mtick.PercentFormatter(1, decimals=0)},
                xticklabels=mlabel(norm.columns), yticklabels=ylabels, linewidths=0.6,
                linecolor="white", vmin=0, vmax=1)
    ax.tick_params(axis="x", rotation=45, labelsize=8.5)
    ax.tick_params(axis="y", rotation=0, labelsize=8.5)
    ax.grid(False)
    ax.set_xlabel("")
    ax.set_ylabel("")
    heading(ax, "Top-10 products: who is seasonal, who is evergreen?",
            "Each row scaled to its own peak month", size=11.5)
    ax = axes[1]
    xm = T["christmas_share"]
    ax.bar(mlabel(xm["InvoiceMonth"]), xm["christmas_themed_share_pct"], color=C["accent"], zorder=3)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.tick_params(axis="x", rotation=60, labelsize=8.5)
    ax.grid(axis="x", visible=False)
    heading(ax, "Christmas-themed share of revenue",
            "keyword match on product name (Christmas, Xmas, Santa...)", size=11.5)
    fig.tight_layout()
    save(fig, "07_product_seasonality.png")


def chart_concentration(T, F):
    d = T["customer_deciles"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    ax = axes[0]
    cols = [C["primary"] if i == 1 else C["secondary"] for i in d["decile"]]
    ax.bar(d["decile"].astype(str), d["share_pct"], color=cols, zorder=3)
    for i, v in zip(d["decile"], d["share_pct"]):
        ax.text(i - 1, v + 0.9, f"{v:.0f}%", ha="center", fontsize=9, fontweight="bold")
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.set_xlabel("Customer decile (1 = top 10% of customers by net revenue)")
    ax.grid(axis="x", visible=False)
    ax.set_ylim(0, d["share_pct"].max() * 1.15)
    heading(ax, "Share of net revenue by customer decile", size=11.5)
    draw_concentration(axes[1], T, F)
    heading(axes[1], "Revenue concentration curve", size=11.5)
    k = F["concentration"]
    fig.suptitle(f"A small core of customers drives the business: top 10% = {k['top10pct_share']:.0f}% "
                 f"of revenue, bottom 50% = {k['bottom50pct_share']:.0f}%", x=0.01, ha="left",
                 fontsize=12.5, fontweight="bold", y=1.03)
    fig.tight_layout()
    save(fig, "08_customer_concentration.png")


def chart_rfm(T, F):
    fig, ax = plt.subplots(figsize=(11, 5.4))
    draw_rfm(ax, T, F)
    r = F["rfm"]
    heading(ax, "RFM segments: customers vs. revenue",
            f"Champions are {r['champions_pct_customers']:.0f}% of customers but {r['champions_pct_revenue']:.0f}% of revenue; "
            f"At Risk / Can't Lose / Hibernating = {r['at_risk_group_pct_customers']:.0f}% of customers, "
            f"{r['at_risk_group_pct_revenue']:.0f}% of revenue")
    save(fig, "09_rfm_segments.png")


def chart_repeat(T, F):
    o = T["orders_distribution"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.6), gridspec_kw={"width_ratios": [1.4, 1]})
    ax = axes[0]
    x = np.arange(len(o))
    w = 0.38
    ax.bar(x - w / 2, o["pct_customers"], w, color=C["muted"], label="% of customers", zorder=3)
    ax.bar(x + w / 2, o["pct_net_revenue"], w, color=C["primary"], label="% of net revenue", zorder=3)
    for xi, (a, b) in enumerate(zip(o["pct_customers"], o["pct_net_revenue"])):
        ax.text(xi - w / 2, a + 0.8, f"{a:.0f}%", ha="center", fontsize=8.5, color="#5B6B7A")
        ax.text(xi + w / 2, b + 0.8, f"{b:.0f}%", ha="center", fontsize=8.5, fontweight="bold")
    ax.set_xticks(x)
    ax.set_xticklabels(o["orders_band"])
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper center", fontsize=9)
    ax.set_ylim(0, max(o["pct_customers"].max(), o["pct_net_revenue"].max()) * 1.18)
    heading(ax, "Orders per customer", size=11.5)
    ax = axes[1]
    g = T["gaps_days"]["days_between_orders"]
    ax.hist(g[g <= 120], bins=np.arange(0, 125, 7), color=C["secondary"], edgecolor="white", zorder=3)
    med = F["repeat"]["median_days_between_orders"]
    ax.axvline(med, color=C["accent"], ls="--", lw=1.8)
    ax.text(med + 2, ax.get_ylim()[1] * 0.88, f"Median = {med:.0f} days", color=C["accent"],
            fontsize=9.5, fontweight="bold")
    ax.set_xlabel("Days between a customer's shopping days (capped at 120)")
    ax.set_ylabel("Number of order gaps")
    ax.grid(axis="x", visible=False)
    heading(ax, "Purchase cycle of repeat customers", size=11.5)
    rp = F["repeat"]
    fig.suptitle(f"{rp['repeat_customer_rate_pct']:.0f}% of customers buy again, and they generate "
                 f"{rp['repeat_revenue_share_pct']:.0f}% of revenue", x=0.01, ha="left", fontsize=12.5,
                 fontweight="bold", y=1.03)
    fig.tight_layout()
    save(fig, "10_repeat_behaviour.png")


def chart_cohort(T, F):
    ret = T["cohort_retention"].copy()
    ret = ret[~ret["cohort"].isin(["2010-12", "2011-11"])]  # Dec-10 = mixed; Nov-11 has no follow-up
    lab = [f"{pd.Period(c).strftime('%b-%y')}  (n={n})" for c, n in zip(ret["cohort"], ret["cohort_size"])]
    mat = ret.drop(columns=["cohort", "cohort_size", "0"])
    mat.columns = [int(c) for c in mat.columns]
    mat = mat.dropna(axis=1, how="all")
    fig, ax = plt.subplots(figsize=(11.5, 5.6))
    sns.heatmap(mat.astype(float), annot=True, fmt=".0f", cmap="YlGnBu", ax=ax, linewidths=0.6,
                linecolor="white", yticklabels=lab, vmin=10, vmax=40, annot_kws={"fontsize": 8.5},
                cbar_kws={"label": "% of cohort placing an order that month",
                          "format": mtick.PercentFormatter(decimals=0)})
    ax.set_xlabel("Months since customer's first order")
    ax.set_ylabel("")
    ax.grid(False)
    ax.tick_params(axis="y", rotation=0)
    avg = T["avg_retention"].set_index("months_since_first_order")["avg_retention_pct"]
    plateau = avg.loc[2:7]
    ax.set_title("Cohort retention: about 1 in 5 new customers returns the next month", loc="left",
                 fontsize=13, pad=36, color=C["dark"])
    ax.text(0, 1.02,
            f"Avg. month-1 retention {avg.loc[1]:.0f}%; months 2-7 hold at {plateau.min():.0f}-{plateau.max():.0f}% "
            "(no steady decay); the lift after month 7 coincides with the Sep-Nov peak.\n"
            "Dec-10 cohort excluded (mixes existing customers); Nov-11 has no follow-up yet.",
            transform=ax.transAxes, fontsize=9, color="#5B6B7A", va="bottom")
    save(fig, "11_cohort_retention.png")


def chart_new_returning(T, F):
    n = T["new_vs_returning"]
    fig, ax = plt.subplots(figsize=(11, 4.8))
    x = np.arange(len(n))
    ax.bar(x, n["Returning"], color=C["primary"], label="Returning customers", zorder=3)
    ax.bar(x, n["New"], bottom=n["Returning"], color=C["positive"], label="New customers (first order in data)",
           zorder=3)
    for xi, (r, nn, sh) in enumerate(zip(n["Returning"], n["New"], n["returning_share_pct"])):
        ax.text(xi, r + nn + 15000, f"{sh:.0f}%", ha="center", fontsize=9, fontweight="bold",
                color=C["primary"])
    ax.set_xticks(x)
    ax.set_xticklabels(mlabel(n["InvoiceMonth"]))
    ax.yaxis.set_major_formatter(mtick.FuncFormatter(gbp))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper left")
    ax.set_ylim(0, (n["Returning"] + n["New"]).max() * 1.15)
    heading(ax, "Gross sales from new vs. returning customers (customers with a customer ID)",
            "Labels = returning share. Early-2011 'new' is overstated: the data starts Dec-10, "
            "so some 'new' customers are pre-existing.")
    save(fig, "12_new_vs_returning.png")


def chart_returns(T, F):
    m = T["monthly"]
    m = m[~m["is_partial_month"]].reset_index(drop=True)
    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8), gridspec_kw={"width_ratios": [1.2, 1]})
    ax = axes[0]
    x = np.arange(len(m))
    ax.bar(x, m["return_rate_pct"], color=C["muted"], label="Reported return rate", zorder=3, width=0.7)
    ax.plot(x, m["return_rate_adj_pct"], color=C["accent"], marker="o", lw=2.4,
            label="Adjusted (excl. same-day order reversals)", zorder=4)
    ax.set_xticks(x)
    ax.set_xticklabels(mlabel(m["month"]), rotation=60, ha="right", fontsize=8.5)
    ax.yaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.grid(axis="x", visible=False)
    ax.legend(loc="upper right", fontsize=8.5)
    apr = int(m.index[m["month"] == "2011-04"][0])
    ax.annotate("Apr-11: one customer returned £23k\n(invoice C550456), a genuine return",
                xy=(apr, m.loc[apr, "return_rate_adj_pct"]), xytext=(apr + 1.1, 9.2), fontsize=8.5,
                fontweight="bold", color=C["accent"], arrowprops=dict(arrowstyle="->", color=C["accent"]))
    heading(ax, "Monthly return rate (returns / gross revenue)",
            "Jan-11 spike = one £77k order cancelled minutes after being placed", size=11.5)
    ax = axes[1]
    t = T["top_return_rate_products"].head(8)[::-1]
    labels = [textwrap.shorten(nice(d), 30, placeholder="...") for d in t["description"]]
    ax.barh(labels, t["return_rate_adj_pct"], color=C["accent"], zorder=3, height=0.65)
    for i, (v, g) in enumerate(zip(t["return_rate_adj_pct"], t["gross_revenue"])):
        ax.text(v + 0.6, i, f"{v:.0f}%  (of {gbp(g)} sold)", va="center", fontsize=8.5)
    ax.xaxis.set_major_formatter(mtick.PercentFormatter(decimals=0))
    ax.grid(axis="y", visible=False)
    ax.set_xlim(0, t["return_rate_adj_pct"].max() * 1.6)
    heading(ax, "Highest genuine return rates", "products with >= £5k sales", size=11.5)
    fig.tight_layout()
    save(fig, "13_returns.png")


# --------------------------------------------------------------------------- #
# Executive dashboard (one page)
# --------------------------------------------------------------------------- #
def kpi_tile(fig, rect, value, label, sub, color):
    ax = fig.add_axes(rect)
    ax.axis("off")
    ax.add_patch(FancyBboxPatch((0.0, 0.0), 1, 1, boxstyle="round,pad=0,rounding_size=0.06",
                                fc=C["light"], ec="none", transform=ax.transAxes))
    ax.add_patch(plt.Rectangle((0, 0.0), 0.022, 1, fc=color, ec="none", transform=ax.transAxes))
    ax.text(0.09, 0.66, value, fontsize=24, fontweight="bold", color=C["dark"], transform=ax.transAxes)
    ax.text(0.09, 0.38, label, fontsize=11.5, fontweight="bold", color="#3B4B5A", transform=ax.transAxes)
    ax.text(0.09, 0.14, sub, fontsize=9, color="#6B7A88", transform=ax.transAxes)


def dashboard(T, F):
    K = F["kpis"]
    fig = plt.figure(figsize=(20, 12.6))
    fig.text(0.03, 0.965, "Online Retail | Customer & Revenue Performance Dashboard", fontsize=26,
             fontweight="bold", color=C["dark"])
    fig.text(0.03, 0.937, f"UK-based online gift wholesaler  |  {K['date_start']} to {K['date_end']}  |  "
             "541,909 raw transaction lines cleaned to 522,568 sales lines  |  Source: UCI Online Retail dataset",
             fontsize=11.5, color="#5B6B7A")
    tiles = [
        (f"£{K['net_revenue'] / 1e6:.2f}M", "Net revenue", f"gross £{K['gross_revenue'] / 1e6:.2f}M - returns £{K['returns_value'] / 1e3:.0f}k", C["primary"]),
        (f"{K['orders']:,}", "Orders", f"{K['units_per_order']:.0f} units per order", C["secondary"]),
        (f"{K['customers']:,}", "Identified customers", f"{K['pct_revenue_identified_customers']:.0f}% of revenue has a customer ID", C["secondary"]),
        (f"£{K['aov']:,.0f}", "Avg order value", "wholesale-sized baskets", C["positive"]),
        (f"{F['repeat']['repeat_customer_rate_pct']:.0f}%", "Repeat customers", f"they drive {F['repeat']['repeat_revenue_share_pct']:.0f}% of revenue", C["positive"]),
        (f"{F['returns']['adjusted_return_rate_pct']:.1f}%", "Genuine return rate", f"{K['return_rate_pct']:.1f}% before removing order reversals", C["accent"]),
    ]
    left, w, gap, top, h = 0.03, 0.148, 0.0124, 0.79, 0.115
    for i, (v, l, s, c) in enumerate(tiles):
        kpi_tile(fig, [left + i * (w + gap), top, w, h], v, l, s, c)

    # Row 2
    ax1 = fig.add_axes([0.045, 0.485, 0.50, 0.255])
    draw_monthly(ax1, T, F, compact=True)
    heading(ax1, "Net revenue by month", f"Sep-Nov = {F['seasonality']['sep_nov_share_pct']:.0f}% of the year (vs 25% if flat)")
    ax2 = fig.add_axes([0.66, 0.485, 0.32, 0.255])
    draw_rfm(ax2, T, F, compact=True)
    heading(ax2, "RFM segments: customers vs. revenue", "Champions = 14% of customers, 50% of revenue")

    # Row 3
    ax3 = fig.add_axes([0.045, 0.065, 0.24, 0.27])
    draw_concentration(ax3, T, F, compact=True)
    heading(ax3, "Revenue concentration", "a small core carries the business")
    ax4 = fig.add_axes([0.375, 0.065, 0.25, 0.27])
    draw_country(ax4, T, F, compact=True, n=6)
    heading(ax4, "Top international markets",
            f"UK = {F['geography']['uk_share_pct']:.0f}% of net revenue. Orange = rides on 1-2 accounts")

    # Insights box
    axi = fig.add_axes([0.685, 0.05, 0.305, 0.32])
    axi.axis("off")
    axi.add_patch(FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0,rounding_size=0.03", fc=C["light"],
                                 ec="none", transform=axi.transAxes))
    r, s, rt = F["rfm"], F["seasonality"], F["retention"]
    lines = [
        ("KEY INSIGHTS & ACTIONS", True),
        (f"1. Protect the core: {r['champions_customers']:.0f} Champions bring {r['champions_pct_revenue']:.0f}% of revenue "
         "-> account management & loyalty tiers.", False),
        (f"2. Win back {r['at_risk_group_customers']:,.0f} lapsing customers ({gbp(r['at_risk_group_revenue'])} "
         f"historic revenue), starting with {r['cant_lose_customers']:.0f} 'Can't Lose' accounts.", False),
        (f"3. Only {rt['month1_pct']:.0f}% of new customers reorder next month -> "
         "run a 2nd-order campaign inside 4 weeks (median cycle = 28 days).", False),
        (f"4. Plan for autumn: Nov is {s['nov_vs_jan_aug_avg_x']:.1f}x the Jan-Aug average. Stock & staff "
         "from Sep; use Jan-Feb for promotions.", False),
        ("5. Grow Germany & France (broad bases); treat NL/EIRE/Australia as key-account risk.", False),
    ]
    yy = 0.94
    for txt, head in lines:
        wrapped = textwrap.fill(txt, 58)
        axi.text(0.04, yy, wrapped, fontsize=14 if head else 11.8, fontweight="bold" if head else "normal",
                 color=C["primary"] if head else C["dark"], va="top", transform=axi.transAxes)
        yy -= (wrapped.count("\n") + 1) * 0.056 + 0.04
    save(fig, "executive_dashboard.png", folder=DASHBOARD)


def main() -> None:
    T, F = load_tables()
    print("Building charts ...")
    for fn in (chart_monthly, chart_drivers, chart_time, chart_country, chart_products, chart_pareto,
               chart_seasonality, chart_concentration, chart_rfm, chart_repeat, chart_cohort,
               chart_new_returning, chart_returns, dashboard):
        fn(T, F)


if __name__ == "__main__":
    main()
