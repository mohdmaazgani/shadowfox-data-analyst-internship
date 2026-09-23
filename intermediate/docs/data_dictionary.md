# Data Dictionary

## Raw data — `data/raw/online_retail_raw.csv.gz` (541,909 rows)

| Column | Type | Description |
|---|---|---|
| InvoiceNo | text | 6-digit invoice number. Prefix `C` = cancellation. |
| StockCode | text | 5-digit product code (may carry a trailing letter). |
| Description | text | Product name as entered at point of sale. |
| Quantity | integer | Units on this line. Negative on cancellations. |
| InvoiceDate | datetime | Date and time the line was recorded. |
| UnitPrice | float | Price per unit, GBP (£). |
| CustomerID | integer (nullable) | 5-digit customer identifier. ~25% of lines are null (guest-style orders). |
| Country | text | Customer's country. |

## Cleaned sales — `data/processed/sales_clean.csv.gz` (522,568 rows)

All raw columns, plus:

| Column | Type | Description |
|---|---|---|
| Revenue | float | `Quantity x UnitPrice`, rounded to 2dp. |
| InvoiceMonth | text | `YYYY-MM`. |
| InvoiceDay | text | `YYYY-MM-DD`. |
| Weekday | text | Full weekday name. |
| Hour | integer | Hour of day (0-23) the invoice was recorded. |
| HasCustomerID | boolean | `True` if CustomerID is present. |

## Cleaned returns — `data/processed/returns_clean.csv.gz` (8,668 rows)

Same structure as sales, except:

| Column | Type | Description |
|---|---|---|
| ReturnValue | float | Positive value of the return (`-Quantity x UnitPrice`). |
| is_reversal | boolean | `True` if this return reverses an identical purchase by the same customer within 24 hours (see methodology.md). |

## Non-product lines — `data/processed/non_product_lines.csv.gz` (2,910 rows)

Same structure as raw data. Contains postage, carriage, manual adjustments,
bank charges, Amazon fees and gift vouchers - kept for completeness but
excluded from all revenue/product/customer analysis.

## Output tables — `outputs/tables/*.csv`

| File | Grain | Key columns |
|---|---|---|
| monthly.csv | month | gross_revenue, net_revenue, returns_value, reversal_value, return_rate_pct, return_rate_adj_pct, orders, active_customers, aov |
| weekday.csv | weekday | gross_revenue, orders, aov, share_pct |
| hourly.csv | hour of day | gross_revenue, orders, share_pct |
| country.csv | country | net_revenue, share_of_net_pct, orders, customers, aov, top_customer_share_pct |
| products.csv | product (StockCode) | net_revenue, units, orders, customers, return_rate_pct, return_rate_adj_pct, cum_share_pct, rank |
| product_heatmap.csv | product x month | revenue for the top-10 products only |
| seasonal_products.csv | product | revenue_12m, autumn_share_pct (products >=60% autumn-weighted) |
| christmas_share.csv | month | % of monthly revenue from Christmas-themed products |
| customers.csv | customer (CustomerID) | orders, net_revenue, recency_days, R/F/M scores, segment |
| rfm_summary.csv | RFM segment | customers, net_revenue, pct_customers, pct_net_revenue |
| customer_deciles.csv | customer decile (1=top) | customers, net_revenue, share_pct, cum_share_pct |
| top10_customers.csv | customer | the 10 largest customers by net revenue |
| lorenz_curve.csv | percentile | cumulative customer % vs cumulative revenue % |
| orders_distribution.csv | orders band | customers, net_revenue in each band (1, 2, 3, 4-5, 6-10, 11+) |
| new_vs_returning.csv | month | revenue split between new and returning identified customers |
| gaps_days.csv | order gap (row per gap) | days_between_orders |
| cohort_retention.csv | first-order cohort | % of cohort active in each subsequent month |
| avg_retention.csv | months since first order | average retention % across cohorts |
| top_return_invoices.csv | invoice | the 10 largest return invoices |
| top_return_rate_products.csv | product | highest genuine (reversal-adjusted) return rates, >=£5k sales |
| top_return_value_products.csv | product | highest genuine return value |
| data_cleaning_log.csv | cleaning step | rule, rows affected, rows remaining, value affected |
| kpis_and_facts.json | - | every headline figure quoted in the report, machine-readable |
