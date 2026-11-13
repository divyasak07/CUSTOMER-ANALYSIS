# 📈 Customer Analytics: Segmentation, Retention & Revenue Analysis

**Author:** Oshi Sharma
**Tools:** Python (pandas, matplotlib, seaborn) · SQL · Power BI
**Data:** UCI Online Retail Dataset — 260K+ transactions, 4,300+ customers, UK e-commerce
**Period:** Dec 2010 – Dec 2011

---

## The Question

> An e-commerce company hands you one year of transaction data and asks:
> "Who are our best customers? Are we retaining them? Where are we losing revenue? What should we do about it?"

This project answers that question through five layers of analysis — going beyond "what happened" to explain **why** and recommend **what to do.**

---

## The Five Layers

### Layer 1: Data Cleaning & Quality
- Started with 260,562 raw transactions — 25% missing CustomerIDs, 5,035 cancellations, 14,199 zero-price rows, and 814 duplicates
- Cleaned to 180,593 analysis-ready rows across 4,297 customers and 38 products
- Total revenue: £10.9M

### Layer 2: RFM Segmentation
Scored every customer on **Recency** (days since last purchase), **Frequency** (number of orders), and **Monetary** (total spend), then classified into 8 segments:

| Segment | Customers | % Revenue | Avg Spend |
|---------|-----------|-----------|-----------|
| Champions | 1,106 | 72.2% | £7,117 |
| Loyal | 750 | 14.3% | £2,079 |
| At Risk | 443 | 7.1% | £1,751 |
| Lost | 1,156 | 3.5% | £327 |
| Others | 842 | 2.9% | — |

**Key insight:** 25.7% of customers (Champions) drive **72% of all revenue.** Protecting this segment is the single highest-leverage thing the business can do.

### Layer 3: Cohort Retention Analysis
Grouped customers by their first-purchase month and tracked what percentage returned each subsequent month.

![Cohort Retention Heatmap](visualizations/cohort_retention_heatmap.png)

**Key insight:** Average Month-1 retention is only **47%** — more than half of new customers never come back. The Dec 2010 cohort retains at 60% (best), while Nov 2011 drops to 22% (worst). Investigating what drove the Dec cohort's stickiness could unlock retention gains across all cohorts.

### Layer 4: Revenue Decomposition
Split total revenue into new vs. returning customer contributions:

- **Returning customers: 77% of revenue** (£8.4M)
- **New customers: 23% of revenue** (£2.5M)

![Revenue Decomposition](visualizations/revenue_decomposition.png)

**Key insight:** Growth is overwhelmingly driven by existing customers spending more, not by new customer acquisition. Retention is the growth lever, not acquisition.

### Layer 5: Churn Risk Identification
Flagged customers who bought 3+ times historically but have been inactive for 60+ days:

- **311 at-risk customers** with £404K in historical revenue
- **63 high-value at-risk** (top 20% by spend, avg £2,705 lifetime) — priority for re-engagement
- Most at-risk customers fall in the "At Risk" and "Needs Attention" RFM segments

![Churn Risk](visualizations/churn_risk.png)

---

## Recommendations

1. **Second-Purchase Campaign:** Month-1 retention drops to 47%. Implement a targeted discount/reminder within 30 days of first order to drive the critical second purchase.

2. **Champion Protection Program:** 1,106 Champions drive 72% of revenue. Create loyalty/early-access programs — losing even a few Champions has outsized revenue impact.

3. **Win-Back Campaign:** Target the 63 high-value at-risk customers with personalized re-engagement. They've already proven willingness to spend (avg £2,705 lifetime).

4. **Cohort Investigation:** The Dec 2010 cohort retains at 60% vs. 47% average. Investigate what campaign, product, or seasonal factor drove that — replicate for future cohorts.

5. **Reduce One-and-Done:** 27% of customers are "Lost" (bought once, never returned). Improve post-purchase experience and onboarding to convert first-time buyers into repeat customers.

---

## Project Structure

```
customer-analytics/
├── README.md
├── customer_analytics.py          ← Complete Python analysis (all 5 layers)
├── sql/
│   └── analysis.sql               ← 10 SQL queries
├── data/
│   ├── online_retail_raw.csv      ← Raw transaction data
│   ├── online_retail_clean.csv    ← Cleaned data
│   ├── rfm_segments.csv           ← RFM scores per customer
│   ├── cohort_retention.csv       ← Retention matrix
│   └── monthly_revenue_by_type.csv
├── visualizations/
│   ├── rfm_segments.png
│   ├── cohort_retention_heatmap.png
│   ├── revenue_decomposition.png
│   └── churn_risk.png
└── output/
    └── executive_summary.txt
```

---

## How to Run

```bash
git clone https://github.com/oshi-b-s/customer-analytics.git
cd customer-analytics
pip install pandas matplotlib seaborn
python customer_analytics.py
```

---

## Connect

- [LinkedIn](https://www.linkedin.com/in/oshi-b-sharma/)
- [Portfolio](https://oshi-sharma-portfolio.vercel.app/)
- [Email](mailto:oshibs24.pumba@gmail.com)
