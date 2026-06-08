
/* 
    Analytics Queries for E-commerce Data
    ------------------------------------
    This file contains SQL queries to analyze sales performance, customer behavior, and product trends.
    The queries are designed to provide insights into revenue, order patterns, and category performance.
*/

/* 
    1. Overall Sales Performance
    ---------------------------
    This query calculates total revenue, total orders, unique customers, and average item value for completed orders.
*/
SELECT 
    ROUND(SUM(oi.subtotal)::numeric, 2) AS total_revenue,
    COUNT(DISTINCT o.order_id)          AS total_orders,
    COUNT(DISTINCT o.customer_id)       AS unique_customers,
    ROUND(AVG(oi.subtotal)::numeric, 2) AS avg_item_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'completed';


/* 
    2. Sales by Product Category
    ----------------------------
    This query breaks down sales performance by product category, showing total orders, units sold, revenue, average price, and revenue percentage.
*/



SELECT 
    p.category,
    COUNT(DISTINCT o.order_id)          AS total_orders,
    SUM(oi.quantity)                    AS units_sold,
    ROUND(SUM(oi.subtotal)::numeric, 2) AS revenue,
    ROUND(AVG(p.price)::numeric, 2)     AS avg_price,
    ROUND(
        (SUM(oi.subtotal) / SUM(SUM(oi.subtotal)) OVER () * 100)::numeric, 1
    ) AS revenue_pct 
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p     ON oi.product_id = p.product_id
WHERE o.status = 'completed'
GROUP BY p.category
ORDER BY revenue DESC;

/* 
    3. Monthly Sales Trends
    ----------------------
    This query analyzes monthly sales trends, showing revenue, order count, previous month revenue, and month-over-month growth percentage.
*/


SELECT 
    TO_CHAR(o.order_date::date, 'YYYY-MM') AS month,
    ROUND(SUM(oi.subtotal)::numeric, 2)    AS revenue,
    COUNT(DISTINCT o.order_id)             AS orders,
    ROUND(
        LAG(SUM(oi.subtotal)::numeric) 
        OVER (ORDER BY TO_CHAR(o.order_date::date, 'YYYY-MM'))
    , 2)                                   AS prev_month_revenue,
    ROUND(
        (SUM(oi.subtotal)::numeric - LAG(SUM(oi.subtotal)::numeric) 
            OVER (ORDER BY TO_CHAR(o.order_date::date, 'YYYY-MM')))
        / NULLIF(LAG(SUM(oi.subtotal)::numeric) 
            OVER (ORDER BY TO_CHAR(o.order_date::date, 'YYYY-MM')), 0)
        * 100
    , 1)                                   AS mom_growth_pct
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'completed'
GROUP BY TO_CHAR(o.order_date::date, 'YYYY-MM')
ORDER BY month;

/* 
    4. Top Customers by Revenue
    --------------------------
    This query identifies the top 10 customers based on total revenue, showing their name, segment, country, total orders, total spent, average order value, and order dates.
*/


SELECT 
    c.customer_id,
    c.name,
    c.segment,
    c.country,
    COUNT(DISTINCT o.order_id)          AS total_orders,
    ROUND(SUM(oi.subtotal)::numeric, 2) AS total_spent,
    ROUND(AVG(oi.subtotal)::numeric, 2) AS avg_order_value,
    MIN(o.order_date::date)             AS first_order,
    MAX(o.order_date::date)             AS last_order
FROM customers c
JOIN orders o     ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'completed'
GROUP BY c.customer_id, c.name, c.segment, c.country
ORDER BY total_spent DESC
LIMIT 10;

/* 
    5. Product Profitability Analysis
    --------------------------------
    This query evaluates product profitability by calculating selling price, cost, gross profit, margin percentage, units sold, and total profit for each product.
*/

SELECT 
    p.name,
    p.category,
    ROUND(p.price::numeric, 2)                    AS selling_price,
    ROUND(p.cost::numeric, 2)                     AS cost,
    ROUND((p.price - p.cost)::numeric, 2)         AS gross_profit,
    ROUND(
        ((p.price - p.cost) / p.price * 100)::numeric, 1
    )                                             AS margin_pct,
    SUM(oi.quantity)                              AS units_sold,
    ROUND(
        (SUM(oi.quantity) * (p.price - p.cost))::numeric, 2
    )                                             AS total_profit
FROM products p
JOIN order_items oi ON p.product_id = oi.product_id
JOIN orders o       ON oi.order_id = o.order_id
WHERE o.status = 'completed'
GROUP BY p.product_id, p.name, p.category, p.price, p.cost
ORDER BY total_profit DESC;


/* 
    6. Customer Churn Analysis
    -------------------------
    This query identifies customers who have not made a purchase in the last 180 days, showing their last order date, total orders, total spent, and churn status.
*/

WITH last_order AS (
    SELECT 
        c.customer_id,
        c.name,
        c.segment,
        c.country,
        MAX(o.order_date::date)                    AS last_order_date,
        COUNT(DISTINCT o.order_id)                 AS total_orders,
        ROUND(SUM(oi.subtotal)::numeric, 2)        AS total_spent
    FROM customers c
    JOIN orders o      ON c.customer_id = o.customer_id
    JOIN order_items oi ON o.order_id  = oi.order_id
    WHERE o.status = 'completed'
    GROUP BY c.customer_id, c.name, c.segment, c.country
)
SELECT 
    customer_id,
    name,
    segment,
    country,
    last_order_date,
    total_orders,
    total_spent,
    -- How many days since their last order?
    ('2024-12-31'::date - last_order_date)         AS days_since_order,
    -- Label them as churned if no order in 180 days
    CASE 
        WHEN ('2024-12-31'::date - last_order_date) > 180 
        THEN 'Churned'
        ELSE 'Active'
    END                                            AS churn_status
FROM last_order
ORDER BY days_since_order DESC;

/* 
    7. Repeat vs One-Time Customers
    -----------------------------
    This query categorizes customers as 'Repeat' or 'One-Time' based on their order count, showing the number of customers in each category and their average spending.
*/

WITH customer_stats AS (
    SELECT
        o.customer_id,
        COUNT(DISTINCT o.order_id)         AS order_count,
        ROUND(SUM(oi.subtotal)::numeric, 2) AS total_spent
    FROM orders o
    JOIN order_items oi ON o.order_id = oi.order_id
    WHERE o.status = 'completed'
    GROUP BY o.customer_id
)
SELECT
    CASE
        WHEN order_count > 1 THEN 'Repeat'
        ELSE 'One-Time'
    END                          AS customer_type,
    COUNT(*)                     AS customer_count,
    ROUND(AVG(total_spent)::numeric, 2) AS avg_spending
FROM customer_stats
GROUP BY
    CASE
        WHEN order_count > 1 THEN 'Repeat'
        ELSE 'One-Time'
    END
ORDER BY customer_type;


/* 
    8. Sales by Country
    ------------------
    This query analyzes sales performance by country, showing total orders and total revenue for each country.
*/

SELECT
    c.country,
    COUNT(DISTINCT o.order_id) AS total_orders,
    ROUND(SUM(oi.subtotal)::numeric, 2) AS total_revenue
FROM orders o , customers c , order_items oi 
where  o.customer_id = c.customer_id and o.order_id = oi.order_id and
status = 'completed'
GROUP BY country
ORDER BY total_revenue DESC;



/* 
    9. Customer Segmentation Analysis
    --------------------------------
    This query analyzes sales performance by customer segment, showing the number of customers, total orders, total revenue, average order value, and revenue per customer for each segment.
*/

SELECT 
    c.segment,
    COUNT(DISTINCT c.customer_id)              AS customers,
    COUNT(DISTINCT o.order_id)                 AS total_orders,
    ROUND(SUM(oi.subtotal)::numeric, 2)        AS total_revenue,
    ROUND(AVG(oi.subtotal)::numeric, 2)        AS avg_order_value,
    ROUND(
        SUM(oi.subtotal)::numeric / 
        COUNT(DISTINCT c.customer_id)::numeric
    , 2)                                       AS revenue_per_customer
FROM customers c
JOIN orders o       ON c.customer_id = o.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'completed'
GROUP BY c.segment
ORDER BY total_revenue DESC;


/* 
    10. Quarterly Sales Performance by Segment
    ---------------------------------------
    This query breaks down quarterly sales performance by customer segment, showing the number of orders, total revenue, and average order value for each segment in each quarter.
*/



SELECT
    DATE_PART('year', o.order_date::date)      AS year,
    DATE_PART('quarter', o.order_date::date)   AS quarter,
    c.segment,
    COUNT(DISTINCT o.order_id)                 AS orders,
    ROUND(SUM(oi.subtotal)::numeric, 2)        AS revenue,
    ROUND(AVG(oi.subtotal)::numeric, 2)        AS avg_order_value
FROM orders o
JOIN customers c    ON o.customer_id = c.customer_id
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'completed'
GROUP BY 
    DATE_PART('year', o.order_date::date),
    DATE_PART('quarter', o.order_date::date),
    c.segment
ORDER BY year, quarter, revenue DESC;