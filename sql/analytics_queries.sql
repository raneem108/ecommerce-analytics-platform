/*SELECT 
    ROUND(SUM(oi.subtotal)::numeric, 2) AS total_revenue,
    COUNT(DISTINCT o.order_id)          AS total_orders,
    COUNT(DISTINCT o.customer_id)       AS unique_customers,
    ROUND(AVG(oi.subtotal)::numeric, 2) AS avg_item_value
FROM orders o
JOIN order_items oi ON o.order_id = oi.order_id
WHERE o.status = 'completed';

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
*/