# Methodology

This document explains every analytical decision behind the report in enough
detail to reproduce, audit, or challenge it.

## 1. Data source

**UCI "Online Retail" dataset** (Chen, Sain & Guo, 2012), obtained via a public
GitHub mirror of the same 541,909-row dataset (see `src/00_download_data.py`
and `README.md` for provenance). Licence: CC BY 4.0.

- Transactions of a UK-registered, non-store online retailer of unique
  all-occasion gifts, many of whose customers are wholesalers.
- Period: 2010-12-01 to 2011-12-09 (2011-12 is a **partial month**).
- Columns: `InvoiceNo, StockCode, Description, Quantity, InvoiceDate,
  UnitPrice, CustomerID, Country`.

## 2. Cleaning pipeline (`src/clean.py`)

Every step below is logged with row counts and pound-value affected in
`outputs/tables/data_cleaning_log.csv`.

| # | Rule | Rationale |
|---|------|-----------|
| 1 | Remove exact duplicate rows (all 8 columns identical) | Same invoice/product/qty/price/timestamp is almost certainly a double-entered row, not two genuine lines |
| 2 | Separate non-product lines (`POST`, `DOT`, `M`, `D`, `S`, `B`, `C2`, `BANK CHARGES`, `AMAZONFEE`, `CRUK`, `PADS`, `gift_*` vouchers) | These are postage, manual adjustments, fees and vouchers, not merchandise sales, and would distort product/AOV metrics if left in |
| 3 | Separate cancellations (`InvoiceNo` starts with `C`) into a returns table | Cancellations are a different business event from a sale and are analysed on their own terms |
| 4 | Remove sales lines with `Quantity <= 0` | Stock write-offs / damages, not customer sales |
| 5 | Remove sales lines with `UnitPrice <= 0` | Free/adjustment lines carry no revenue and are usually missing a description |
| 6 | Remove return lines with `UnitPrice <= 0` or `Quantity >= 0` | A valid return needs a positive price and a negative quantity |
| 7 | Standardise product descriptions | A `StockCode` can carry multiple spellings; the most frequent spelling per code is used everywhere |
| 8 | Add derived columns | `Revenue`, `InvoiceMonth`, `InvoiceDay`, `Weekday`, `Hour`, `HasCustomerID` |
| 9 | Flag (not drop) missing `CustomerID` | Kept for revenue/product analysis; excluded only from customer-level analysis |

Result: **522,568 clean sales lines**, **8,668 return lines**, **2,910
non-product lines**.

## 3. Order-entry reversals

A return line is flagged `is_reversal = True` when the **same customer**
returns the **same product and quantity** they bought, within **24 hours** of
that purchase (`analysis.flag_reversals`). These are treated as corrections,
not genuine dissatisfaction. They are:

- Never removed from the returns table (so nothing is silently discarded).
- Always shown alongside the "reported" return rate, never merged into it
  without disclosure.
- Responsible for 61.5% of all return value, driven mainly by two large
  orders (invoices 581483/C581484 and 541431/C541433) cancelled minutes
  after being placed.

## 4. Definitions used throughout

- **Gross revenue** = `Quantity x UnitPrice`, summed over valid sales lines.
- **Net revenue** = Gross revenue - Returns value. This is the headline
  revenue metric used everywhere in the report.
- **Order** = one invoice. **AOV** = gross revenue / number of orders.
- **Full month** = any calendar month with complete data (Dec-2010 to
  Nov-2011). Dec-2011 is a **partial month** (data stops 9 Dec) and is
  excluded from every month-over-month or seasonal comparison.
- **Identified customer** = a sales line with a non-null `CustomerID`.
  85.3% of net revenue and 74.9% of sales lines have one.

## 5. RFM segmentation (`analysis.customer_table`, `rfm_segment`)

Computed for the **4,320 identified customers with positive net revenue**
(customers whose only orders were fully cancelled are excluded, since they
have no revenue to segment).

- **Recency (R)**: days since last order, converted to a 1-5 score by
  quintile (5 = most recent).
- **Frequency (F)**: a **business-defined** band, not a quintile, to avoid
  arbitrary tie-breaking on a heavily-repeated distribution (median = 2
  orders): 1 order -> F1, 2 -> F2, 3 -> F3, 4-5 -> F4, 6+ -> F5.
- **Monetary (M)**: net revenue, scored 1-5 by quintile.
- **Segment**: R and F are mapped to ten standard lifecycle segments
  (Champions, Loyal Customers, Potential Loyalists, New Customers, Promising,
  Need Attention, About to Sleep, At Risk, Can't Lose Them, Hibernating)
  using the grid in `analysis.rfm_segment`.

## 6. Cohort retention (`analysis.cohort_retention`)

- A customer's cohort = the calendar month of their first order.
- Retention at "month N" = % of the cohort that places at least one order
  exactly N months after their first order.
- The **December 2010 cohort is excluded from the average retention curve**
  (though still shown in the heatmap) because the dataset's start date
  artificially creates it - it mixes genuinely new customers with
  already-existing customers whose earlier history simply isn't in the data.
- Cells beyond the 9-Dec-2011 observation window are left blank, not
  computed as 0%.
- Customers whose net revenue is not positive are excluded (consistent with
  the RFM population).

## 7. Repeat-purchase metrics (`analysis.repeat_behaviour`)

- "Repeat customer" = a customer (net revenue > 0) with 2 or more orders.
- "Days between orders" = the gap between a customer's distinct shopping
  days, computed per customer and pooled.
- "Repeat within 90 days" is computed only for customers whose **first
  order was in Jan-2011 or later** and who had at least 90 days of
  potential follow-up before the data ends, to avoid counting Dec-2010
  arrivals (who may be long-standing customers) as "new".

## 8. Product Pareto & seasonality (`analysis.product_tables`)

- Products are ranked by net revenue; cumulative share is computed only
  over products with **positive** net revenue.
- "Seasonal" products: >= £5,000 in 12-month revenue AND >= 60% of that
  revenue falls in Sep-Nov 2011.
- "Christmas-themed" is a keyword match on the product description
  (`CHRISTMAS|XMAS|SANTA|ADVENT|REINDEER`) - a heuristic, not a maintained
  product-category field, and is disclosed as such in the report.

## 9. Known limitations

- The dataset has no product-category field, cost data, or marketing-spend
  data, so profitability and ROI cannot be assessed - only revenue.
- Country-level "top account share" only reveals concentration; it does not
  distinguish a wholesaler placing regular bulk orders from a single
  one-off large order (both would show high concentration).
- The Christmas-product flag is a name-based heuristic and will miss
  unlabelled seasonal items and may over-count items that merely mention a
  festive word.
- No product cost or margin data exists, so all revenue figures are gross
  of cost of goods sold.
