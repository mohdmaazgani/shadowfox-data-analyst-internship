"""Step 4 - Build the final PDF report.

Assembles the narrative report (reports/Intermediate_Level_Customer_Revenue_Analysis.pdf)
from the tables/facts produced by analysis.py and the charts produced by charts.py.

Usage:  python src/report.py
"""
import json
import string

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image, KeepTogether, ListFlowable, ListItem, PageBreak, Paragraph,
    SimpleDocTemplate, Spacer, Table, TableStyle,
)

from config import AUTHOR, OUT_CHARTS, OUT_TABLES, PALETTE as C, REPORTS

F = json.load(open(OUT_TABLES / "kpis_and_facts.json"))
PRIMARY = colors.HexColor(C["primary"])
ACCENT = colors.HexColor(C["accent"])
DARK = colors.HexColor(C["dark"])
MUTED = colors.HexColor("#5B6B7A")
LIGHT = colors.HexColor(C["light"])

styles = getSampleStyleSheet()
styles.add(ParagraphStyle("CoverSub", fontSize=13.5, leading=18, textColor=MUTED, spaceAfter=4))
styles.add(ParagraphStyle("H1", fontSize=17, leading=21, fontName="Helvetica-Bold", textColor=PRIMARY,
                          spaceBefore=4, spaceAfter=10))
styles.add(ParagraphStyle("H2", fontSize=12.5, leading=16, fontName="Helvetica-Bold", textColor=DARK,
                          spaceBefore=12, spaceAfter=6))
styles.add(ParagraphStyle("Body", fontSize=10, leading=14.5, textColor=DARK, alignment=TA_LEFT,
                          spaceAfter=7))
styles.add(ParagraphStyle("Caption", fontSize=8.7, leading=11.5, textColor=MUTED, spaceAfter=14,
                          alignment=TA_LEFT))
styles.add(ParagraphStyle("KPIVal", fontSize=17, leading=19, fontName="Helvetica-Bold", textColor=PRIMARY))
styles.add(ParagraphStyle("KPILabel", fontSize=8.7, leading=11, textColor=MUTED))
styles.add(ParagraphStyle("RecTitle", fontSize=11, leading=14, fontName="Helvetica-Bold", textColor=colors.white))
styles.add(ParagraphStyle("RecBody", fontSize=9.6, leading=13.3, textColor=colors.white))
styles.add(ParagraphStyle("TblHead", fontSize=8.7, leading=11, fontName="Helvetica-Bold", textColor=colors.white))
styles.add(ParagraphStyle("TblCell", fontSize=8.7, leading=11, textColor=DARK))

PAGE_W, PAGE_H = A4
CONTENT_W = PAGE_W - 2 * 2.0 * cm


def p(text, style="Body"):
    return Paragraph(text, styles[style])


def img(name, width=CONTENT_W, caption=None):
    from PIL import Image as PILImage
    path = OUT_CHARTS / name
    with PILImage.open(path) as im:
        ratio = im.height / im.width
    elems = [Image(str(path), width=width, height=width * ratio)]
    if caption:
        elems.append(Spacer(1, 3))
        elems.append(p(caption, "Caption"))
    return elems


def kpi_row(items):
    """items: list of (value, label) tuples -> a row of KPI boxes."""
    n = len(items)
    w = CONTENT_W / n
    cells = []
    for v, l in items:
        cells.append([p(v, "KPIVal"), p(l, "KPILabel")])
    t = Table([cells], colWidths=[w] * n)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHT),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LINEAFTER", (0, 0), (-2, 0), 0.6, colors.white),
    ]))
    return t


def data_table(headers, rows, col_widths, align=None):
    tbl_data = [[Paragraph(h, styles["TblHead"]) for h in headers]]
    for r in rows:
        tbl_data.append([Paragraph(str(c), styles["TblCell"]) for c in r])
    t = Table(tbl_data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), PRIMARY),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F6F9")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D8E0E8")),
        ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]
    if align:
        for col, a in align.items():
            style.append(("ALIGN", (col, 0), (col, -1), a))
    t.setStyle(TableStyle(style))
    return t


def recommendation_box(num, title, body):
    inner = Table([[p(f"{num}. {title}", "RecTitle")], [p(body, "RecBody")]],
                 colWidths=[CONTENT_W - 0.6 * cm])
    inner.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), PRIMARY), ("TOPPADDING", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 10), ("LEFTPADDING", (0, 0), (-1, -1), 12),
        ("RIGHTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 1), (-1, 1), 3),
    ]))
    return inner


def bullets(items):
    return ListFlowable([ListItem(p(t, "Body"), leftIndent=2, spaceAfter=4) for t in items],
                        bulletType="bullet", start="\u2022", leftIndent=14)


def header_footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(colors.HexColor("#D8E0E8"))
    canvas.setLineWidth(0.6)
    canvas.line(2 * cm, PAGE_H - 1.55 * cm, PAGE_W - 2 * cm, PAGE_H - 1.55 * cm)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    canvas.drawString(2 * cm, PAGE_H - 1.35 * cm, "Online Retail | Customer & Revenue Performance Analysis")
    canvas.drawRightString(PAGE_W - 2 * cm, PAGE_H - 1.35 * cm,
                           "Intermediate Level - ShadowFox Data Analyst Internship")
    canvas.line(2 * cm, 1.5 * cm, PAGE_W - 2 * cm, 1.5 * cm)
    canvas.drawString(2 * cm, 1.15 * cm, "Source: UCI Machine Learning Repository - Online Retail dataset (CC BY 4.0)")
    canvas.drawRightString(PAGE_W - 2 * cm, 1.15 * cm, f"Page {doc.page}")
    canvas.restoreState()


def cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(PRIMARY)
    canvas.rect(0, PAGE_H - 6.4 * cm, PAGE_W, 6.4 * cm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 15)
    canvas.drawString(2 * cm, PAGE_H - 2.2 * cm, "ShadowFox")
    canvas.setFont("Helvetica", 9.5)
    canvas.drawString(2 * cm, PAGE_H - 2.75 * cm, "Data Analyst Internship  |  Intermediate Level Submission")
    canvas.setFont("Helvetica-Bold", 25)
    canvas.drawString(2 * cm, PAGE_H - 4.3 * cm, "Customer & Revenue Performance")
    canvas.drawString(2 * cm, PAGE_H - 5.15 * cm, "Analysis of a UK Online Retailer")
    canvas.setFillColor(ACCENT)
    canvas.rect(2 * cm, PAGE_H - 6.55 * cm, 3.2 * cm, 0.14 * cm, fill=1, stroke=0)
    canvas.restoreState()


def build():
    REPORTS.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(REPORTS / "Intermediate_Level_Customer_Revenue_Analysis.pdf"),
                            pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm,
                            topMargin=2.1 * cm, bottomMargin=2 * cm,
                            title="Customer & Revenue Performance Analysis")
    S = []
    K, SS, GG, PP, CC, RR, RF, RT, RE = (F["kpis"], F["seasonality"], F["geography"], F["products"],
                                         F["concentration"], F["repeat"], F["rfm"], F["retention"],
                                         F["returns"])

    # ---------------------------------------------------------------- Cover
    S.append(Spacer(1, 7.2 * cm))
    S.append(p("Business performance analysis of customer behaviour, revenue concentration and repeat "
               "purchasing for a UK-based online gift wholesaler, with data-driven recommendations for "
               "customer retention and revenue growth.", "CoverSub"))
    S.append(Spacer(1, 0.9 * cm))
    meta_rows = [
        ["Dataset", "UCI \u201cOnline Retail\u201d dataset - 541,909 transactions, "
                   f"{K['date_start']} to {K['date_end']}"],
        ["Scope", "Customer, revenue and business performance analysis (Intermediate Level)"],
        ["Tools", "Python (pandas, matplotlib, seaborn), reportlab"],
    ]
    if AUTHOR:
        meta_rows.insert(0, ["Prepared by", AUTHOR])
    mt = Table(meta_rows, colWidths=[3.2 * cm, CONTENT_W - 3.2 * cm])
    mt.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, -1), 9.5),
        ("TEXTCOLOR", (0, 0), (0, -1), PRIMARY), ("TEXTCOLOR", (1, 0), (1, -1), DARK),
        ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    S.append(mt)
    S.append(PageBreak())

    # ---------------------------------------------------------------- Executive summary
    S.append(p("Executive Summary", "H1"))
    S.append(p(
        f"This report analyses {K['sales_lines']:,} cleaned sales lines from a UK-based online wholesaler "
        f"of gift-ware, covering {K['date_start']} to {K['date_end']} (541,909 raw transaction lines before "
        f"cleaning). Net revenue over the period was <b>£{K['net_revenue']/1e6:.2f}M</b> from "
        f"<b>{K['orders']:,} orders</b> and <b>{K['customers']:,} identified customers</b>, at an average "
        f"order value of <b>£{K['aov']:,.0f}</b> - a wholesale-sized basket, consistent with the company's "
        "many trade and gift-shop customers.", "Body"))
    S.append(kpi_row([
        (f"£{K['net_revenue']/1e6:.2f}M", "Net revenue (gross \u2212 returns)"),
        (f"{K['orders']:,}", "Orders"),
        (f"£{K['aov']:,.0f}", "Average order value"),
        (f"{RR['repeat_customer_rate_pct']:.0f}%", "Customers who buy again"),
    ]))
    S.append(Spacer(1, 8))
    S.append(kpi_row([
        (f"{RF['champions_pct_revenue']:.0f}%", "Revenue from Champions (14% of customers)"),
        (f"{CC['top10pct_share']:.0f}%", "Revenue from top 10% of customers"),
        (f"{SS['sep_nov_share_pct']:.0f}%", "Revenue earned in Sep-Nov alone"),
        (f"{RE['adjusted_return_rate_pct']:.1f}%", "Genuine return rate"),
    ]))
    S.append(Spacer(1, 10))
    S.append(p("Five findings shape the recommendations in this report:", "Body"))
    S.append(bullets([
        f"<b>Revenue is highly seasonal.</b> September-November produced {SS['sep_nov_share_pct']:.0f}% of "
        f"full-year net revenue; November alone was {SS['nov_vs_jan_aug_avg_x']:.1f}x the Jan-Aug monthly "
        "average, driven mainly by more orders and more customers, not bigger baskets.",
        f"<b>Revenue is concentrated in a small core of customers.</b> The top 10% of customers generate "
        f"{CC['top10pct_share']:.0f}% of net revenue, and \u201cChampions\u201d "
        f"({RF['champions_customers']:.0f} customers, {RF['champions_pct_customers']:.0f}% of the base) "
        f"alone generate {RF['champions_pct_revenue']:.0f}%.",
        f"<b>Most customers do come back.</b> {RR['repeat_customer_rate_pct']:.0f}% place more than one "
        f"order and together drive {RR['repeat_revenue_share_pct']:.0f}% of revenue, but only "
        f"{RT['month1_pct']:.0f}% of new customers place a second order the following month.",
        f"<b>Reported returns overstate the real return rate.</b> {RE['reversal_share_of_returns_pct']:.0f}%"
        " of \u201creturns\u201d value comes from two orders cancelled minutes after being placed. Once "
        f"these order-entry reversals are removed, the genuine return rate is {RE['adjusted_return_rate_pct']:.1f}%, "
        f"not the headline {K['return_rate_pct']:.1f}%.",
        f"<b>International revenue looks broader than it is.</b> The UK is {GG['uk_share_pct']:.1f}% of "
        "net revenue; three of the next five markets by revenue (Netherlands, EIRE, Australia) each depend "
        "on one or two large accounts rather than a broad customer base.",
    ]))
    S.append(PageBreak())

    # ---------------------------------------------------------------- 1. Data & methodology
    S.append(p("1. Data & Methodology", "H1"))
    S.append(p("<b>Dataset.</b> The <a href='https://archive.ics.uci.edu/dataset/352/online-retail' "
               "color='#1F4E79'>UCI Online Retail dataset</a> (Chen, Sain &amp; Guo, 2012), covering all "
               "transactions of a UK-registered, non-store online retailer of unique all-occasion gifts "
               f"between {K['date_start']} and {K['date_end']}. Many of its customers are wholesalers, "
               "which explains the large basket sizes seen throughout this report.", "Body"))
    S.append(p("<b>Cleaning approach.</b> Of 541,909 raw transaction lines: 5,268 exact duplicates were "
               "removed; 2,910 non-merchandise lines (postage, carriage, manual adjustments, bank charges, "
               "Amazon fees, gift vouchers) were set aside; 8,668 cancelled-order lines were separated into "
               "a returns table; and roughly 2,500 lines with a non-positive quantity or price were removed "
               "as stock write-offs rather than sales. This left 522,568 clean sales lines. The full, "
               "row-by-row log is in <i>outputs/tables/data_cleaning_log.csv</i> and "
               "<i>docs/methodology.md</i>.", "Body"))
    S.append(p("<b>Handling missing customer IDs.</b> 25.1% of sales lines (14.7% of revenue) have no "
               "CustomerID - these are guest-style orders. They are kept in all revenue and product "
               "analysis, and excluded only from customer-level analysis (RFM, cohorts, repeat behaviour), "
               "which is based on the 4,334 identified customers covering 85.3% of revenue.", "Body"))
    S.append(p("<b>Order-entry reversals.</b> A return is flagged as a same-day reversal when the same "
               "customer returns the exact product and quantity they bought within the previous 24 hours. "
               "These behave like corrections rather than genuine dissatisfaction, and account for "
               f"{RE['reversal_share_of_returns_pct']:.0f}% of all return value (driven mostly by two large "
               "cancelled orders). They are shown separately throughout, never silently merged into "
               "\u201creturns\u201d.", "Body"))
    S.append(p("<b>Key definitions.</b>", "H2"))
    S.append(bullets([
        "<b>Gross revenue</b> = Quantity \u00d7 Unit Price, summed over valid sales lines.",
        "<b>Net revenue</b> = Gross revenue \u2212 Returns value (the headline revenue metric used throughout).",
        "<b>Order</b> = one invoice. <b>AOV</b> = gross revenue / number of orders.",
        "<b>RFM segment</b> = Recency / Frequency / Monetary scoring (1-5 each) computed for the 4,320 "
        "identified customers with positive net revenue; see Section 5 for the segment definitions.",
    ]))
    S.append(PageBreak())

    # ---------------------------------------------------------------- 2. Revenue trend
    S.append(p("2. Revenue Trend &amp; Seasonality", "H1"))
    S.append(p(f"Net revenue rose from a Jan-Aug 2011 monthly average of £{SS['jan_aug_avg_monthly']:,.0f} "
               f"to a peak of £{SS['peak_month_net_revenue']/1e6:.2f}M in November 2011 - a rise of "
               f"{SS['nov_vs_jan_aug_avg_x']:.1f}x. December 2011 data stops on the 9th and is shown "
               "hatched; it is a partial month and is excluded from all month-over-month comparisons.", "Body"))
    S.extend(img("01_monthly_net_revenue.png"))
    S.append(p(f"April 2011 was the weakest full month (£{SS['low_month_net_revenue']:,.0f}), a "
               f"{abs(F['monthly_extra']['biggest_mom_drop_pct']):.0f}% drop from March; May then recovered "
               f"{F['monthly_extra']['biggest_mom_gain_pct']:.0f}% month-on-month, the largest gain of the year.",
               "Body"))
    S.append(p("What drove the November peak?", "H2"))
    S.append(p("Breaking the peak into its components shows growth came overwhelmingly from <b>more orders "
               "and more customers</b>, not from customers spending more per order:", "Body"))
    S.extend(img("02_growth_drivers.png"))
    S.append(p(f"Orders in November were {SS['nov_orders_vs_jan_aug_x']:.1f}x the Jan-Aug average and active "
               f"customers were {SS['nov_customers_vs_jan_aug_x']:.1f}x, while AOV rose only "
               f"{100*(SS['nov_aov_vs_jan_aug_x']-1):.0f}%. This points to <b>acquisition and reactivation</b> "
               "(new and returning shoppers placing orders) as the seasonal growth lever, rather than "
               "upsell or bigger baskets - a distinction that matters for how the autumn peak should be "
               "planned and staffed.", "Body"))
    S.append(PageBreak())

    S.append(p("Trading patterns within the week", "H2"))
    S.append(p("No orders are recorded on Saturdays in this dataset (a data or business-hours artefact, "
               "not necessarily a real trading gap), and Sunday is consistently the weakest trading day. "
               "Within the day, the 10:00-16:00 window concentrates the large majority of revenue, "
               "consistent with a business-hours, trade-buyer customer base.", "Body"))
    S.extend(img("03_weekday_hour_patterns.png"))
    S.append(PageBreak())

    # ---------------------------------------------------------------- 3. Geography
    S.append(p("3. Geographic Performance", "H1"))
    S.append(p(f"The UK accounts for {GG['uk_share_pct']:.1f}% of net revenue across {GG['uk_customers']:,} "
               f"customers. The remaining {GG['international_share_pct']:.1f}% is spread across "
               f"{GG['n_countries']-1} other countries, but revenue size is a misleading guide to market "
               "health: some of the largest \u201cinternational markets\u201d are really one or two large "
               "wholesale accounts.", "Body"))
    S.extend(img("04_country_performance.png"))
    S.append(p(f"Netherlands (98% from one account), EIRE (53% from one account) and Australia (90% from "
               "one account) are effectively key-account relationships dressed up as country performance - "
               "losing that single customer would collapse the market. By contrast, Germany and France "
               f"have broad, diversified customer bases ({GG['broad_markets_customers']} combined customers "
               f"across the five broad markets, at an average of £{GG['broad_markets_rev_per_customer']:,.0f} "
               "revenue per customer) and are the more reliable growth candidates.", "Body"))
    S.append(PageBreak())

    # ---------------------------------------------------------------- 4. Products
    S.append(p("4. Product Performance", "H1"))
    S.append(p(f"{PP['products_with_positive_net']:,} distinct products were sold. The top 10 products "
               f"generate only {PP['top10_share_pct']:.1f}% of net revenue - there is no single-product "
               "dependency - but the range as a whole follows a textbook Pareto pattern:", "Body"))
    S.extend(img("06_product_pareto.png"))
    S.append(p(f"Just {PP['products_for_80pct_revenue']:,} products "
               f"({PP['products_for_80pct_share_of_range_pct']:.0f}% of the range) generate 80% of revenue, "
               f"while the bottom half of the range contributes only {PP['bottom50pct_products_share_pct']:.1f}%. "
               "This is a candidate list for inventory rationalisation: the long tail carries "
               "working-capital and listing costs disproportionate to its revenue contribution.", "Body"))
    S.append(p("Top products by revenue", "H2"))
    S.extend(img("05_top_products.png"))
    S.append(p("Which products are seasonal, and which are evergreen?", "H2"))
    S.append(p("Scaling each of the top-10 products to its own peak month shows a mix of steady, "
               "year-round sellers (e.g. the cakestand and party bunting peak outside the holiday period) "
               "and clearly seasonal lines that spike in November. A simple keyword screen for "
               "Christmas-themed products confirms the same pattern at the category level, rising from "
               "under 1% of monthly revenue in mid-year to nearly 12% in November.", "Body"))
    S.extend(img("07_product_seasonality.png"))
    S.append(p(f"{PP['seasonal_products_count']} products (\u2265 £5k annual revenue each, \u2265 60% of "
               f"their revenue in Sep-Nov) are strongly seasonal, together worth £{PP['seasonal_products_revenue']/1e3:,.0f}k "
               "a year. These are the SKUs to prioritise for autumn stock-in and to de-prioritise (or "
               "discount) outside the season.", "Body"))
    S.append(PageBreak())

    # ---------------------------------------------------------------- 5. Customer segmentation
    S.append(p("5. Customer Segmentation (RFM)", "H1"))
    S.append(p("Every identified customer with positive net revenue was scored on Recency (days since "
               "last order), Frequency (number of orders, using business-defined bands) and Monetary value "
               "(net revenue), each on a 1-5 scale, and mapped to ten standard lifecycle segments.", "Body"))
    S.extend(img("09_rfm_segments.png"))
    S.append(p(f"<b>Champions</b> ({RF['champions_customers']:.0f} customers, {RF['champions_pct_customers']:.0f}% "
               f"of the base) alone generate {RF['champions_pct_revenue']:.0f}% of net revenue, and together "
               f"with <b>Loyal Customers</b> ({RF['loyal_pct_revenue']:.0f}% of revenue) these two segments "
               "carry the great majority of the business. At the other end, <b>At Risk</b>, "
               f"<b>Can't Lose Them</b> and <b>Hibernating</b> together are {RF['at_risk_group_pct_customers']:.0f}% "
               f"of customers but only {RF['at_risk_group_pct_revenue']:.0f}% of revenue - representing "
               f"£{RF['at_risk_group_revenue']/1e6:.2f}M of historic revenue now at risk of being lost "
               f"entirely, including {RF['cant_lose_customers']:.0f} \u201cCan't Lose Them\u201d customers "
               f"(previously high-value, now lapsing) worth £{RF['cant_lose_revenue']/1e3:,.0f}k.", "Body"))
    S.append(p("Revenue concentration", "H2"))
    S.append(p(f"The RFM segments are one view of a deeper pattern: revenue is heavily concentrated in a "
               f"small share of customers. The top 10% of customers generate {CC['top10pct_share']:.0f}% of "
               f"net revenue, and just {CC['customers_for_50pct']:,} customers "
               f"({100*CC['customers_for_50pct']/CC['customers_in_rfm']:.0f}% of the base) account for half "
               "of all revenue.", "Body"))
    S.extend(img("08_customer_concentration.png"))
    S.append(p("This concentration is healthy for focused account management, but it is also a "
               f"concentration risk: the single largest customer alone represents "
               f"{CC['largest_customer_share']:.1f}% of identified net revenue.", "Body"))
    S.append(PageBreak())

    # ---------------------------------------------------------------- 6. Repeat behaviour
    S.append(p("6. Repeat Purchase Behaviour &amp; Retention", "H1"))
    S.append(p(f"{RR['repeat_customer_rate_pct']:.0f}% of identified customers place more than one order, "
               f"and these repeat customers generate {RR['repeat_revenue_share_pct']:.0f}% of net revenue - "
               f"on average {RR['avg_revenue_repeat_vs_onetime_x']:.1f}x more revenue per customer than "
               "one-time buyers. For those who do come back, the typical (median) gap between shopping "
               f"days is {RR['median_days_between_orders']:.0f} days.", "Body"))
    S.extend(img("10_repeat_behaviour.png"))
    S.append(p("Revenue is not just concentrated by segment, but by order frequency: customers with 11 or "
               "more orders are only 8% of the base yet generate half of net revenue, while one-time "
               "buyers - over a third of customers - generate just 6%.", "Body"))
    S.append(p("Do new customers come back? Cohort retention", "H2"))
    S.append(p(f"Tracking each month's new-customer cohort forward, only {RT['month1_pct']:.0f}% place "
               "another order the following month. Retention does not then decay steadily - it plateaus "
               f"around {RT['min_after_m1_pct']:.0f}-25% for months 2 through 7 - suggesting the biggest "
               "opportunity is not slowing an ongoing decline, but converting more first-time buyers into "
               "a second purchase in the critical first month.", "Body"))
    S.extend(img("11_cohort_retention.png"))
    S.append(p("New vs. returning revenue", "H2"))
    S.append(p("The share of monthly revenue coming from returning customers rose steadily across the "
               "year, from roughly half in January to 88% by November - additional evidence that the "
               "autumn peak was substantially fuelled by the existing, already-engaged customer base "
               "returning to buy again, alongside new customer acquisition.", "Body"))
    S.extend(img("12_new_vs_returning.png"))
    S.append(PageBreak())

    # ---------------------------------------------------------------- 7. Returns
    S.append(p("7. Returns Analysis", "H1"))
    S.append(p(f"The headline return rate (returns value / gross revenue) is {K['return_rate_pct']:.1f}%, "
               f"but {RE['reversal_share_of_returns_pct']:.0f}% of that value comes from just two orders "
               "that were cancelled within 24 hours of being placed by the same customer for the same "
               "product and quantity - almost certainly order-entry corrections rather than genuine "
               f"returns. Excluding these, the <b>genuine return rate is {RE['adjusted_return_rate_pct']:.1f}%</b>, "
               "a materially healthier and more decision-useful figure.", "Body"))
    S.extend(img("13_returns.png"))
    S.append(p("The clearest genuine quality signal is the \u201cFairy Cake Flannel\u201d line, with a "
               "36% return rate on meaningful sales volume, followed by several other homeware and gift "
               "items in the 15-30% range - these are worth a quality or listing-description review.", "Body"))
    S.append(PageBreak())

    # ---------------------------------------------------------------- 8. Recommendations
    S.append(p("8. Recommendations", "H1"))
    S.append(p("The following five actions follow directly from the findings above, in priority order:", "Body"))
    S.append(Spacer(1, 4))
    S.append(recommendation_box(1, "Protect and grow the Champions segment",
        f"{RF['champions_customers']:.0f} customers generate {RF['champions_pct_revenue']:.0f}% of revenue. "
        "Introduce a named account-management or loyalty-tier programme for this group, with proactive "
        "contact ahead of the autumn peak and early access to seasonal stock, to defend this concentrated "
        "revenue base."))
    S.append(Spacer(1, 8))
    S.append(recommendation_box(2, "Run a targeted win-back campaign for lapsing high-value customers",
        f"£{RF['at_risk_group_revenue']/1e6:.2f}M of historic revenue sits with At Risk / Can't Lose / "
        f"Hibernating customers. Prioritise the {RF['cant_lose_customers']:.0f} \u201cCan't Lose Them\u201d "
        "accounts (previously high-value, now lapsing) with personal outreach and an incentive, before "
        "attempting the larger, lower-value Hibernating group."))
    S.append(Spacer(1, 8))
    S.append(recommendation_box(3, "Build a first-30-day reorder journey for new customers",
        f"Only {RT['month1_pct']:.0f}% of new customers reorder the following month, and the typical repeat "
        f"cycle is {RR['median_days_between_orders']:.0f} days. A structured onboarding sequence (e.g. a "
        "second-order incentive timed to arrive around day 20-25) targets the single biggest drop-off "
        "point in the customer lifecycle."))
    S.append(Spacer(1, 8))
    S.append(recommendation_box(4, "Plan inventory, staffing and cash flow around the Sep-Nov peak",
        f"November revenue is {SS['nov_vs_jan_aug_avg_x']:.1f}x the Jan-Aug average, driven by order and "
        "customer volume rather than basket size. Begin stock build and seasonal staffing from September, "
        f"prioritising the {PP['seasonal_products_count']} identified seasonal SKUs, and use the Jan-Apr "
        "trough for clearance and demand-generation promotions."))
    S.append(Spacer(1, 8))
    S.append(recommendation_box(5, "Grow broad-based international markets, manage key-account risk in others",
        "Germany and France have wide, diversified customer bases and room to grow with normal marketing "
        "investment. Netherlands, EIRE and Australia depend on one or two accounts each - treat these as "
        "key-account relationships requiring retention planning, not organic growth markets, and avoid "
        "over-reading their revenue size as market health."))
    S.append(PageBreak())

    # ---------------------------------------------------------------- 9. Appendix
    S.append(p("Appendix: Supporting Detail Tables", "H1"))
    S.append(p("Data Cleaning Summary", "H2"))
    cl = pd.read_csv(OUT_TABLES / "data_cleaning_log.csv")
    rows = [[r["step"], r["rule"][:70] + ("..." if len(r["rule"]) > 70 else ""),
            f"{r['rows_affected']:,}", f"{r['rows_remaining']:,}"] for _, r in cl.iterrows()]
    S.append(data_table(["#", "Cleaning rule", "Rows affected", "Rows remaining"], rows,
                        [1.1 * cm, 10.8 * cm, 2.6 * cm, 2.6 * cm],
                        align={2: "RIGHT", 3: "RIGHT"}))
    S.append(Spacer(1, 14))

    rf = pd.read_csv(OUT_TABLES / "rfm_summary.csv")
    rows = [[r["segment"], f"{r['customers']:,.0f}", f"{r['pct_customers']:.1f}%",
            f"£{r['net_revenue']:,.0f}", f"{r['pct_net_revenue']:.1f}%", f"{r['avg_recency_days']:.0f}"]
           for _, r in rf.iterrows()]
    S.append(KeepTogether([p("RFM Segment Summary", "H2"),
        data_table(["Segment", "Customers", "% cust.", "Net revenue", "% revenue", "Avg recency (days)"],
                  rows, [3.3 * cm, 1.9 * cm, 1.7 * cm, 2.9 * cm, 2.1 * cm, 3.2 * cm],
                  align={1: "RIGHT", 2: "RIGHT", 3: "RIGHT", 4: "RIGHT", 5: "RIGHT"})]))
    S.append(Spacer(1, 14))

    ct = pd.read_csv(OUT_TABLES / "country.csv").head(10)
    rows = [[r["Country"], f"£{r['net_revenue']:,.0f}", f"{r['share_of_net_pct']:.1f}%",
            f"{r['customers']:,.0f}", f"£{r['aov']:,.0f}", f"{r['top_customer_share_pct']:.0f}%"]
           for _, r in ct.iterrows()]
    S.append(KeepTogether([p("Top 10 Countries by Net Revenue", "H2"),
        data_table(["Country", "Net revenue", "% of total", "Customers", "AOV", "Top account %"],
                  rows, [3.0 * cm, 2.7 * cm, 2.0 * cm, 2.2 * cm, 2.0 * cm, 3.2 * cm],
                  align={1: "RIGHT", 2: "RIGHT", 3: "RIGHT", 4: "RIGHT", 5: "RIGHT"})]))
    S.append(Spacer(1, 14))

    pt = pd.read_csv(OUT_TABLES / "products.csv").head(10)
    rows = [[string.capwords(r["description"].lower())[:36], f"£{r['net_revenue']:,.0f}",
            f"{r['units']:,.0f}", f"{r['orders']:,.0f}", f"{r['return_rate_pct']:.1f}%"]
           for _, r in pt.iterrows()]
    S.append(KeepTogether([p("Top 10 Products by Net Revenue", "H2"),
        data_table(["Product", "Net revenue", "Units", "Orders", "Return rate"],
                  rows, [6.4 * cm, 2.9 * cm, 2.2 * cm, 2.2 * cm, 2.4 * cm],
                  align={1: "RIGHT", 2: "RIGHT", 3: "RIGHT", 4: "RIGHT"})]))
    S.append(Spacer(1, 16))
    S.append(p("Full detail tables (22 CSVs covering every metric in this report) are provided in "
               "<i>outputs/tables/</i>; full-resolution charts are in <i>outputs/charts/</i>; the one-page "
               "executive dashboard is in <i>dashboard/executive_dashboard.png</i>; and the complete, "
               "reproducible analysis code is in <i>src/</i>. See <i>README.md</i> for how to reproduce "
               "every figure in this report from the raw data.", "Body"))

    doc.build(S, onFirstPage=cover, onLaterPages=header_footer)
    print(f"Saved {doc.filename}")


if __name__ == "__main__":
    build()
