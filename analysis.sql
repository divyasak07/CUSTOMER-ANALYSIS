-- ============================================================
-- Customer Analytics: Segmentation, Retention & Revenue — SQL
-- ============================================================
-- Author: Oshi Sharma
-- Data:   online_retail_clean.csv (loaded as: online_retail)
-- ============================================================


-- ─────────────────────────────────────────────────────
-- Q1: RFM Metrics per Customer
-- ─────────────────────────────────────────────────────
WITH reference AS (
    SELECT DATE(MAX(InvoiceDate), '+1 day') AS ref_date
    FROM online_retail
)
SELECT
    CustomerID,
    CAST(julianday(ref_date) - julianday(MAX(InvoiceDate)) AS INT) AS Recency,
    COUNT(DISTINCT InvoiceNo) AS Frequency,
    ROUND(SUM(Quantity * UnitPrice), 2) AS Monetary
FROM online_retail, reference
GROUP BY CustomerID
ORDER BY Monetary DESC;


-- ─────────────────────────────────────────────────────
-- Q2: Revenue by Customer Segment
-- ─────────────────────────────────────────────────────
SELECT
    Segment,
    COUNT(*) AS Customers,
    ROUND(AVG(Recency), 1) AS Avg_Recency,
    ROUND(AVG(Frequency), 1) AS Avg_Frequency,
    ROUND(SUM(Monetary), 2) AS Total_Revenue,
    ROUND(SUM(Monetary) * 100.0 / (SELECT SUM(Monetary) FROM rfm_segments), 1) AS Revenue_Pct
FROM rfm_segments
GROUP BY Segment
ORDER BY Total_Revenue DESC;


-- ─────────────────────────────────────────────────────
-- Q3: Monthly Cohort Retention (Window Function)
-- ─────────────────────────────────────────────────────
WITH first_purchase AS (
    SELECT
        CustomerID,
        strftime('%Y-%m', MIN(InvoiceDate)) AS CohortMonth
    FROM online_retail
    GROUP BY CustomerID
),
monthly_activity AS (
    SELECT DISTINCT
        o.CustomerID,
        f.CohortMonth,
        strftime('%Y-%m', o.InvoiceDate) AS ActivityMonth,
        (CAST(strftime('%Y', o.InvoiceDate) AS INT) - CAST(substr(f.CohortMonth,1,4) AS INT)) * 12
        + (CAST(strftime('%m', o.InvoiceDate) AS INT) - CAST(substr(f.CohortMonth,6,2) AS INT)) AS CohortIndex
    FROM online_retail o
    JOIN first_purchase f ON o.CustomerID = f.CustomerID
)
SELECT
    CohortMonth,
    CohortIndex,
    COUNT(DISTINCT CustomerID) AS ActiveCustomers
FROM monthly_activity
GROUP BY CohortMonth, CohortIndex
ORDER BY CohortMonth, CohortIndex;


-- ─────────────────────────────────────────────────────
-- Q4: New vs Returning Revenue by Month
-- ─────────────────────────────────────────────────────
WITH first_purchase AS (
    SELECT
        CustomerID,
        strftime('%Y-%m', MIN(InvoiceDate)) AS FirstMonth
    FROM online_retail
    GROUP BY CustomerID
)
SELECT
    strftime('%Y-%m', o.InvoiceDate) AS Month,
    CASE
        WHEN strftime('%Y-%m', o.InvoiceDate) = f.FirstMonth THEN 'New'
        ELSE 'Returning'
    END AS CustomerType,
    COUNT(DISTINCT o.CustomerID) AS Customers,
    ROUND(SUM(o.Quantity * o.UnitPrice), 2) AS Revenue
FROM online_retail o
JOIN first_purchase f ON o.CustomerID = f.CustomerID
GROUP BY Month, CustomerType
ORDER BY Month, CustomerType;


-- ─────────────────────────────────────────────────────
-- Q5: At-Risk Customers (High Value, Gone Quiet)
-- ─────────────────────────────────────────────────────
SELECT
    CustomerID,
    Segment,
    Recency,
    Frequency,
    ROUND(Monetary, 2) AS Monetary
FROM rfm_segments
WHERE Frequency >= 3
  AND Recency > 60
ORDER BY Monetary DESC
LIMIT 20;


-- ─────────────────────────────────────────────────────
-- Q6: Top 10 Customers by Lifetime Value
-- ─────────────────────────────────────────────────────
SELECT
    CustomerID,
    COUNT(DISTINCT InvoiceNo) AS Orders,
    COUNT(DISTINCT strftime('%Y-%m', InvoiceDate)) AS Active_Months,
    ROUND(SUM(Quantity * UnitPrice), 2) AS Lifetime_Revenue,
    ROUND(AVG(Quantity * UnitPrice), 2) AS Avg_Order_Value,
    MIN(DATE(InvoiceDate)) AS First_Purchase,
    MAX(DATE(InvoiceDate)) AS Last_Purchase
FROM online_retail
GROUP BY CustomerID
ORDER BY Lifetime_Revenue DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────
-- Q7: Product Performance — Top 10 by Revenue
-- ─────────────────────────────────────────────────────
SELECT
    StockCode,
    Description,
    SUM(Quantity) AS Units_Sold,
    COUNT(DISTINCT InvoiceNo) AS Orders,
    COUNT(DISTINCT CustomerID) AS Unique_Buyers,
    ROUND(SUM(Quantity * UnitPrice), 2) AS Total_Revenue
FROM online_retail
WHERE StockCode NOT IN ('POST', 'DOT', 'M', 'BANK CHARGES', 'C2')
GROUP BY StockCode, Description
ORDER BY Total_Revenue DESC
LIMIT 10;


-- ─────────────────────────────────────────────────────
-- Q8: Country-Level Revenue Analysis
-- ─────────────────────────────────────────────────────
SELECT
    Country,
    COUNT(DISTINCT CustomerID) AS Customers,
    COUNT(DISTINCT InvoiceNo) AS Orders,
    ROUND(SUM(Quantity * UnitPrice), 2) AS Revenue,
    ROUND(SUM(Quantity * UnitPrice) / COUNT(DISTINCT CustomerID), 2) AS Revenue_Per_Customer
FROM online_retail
GROUP BY Country
ORDER BY Revenue DESC;


-- ─────────────────────────────────────────────────────
-- Q9: Purchase Frequency Distribution
-- ─────────────────────────────────────────────────────
WITH customer_orders AS (
    SELECT CustomerID, COUNT(DISTINCT InvoiceNo) AS OrderCount
    FROM online_retail
    GROUP BY CustomerID
)
SELECT
    CASE
        WHEN OrderCount = 1 THEN '1 order'
        WHEN OrderCount BETWEEN 2 AND 5 THEN '2-5 orders'
        WHEN OrderCount BETWEEN 6 AND 10 THEN '6-10 orders'
        WHEN OrderCount BETWEEN 11 AND 20 THEN '11-20 orders'
        ELSE '20+ orders'
    END AS Frequency_Bucket,
    COUNT(*) AS Customers,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM customer_orders), 1) AS Pct
FROM customer_orders
GROUP BY Frequency_Bucket
ORDER BY MIN(OrderCount);


-- ─────────────────────────────────────────────────────
-- Q10: Monthly Business Health Dashboard
-- ─────────────────────────────────────────────────────
SELECT
    strftime('%Y-%m', InvoiceDate) AS Month,
    COUNT(DISTINCT CustomerID) AS Active_Customers,
    COUNT(DISTINCT InvoiceNo) AS Orders,
    ROUND(SUM(Quantity * UnitPrice), 2) AS Revenue,
    ROUND(SUM(Quantity * UnitPrice) / COUNT(DISTINCT InvoiceNo), 2) AS Avg_Order_Value,
    ROUND(SUM(Quantity * UnitPrice) / COUNT(DISTINCT CustomerID), 2) AS Revenue_Per_Customer
FROM online_retail
GROUP BY Month
ORDER BY Month;
