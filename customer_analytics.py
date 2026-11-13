"""
Customer Analytics: Segmentation, Retention & Revenue Analysis
================================================================
Author: Oshi Sharma
Data:   UCI Online Retail Dataset (UK e-commerce, ~260K transactions, 4,300+ customers)
Tools:  Python (pandas, matplotlib, seaborn), SQL, Power BI

Five layers of analysis:
1. Data Cleaning & Quality
2. RFM Segmentation (Recency, Frequency, Monetary)
3. Cohort Retention Analysis
4. Revenue Decomposition (New vs Returning)
5. Churn Risk Identification & Recommendations
"""

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette('deep')

print("=" * 70)
print("CUSTOMER ANALYTICS: SEGMENTATION, RETENTION & REVENUE")
print("=" * 70)


# ══════════════════════════════════════════════════════════════════════
# LAYER 1: DATA CLEANING & QUALITY
# ══════════════════════════════════════════════════════════════════════
print("\n📋 LAYER 1: DATA CLEANING & QUALITY")
print("-" * 50)

df = pd.read_csv("data/online_retail_raw.csv", parse_dates=["InvoiceDate"])
print(f"Raw data: {len(df):,} rows × {len(df.columns)} columns")

# --- Quality checks ---
print(f"\nQuality issues found:")
print(f"  Null CustomerIDs:    {df['CustomerID'].isna().sum():,} ({df['CustomerID'].isna().mean()*100:.1f}%)")
print(f"  Negative quantities: {(df['Quantity'] < 0).sum():,} (cancellations)")
print(f"  Zero/neg prices:     {(df['UnitPrice'] <= 0).sum():,}")
print(f"  Duplicate rows:      {df.duplicated().sum():,}")

# --- Clean ---
df_clean = df.copy()

# Remove rows without CustomerID (can't do customer-level analysis without it)
df_clean = df_clean.dropna(subset=['CustomerID'])
df_clean['CustomerID'] = df_clean['CustomerID'].astype(int)

# Remove cancellations (InvoiceNo starting with 'C')
df_clean = df_clean[~df_clean['InvoiceNo'].astype(str).str.startswith('C')]

# Remove zero/negative prices
df_clean = df_clean[df_clean['UnitPrice'] > 0]

# Remove negative quantities
df_clean = df_clean[df_clean['Quantity'] > 0]

# Remove duplicates
df_clean = df_clean.drop_duplicates()

# Calculate revenue
df_clean['Revenue'] = (df_clean['Quantity'] * df_clean['UnitPrice']).round(2)

# Time features
df_clean['Year'] = df_clean['InvoiceDate'].dt.year
df_clean['Month'] = df_clean['InvoiceDate'].dt.month
df_clean['YearMonth'] = df_clean['InvoiceDate'].dt.to_period('M')

print(f"\nCleaned data: {len(df_clean):,} rows ({len(df) - len(df_clean):,} removed)")
print(f"Unique customers: {df_clean['CustomerID'].nunique():,}")
print(f"Unique products: {df_clean['StockCode'].nunique():,}")
print(f"Total revenue: £{df_clean['Revenue'].sum():,.2f}")
print(f"Date range: {df_clean['InvoiceDate'].min().date()} → {df_clean['InvoiceDate'].max().date()}")

# Save cleaned data
df_clean.to_csv("data/online_retail_clean.csv", index=False)


# ══════════════════════════════════════════════════════════════════════
# LAYER 2: RFM SEGMENTATION
# ══════════════════════════════════════════════════════════════════════
print("\n\n📊 LAYER 2: RFM SEGMENTATION")
print("-" * 50)

# Reference date: day after last transaction
reference_date = df_clean['InvoiceDate'].max() + pd.Timedelta(days=1)
print(f"Reference date: {reference_date.date()}")

# Calculate RFM metrics per customer
rfm = df_clean.groupby('CustomerID').agg({
    'InvoiceDate': lambda x: (reference_date - x.max()).days,  # Recency
    'InvoiceNo': 'nunique',                                     # Frequency
    'Revenue': 'sum',                                           # Monetary
}).rename(columns={
    'InvoiceDate': 'Recency',
    'InvoiceNo': 'Frequency',
    'Revenue': 'Monetary',
})

# Score each dimension 1-5 using quintiles
rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=[5,4,3,2,1]).astype(int)
rfm['F_Score'] = pd.qcut(rfm['Frequency'].rank(method='first'), 5, labels=[1,2,3,4,5]).astype(int)
rfm['M_Score'] = pd.qcut(rfm['Monetary'].rank(method='first'), 5, labels=[1,2,3,4,5]).astype(int)

# Combined RFM score
rfm['RFM_Score'] = rfm['R_Score'] + rfm['F_Score'] + rfm['M_Score']

# Segment customers based on RFM
def segment_customer(row):
    r, f, m = row['R_Score'], row['F_Score'], row['M_Score']
    if r >= 4 and f >= 4 and m >= 4:
        return 'Champions'
    elif r >= 3 and f >= 3 and m >= 3:
        return 'Loyal'
    elif r >= 4 and f <= 2:
        return 'New Customers'
    elif r >= 3 and f >= 2:
        return 'Potential Loyalists'
    elif r <= 2 and f >= 3 and m >= 3:
        return 'At Risk'
    elif r <= 2 and f >= 4:
        return 'Cannot Lose'
    elif r <= 2 and f <= 2:
        return 'Lost'
    else:
        return 'Needs Attention'

rfm['Segment'] = rfm.apply(segment_customer, axis=1)

# Summary
segment_summary = rfm.groupby('Segment').agg(
    Customers=('Recency', 'count'),
    Avg_Recency=('Recency', 'mean'),
    Avg_Frequency=('Frequency', 'mean'),
    Avg_Monetary=('Monetary', 'mean'),
    Total_Revenue=('Monetary', 'sum'),
).round(1)
segment_summary['Pct_Customers'] = (segment_summary['Customers'] / len(rfm) * 100).round(1)
segment_summary['Pct_Revenue'] = (segment_summary['Total_Revenue'] / rfm['Monetary'].sum() * 100).round(1)
segment_summary = segment_summary.sort_values('Total_Revenue', ascending=False)

print("\nRFM Segment Summary:")
print(segment_summary.to_string())

# Save RFM data
rfm.to_csv("data/rfm_segments.csv")

# --- Visualization: RFM Segment Distribution ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Customer count by segment
order = segment_summary.index.tolist()
colors = sns.color_palette('deep', len(order))
axes[0].barh(order, segment_summary['Customers'], color=colors)
axes[0].set_xlabel('Number of Customers')
axes[0].set_title('Customer Count by Segment', fontsize=14, fontweight='bold')
for i, v in enumerate(segment_summary['Customers']):
    axes[0].text(v + 10, i, f'{v:,}', va='center', fontsize=10)

# Revenue share by segment
axes[1].barh(order, segment_summary['Pct_Revenue'], color=colors)
axes[1].set_xlabel('% of Total Revenue')
axes[1].set_title('Revenue Share by Segment', fontsize=14, fontweight='bold')
for i, v in enumerate(segment_summary['Pct_Revenue']):
    axes[1].text(v + 0.3, i, f'{v:.1f}%', va='center', fontsize=10)

plt.tight_layout()
plt.savefig('visualizations/rfm_segments.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n✓ Saved: visualizations/rfm_segments.png")


# ══════════════════════════════════════════════════════════════════════
# LAYER 3: COHORT RETENTION ANALYSIS
# ══════════════════════════════════════════════════════════════════════
print("\n\n📈 LAYER 3: COHORT RETENTION ANALYSIS")
print("-" * 50)

# Assign each customer to their cohort (month of first purchase)
customer_first = df_clean.groupby('CustomerID')['InvoiceDate'].min().reset_index()
customer_first.columns = ['CustomerID', 'FirstPurchaseDate']
customer_first['CohortMonth'] = customer_first['FirstPurchaseDate'].dt.to_period('M')

# Merge cohort info back
df_cohort = df_clean.merge(customer_first[['CustomerID', 'CohortMonth']], on='CustomerID')
df_cohort['TransactionMonth'] = df_cohort['InvoiceDate'].dt.to_period('M')

# Calculate cohort index (months since first purchase)
df_cohort['CohortIndex'] = (
    (df_cohort['TransactionMonth'].dt.year - df_cohort['CohortMonth'].dt.year) * 12
    + (df_cohort['TransactionMonth'].dt.month - df_cohort['CohortMonth'].dt.month)
)

# Cohort retention table: unique customers per cohort per period
cohort_data = df_cohort.groupby(['CohortMonth', 'CohortIndex'])['CustomerID'].nunique().reset_index()
cohort_data.columns = ['CohortMonth', 'CohortIndex', 'Customers']

# Pivot to matrix
cohort_matrix = cohort_data.pivot(index='CohortMonth', columns='CohortIndex', values='Customers')

# Calculate retention rates
cohort_sizes = cohort_matrix.iloc[:, 0]
retention = cohort_matrix.divide(cohort_sizes, axis=0) * 100

print(f"\nCohort count: {len(cohort_sizes)} monthly cohorts")
print(f"Largest cohort: {cohort_sizes.idxmax()} ({cohort_sizes.max():,} customers)")
print(f"Smallest cohort: {cohort_sizes.idxmin()} ({cohort_sizes.min():,} customers)")

# Average retention by month
avg_retention = retention.mean()
print(f"\nAverage retention by month after first purchase:")
for i in range(min(7, len(avg_retention))):
    if i == 0:
        print(f"  Month 0 (acquisition): 100%")
    else:
        print(f"  Month {i}: {avg_retention.iloc[i]:.1f}%")

# --- Visualization: Retention Heatmap ---
fig, ax = plt.subplots(figsize=(14, 10))

# Only show first 12 months and cohorts that have data
ret_display = retention.iloc[:, :13].copy()
ret_display.index = ret_display.index.astype(str)

sns.heatmap(ret_display, annot=True, fmt='.0f', cmap='YlOrRd_r',
            linewidths=0.5, ax=ax, vmin=0, vmax=100,
            cbar_kws={'label': 'Retention Rate (%)'})
ax.set_title('Monthly Cohort Retention Rates (%)', fontsize=16, fontweight='bold', pad=20)
ax.set_xlabel('Months Since First Purchase', fontsize=12)
ax.set_ylabel('Cohort (First Purchase Month)', fontsize=12)
plt.tight_layout()
plt.savefig('visualizations/cohort_retention_heatmap.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Saved: visualizations/cohort_retention_heatmap.png")

# Save cohort data
retention.to_csv("data/cohort_retention.csv")


# ══════════════════════════════════════════════════════════════════════
# LAYER 4: REVENUE DECOMPOSITION (NEW vs RETURNING)
# ══════════════════════════════════════════════════════════════════════
print("\n\n💰 LAYER 4: REVENUE DECOMPOSITION")
print("-" * 50)

# For each transaction, determine if the customer is "new" or "returning"
df_rev = df_clean.merge(customer_first[['CustomerID', 'FirstPurchaseDate']], on='CustomerID')
df_rev['CustomerType'] = np.where(
    df_rev['InvoiceDate'].dt.to_period('M') == df_rev['FirstPurchaseDate'].dt.to_period('M'),
    'New', 'Returning'
)

# Monthly revenue by customer type
monthly_rev = df_rev.groupby([df_rev['InvoiceDate'].dt.to_period('M'), 'CustomerType'])['Revenue'].sum().unstack(fill_value=0)
monthly_rev.index = monthly_rev.index.astype(str)

# Summary
total_new = monthly_rev['New'].sum()
total_ret = monthly_rev['Returning'].sum()
total_all = total_new + total_ret
print(f"\nRevenue breakdown:")
print(f"  New customers:       £{total_new:>12,.2f}  ({total_new/total_all*100:.1f}%)")
print(f"  Returning customers: £{total_ret:>12,.2f}  ({total_ret/total_all*100:.1f}%)")
print(f"  Total:               £{total_all:>12,.2f}")

# Monthly customer counts
monthly_custs = df_rev.groupby([df_rev['InvoiceDate'].dt.to_period('M'), 'CustomerType'])['CustomerID'].nunique().unstack(fill_value=0)
monthly_custs.index = monthly_custs.index.astype(str)

# --- Visualization: Revenue Decomposition ---
fig, axes = plt.subplots(2, 1, figsize=(14, 10))

# Stacked area: revenue
monthly_rev.plot.area(ax=axes[0], alpha=0.7, color=['#2196F3', '#4CAF50'])
axes[0].set_title('Monthly Revenue: New vs Returning Customers', fontsize=14, fontweight='bold')
axes[0].set_ylabel('Revenue (£)')
axes[0].legend(title='Customer Type')
axes[0].tick_params(axis='x', rotation=45)

# Stacked bar: customer count
monthly_custs.plot.bar(ax=axes[1], stacked=True, alpha=0.8, color=['#2196F3', '#4CAF50'])
axes[1].set_title('Monthly Customer Count: New vs Returning', fontsize=14, fontweight='bold')
axes[1].set_ylabel('Customers')
axes[1].legend(title='Customer Type')
axes[1].tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('visualizations/revenue_decomposition.png', dpi=150, bbox_inches='tight')
plt.close()
print("✓ Saved: visualizations/revenue_decomposition.png")

# Save
monthly_rev.to_csv("data/monthly_revenue_by_type.csv")


# ══════════════════════════════════════════════════════════════════════
# LAYER 5: CHURN RISK IDENTIFICATION
# ══════════════════════════════════════════════════════════════════════
print("\n\n⚠️  LAYER 5: CHURN RISK IDENTIFICATION")
print("-" * 50)

# At-risk: customers who used to buy regularly but have gone quiet
# Definition: bought 3+ times overall, but last purchase was 60+ days ago

at_risk = rfm[(rfm['Frequency'] >= 3) & (rfm['Recency'] > 60)].copy()
at_risk_segments = at_risk['Segment'].value_counts()
at_risk_revenue = at_risk['Monetary'].sum()

print(f"\nAt-risk customers (3+ purchases, inactive 60+ days):")
print(f"  Count: {len(at_risk):,}")
print(f"  Historical revenue: £{at_risk_revenue:,.2f}")
print(f"  Avg lifetime spend: £{at_risk['Monetary'].mean():,.2f}")
print(f"\n  By segment:")
for seg, cnt in at_risk_segments.items():
    rev = at_risk[at_risk['Segment'] == seg]['Monetary'].sum()
    print(f"    {seg}: {cnt} customers (£{rev:,.2f})")

# High-value at risk (top 20% by monetary value)
high_value_threshold = at_risk['Monetary'].quantile(0.8)
high_value_at_risk = at_risk[at_risk['Monetary'] >= high_value_threshold]
print(f"\n  🔴 HIGH-VALUE at risk (top 20%, spending ≥ £{high_value_threshold:,.2f}):")
print(f"     Count: {len(high_value_at_risk):,}")
print(f"     Revenue at stake: £{high_value_at_risk['Monetary'].sum():,.2f}")

# --- Visualization: Churn Risk ---
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Recency vs Monetary scatter, colored by segment
segment_colors = {
    'Champions': '#4CAF50', 'Loyal': '#8BC34A', 'Potential Loyalists': '#CDDC39',
    'New Customers': '#03A9F4', 'Needs Attention': '#FF9800',
    'At Risk': '#FF5722', 'Cannot Lose': '#F44336', 'Lost': '#9E9E9E'
}
for seg in rfm['Segment'].unique():
    mask = rfm['Segment'] == seg
    axes[0].scatter(rfm.loc[mask, 'Recency'], rfm.loc[mask, 'Monetary'],
                    alpha=0.4, label=seg, s=15,
                    color=segment_colors.get(seg, '#666'))
axes[0].set_xlabel('Recency (days since last purchase)')
axes[0].set_ylabel('Monetary (£ total spend)')
axes[0].set_title('Customer Segments: Recency vs Monetary', fontsize=13, fontweight='bold')
axes[0].legend(fontsize=8, loc='upper right')

# At-risk segment breakdown
at_risk_segments.plot.barh(ax=axes[1], color='#FF5722', alpha=0.8)
axes[1].set_xlabel('Number of Customers')
axes[1].set_title('At-Risk Customers by Segment', fontsize=13, fontweight='bold')
for i, v in enumerate(at_risk_segments.values):
    axes[1].text(v + 2, i, str(v), va='center', fontsize=10)

plt.tight_layout()
plt.savefig('visualizations/churn_risk.png', dpi=150, bbox_inches='tight')
plt.close()
print("\n✓ Saved: visualizations/churn_risk.png")


# ══════════════════════════════════════════════════════════════════════
# EXECUTIVE SUMMARY & RECOMMENDATIONS
# ══════════════════════════════════════════════════════════════════════
print("\n\n" + "=" * 70)
print("📋 EXECUTIVE SUMMARY & RECOMMENDATIONS")
print("=" * 70)

# Find best and worst retention cohorts
best_cohort = retention.iloc[:, 1].idxmax() if retention.shape[1] > 1 else 'N/A'
worst_cohort = retention.iloc[:, 1].idxmin() if retention.shape[1] > 1 else 'N/A'
best_ret = retention.iloc[:, 1].max() if retention.shape[1] > 1 else 0
worst_ret = retention.iloc[:, 1].min() if retention.shape[1] > 1 else 0

champions = rfm[rfm['Segment'] == 'Champions']
lost = rfm[rfm['Segment'] == 'Lost']

print(f"""
KEY FINDINGS:

1. CUSTOMER SEGMENTS:
   • {len(rfm):,} customers segmented using RFM analysis
   • Champions ({len(champions):,} customers, {len(champions)/len(rfm)*100:.1f}%) drive 
     £{champions['Monetary'].sum():,.0f} in revenue
   • {len(lost):,} customers classified as "Lost" — {len(lost)/len(rfm)*100:.1f}% of base

2. RETENTION:
   • Best Month-1 retention: {best_cohort} ({best_ret:.0f}%)
   • Worst Month-1 retention: {worst_cohort} ({worst_ret:.0f}%)
   • Average Month-1 retention: {avg_retention.iloc[1]:.0f}% — significant drop-off after first purchase

3. REVENUE COMPOSITION:
   • Returning customers drive {total_ret/total_all*100:.0f}% of total revenue
   • New customer acquisition is important but retention is the growth lever

4. CHURN RISK:
   • {len(at_risk):,} customers at risk of churning (3+ purchases but inactive 60+ days)
   • £{at_risk_revenue:,.0f} in historical revenue at stake
   • {len(high_value_at_risk):,} are high-value — priority for re-engagement

RECOMMENDATIONS:

1. RETENTION FOCUS: Month-1 retention drops sharply — implement a 
   "second purchase" campaign (discount/reminder) within 30 days of first order.

2. CHAMPION PROGRAM: The {len(champions):,} Champions drive disproportionate revenue.
   Create a loyalty program or early-access program to keep them engaged.

3. WIN-BACK CAMPAIGN: Target the {len(high_value_at_risk):,} high-value at-risk customers
   with personalized re-engagement (they've already proven they'll spend — 
   avg £{high_value_at_risk['Monetary'].mean():,.0f} lifetime).

4. COHORT INVESTIGATION: {best_cohort} cohort retains best — investigate what 
   campaign, season, or product drove that. Replicate for future cohorts.

5. REDUCE FIRST-ORDER CHURN: {len(lost)/len(rfm)*100:.0f}% of customers are "Lost" 
   (low recency, low frequency). Improve onboarding experience and 
   post-purchase follow-up to prevent one-and-done behavior.
""")

# Save summary
with open("output/executive_summary.txt", "w") as f:
    f.write(f"Customer Analytics - Executive Summary\n")
    f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    f.write(f"\nTotal Customers: {len(rfm):,}\n")
    f.write(f"Total Revenue: £{rfm['Monetary'].sum():,.2f}\n")
    f.write(f"At-Risk Customers: {len(at_risk):,}\n")
    f.write(f"Revenue at Risk: £{at_risk_revenue:,.2f}\n")
    f.write(f"Returning Customer Revenue Share: {total_ret/total_all*100:.0f}%\n")

# Save all analysis data for Power BI
df_clean.to_csv("data/online_retail_clean.csv", index=False)
print("\n✓ All data files saved in data/")
print("✓ All visualizations saved in visualizations/")
print("✓ Executive summary saved in output/")
print("\n🎯 Ready for SQL analysis and Power BI dashboard.")
