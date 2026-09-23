# ShadowFox Data Analyst Internship

A structured collection of Data Analyst projects completed for the **ShadowFox Data Analyst Internship**, progressing from Beginner → Intermediate → Advanced. Each level lives in its own folder with its own dataset, workflow, and documentation, so it can be reviewed independently.

The work spans data cleaning, exploratory analysis, business insight generation, spreadsheet and Python-based dashboards, and — at the advanced level — interactive BI dashboarding.

---

## 📊 Project Levels

| Level | Focus | Tools | Status |
|---|---|---|---|
| 🟢 [Beginner](beginner/) | Data cleaning, sales KPIs, Excel dashboard, business insights | Excel / Google Sheets | ✅ Completed |
| 🟡 [Intermediate](intermediate/) | Customer behaviour, revenue performance, retention, RFM segmentation | Python (pandas, matplotlib, seaborn, reportlab) | ✅ Completed |
| 🔴 [Advanced](advanced/) | Executive dashboarding, KPI design, interactive reporting | Power BI / Tableau | 🚧 In Progress |

---

## 🗂️ Repository Structure

```text
ShadowFox-Data-Analyst-Internship/
├── beginner/
│   ├── dashboard/           # Excel dashboard workbook
│   ├── data/                # Raw and cleaned sales data
│   ├── documentation/       # Cleaning notes and write-up
│   ├── screenshots/         # Dashboard preview images
│   └── README.md
│
├── intermediate/
│   ├── data/                # Raw and cleaned transaction data
│   ├── src/                 # Reproducible analysis pipeline (clean → analyse → chart → report)
│   ├── outputs/             # Generated tables (CSV) and charts (PNG)
│   ├── dashboard/           # One-page executive dashboard
│   ├── reports/             # Final PDF report
│   ├── docs/                # Methodology, data dictionary, video script
│   ├── notebooks/           # Executed exploratory notebook
│   ├── run_pipeline.py
│   ├── requirements.txt
│   └── README.md
│
├── advanced/                 # 🚧 In progress — Power BI / Tableau executive dashboard
│
└── README.md                 # you are here
```

---

## 🟢 Beginner Level — Small Business Sales Analysis

A synthetic small-business sales dataset (order date, region, category, product, quantity, price, discount, sales, profit) cleaned and analysed in Excel, following the task brief's beginner-level requirements: a cleaned dataset, key summary metrics, monthly/category/region trend analysis, charts, a simple dashboard, and business-oriented conclusions.

**Workbook:** [`ShadowFox_Beginner_Sales_Dashboard.xlsx`](beginner/dashboard/ShadowFox_Beginner_Sales_Dashboard.xlsx), with sheets for `Dashboard`, `Raw_Data`, `Cleaned_Data`, `Analysis`, and `Cleaning_Notes`.

**Headline metrics:**

| Metric | Value |
|---|---|
| Total Sales | ₹436,105.00 |
| Total Profit | ₹141,507.84 |
| Total Orders | 150 |
| Total Units Sold | 581 |
| Average Order Value | ₹2,907.37 |
| Profit Margin | 32.45% |

**Key findings:** Bluetooth Speaker (Electronics) is the top product; Office Supplies is the lowest-selling category; December is the strongest month; North is the strongest region.

📄 Full write-up: [`beginner/README.md`](beginner/README.md)

---

## 🟡 Intermediate Level — Customer & Revenue Performance Analysis

A full customer, revenue, and business-performance analysis of a real UK online gift wholesaler (541,909 transactions, Dec 2010–Dec 2011), built as a reproducible Python pipeline rather than a one-off notebook: raw data → cleaning (with an auditable log) → metrics → charts → a designed PDF report, all regenerable with one command.

**Headline findings:**

- **£9.77M** net revenue from **19,773 orders** and **4,334 identified customers** (AOV £518).
- **Seasonality:** Sep–Nov produced **37.5%** of full-year net revenue; November alone was **2.25×** the Jan–Aug monthly average, driven by more orders and customers rather than bigger baskets.
- **Concentration:** the top **10%** of customers generate **60%** of net revenue; "Champions" (14% of customers) alone generate **50%**.
- **Retention:** **65%** of customers buy again and drive **94%** of revenue, but only **~20%** of new customers place a second order the following month.
- **Returns:** the headline 4.6% return rate is overstated — **61.5%** of "returns" value comes from two orders cancelled minutes after being placed. The genuine return rate is **1.8%**.
- **Geography:** the UK is **84.8%** of revenue; three of the next five markets (Netherlands, EIRE, Australia) each depend on just one or two large accounts.

**Why this dataset:** the brief allowed a free choice of dataset for a customer/revenue/business-performance analysis on "a more realistic dataset." The [UCI Online Retail dataset](https://archive.ics.uci.edu/dataset/352/online-retail) (Chen, Sain & Guo, 2012, CC BY 4.0) was chosen because it has customer IDs — needed for the retention, repeat-purchase, and segmentation requirements — and is large and genuinely messy enough to require real cleaning decisions rather than a toy dataset.

**Reproduce it:**
```bash
cd intermediate
pip install -r requirements.txt
python run_pipeline.py
```

### 📌 Project Resources

- 📄 **Full Report:** [Intermediate Level Customer Revenue Analysis](intermediate/reports/Intermediate_Level_Customer_Revenue_Analysis.pdf)
- 🖼️ **Executive Dashboard:** [View Dashboard](intermediate/dashboard/executive_dashboard.png)
- 📘 **Methodology & Data Dictionary:** [View Documentation](intermediate/docs/)
- 📝 **Full Project Write-up:** [View Intermediate README](intermediate/README.md)
---

## 🔴 Advanced Level — Executive Dashboard *(In Progress)*

The advanced task calls for an executive-style, interactive dashboard built in **Power BI or Tableau** on a realistic sales, operations, HR, or marketing dataset (e.g. the IBM HR Analytics dataset), with KPI selection, filters/drill-down, and decision-oriented storytelling.

Work in progress — this section and the `advanced/` folder will be updated with the dataset choice, dashboard file, KPI rationale, and write-up once complete.

---

## 🧰 Skills Demonstrated Across the Internship

- Data cleaning and quality auditing (Excel and Python)
- Exploratory and business-performance analysis
- Customer segmentation (RFM) and cohort retention analysis
- Data visualization and dashboard design (spreadsheet, matplotlib/seaborn, and BI tooling)
- Reproducible, documented analytical pipelines
- Business-oriented insight writing and recommendations


## 👤 Author

**Mohd Maaz Gani**

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Mohd%20Maaz%20Gani-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/mohd-maaz-gani/)

**GitHub:** [@mohdmaazgani](https://github.com/mohdmaazgani)
