# 3-5 Minute Video Walkthrough — Script Outline

Use this as a talking-point outline, not a word-for-word script. Aim for 4
minutes. Screen-share the PDF report and/or the dashboard image as you talk.

## 1. Intro (30 sec)
- "This is my Intermediate Level submission for the ShadowFox Data Analyst
  internship: a customer and revenue performance analysis of a real UK
  online retailer."
- Name the dataset (UCI Online Retail, 541,909 transactions, Dec 2010-Dec
  2011) and why you chose it (real transactional data with customer IDs,
  rich enough for customer/revenue/segment analysis).

## 2. Data cleaning (45 sec)
- Show `docs/methodology.md` or `outputs/tables/data_cleaning_log.csv`.
- Mention: removed duplicates, separated postage/fees/vouchers from real
  product sales, separated cancellations into a returns table, and — the
  one interesting judgement call — identified that 62% of "returns" value
  was actually two orders cancelled minutes after being placed, not real
  returns, so you reported both a headline and an adjusted return rate.

## 3. Revenue trend & seasonality (45 sec)
- Open the executive dashboard or `01_monthly_net_revenue.png`.
- "Revenue is highly seasonal — Sep-Nov is 38% of the year. I broke down
  *why* November peaked: more orders and more customers, not bigger
  baskets — which changes what the business should actually do to prepare
  for it (stock and staffing, not pricing)."

## 4. Customer segmentation (45 sec)
- Open `09_rfm_segments.png` and `08_customer_concentration.png`.
- "I built a full RFM segmentation. 14% of customers — the Champions — 
  generate half of all revenue. On the other end, 40% of customers are
  At Risk, Can't Lose, or Hibernating, representing over a million pounds
  of revenue that's at risk of disappearing."

## 5. Repeat behaviour & retention (30 sec)
- Open `10_repeat_behaviour.png` or `11_cohort_retention.png`.
- "65% of customers come back, and they drive 94% of revenue — but only
  20% of new customers place a second order the next month. That's the
  single biggest lever I'd pull first."

## 6. Recommendations (30 sec)
- Walk through the 5 recommendations in the report, one sentence each,
  tying each one back to a specific number from the analysis.

## 7. Close (15 sec)
- "All the code, cleaned data, 22 output tables, 13 charts and the full
  PDF report are in the GitHub repo, structured as src/data/outputs/
  reports/docs. Thanks for watching."

## Recording tips
- Screen-record the dashboard PNG and 2-3 report pages at most — don't
  scroll through everything.
- Speak to the *decisions* you made (reversal detection, cohort exclusion,
  frequency banding) — that's what distinguishes analysis from just
  running a script.
