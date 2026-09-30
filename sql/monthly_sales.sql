-- Dates are inclusive; bind values instead of interpolating SQL strings.
SELECT substr(order_date, 1, 7) AS month,
    SUM(CASE WHEN status = 'Completed' THEN 1 ELSE 0 END) AS completed_orders,
    SUM(revenue_cents) / 100.0 AS revenue_mad,
    SUM(profit_cents) / 100.0 AS gross_profit_mad
FROM sales_fact
WHERE order_date BETWEEN :start AND :end
GROUP BY substr(order_date, 1, 7)
ORDER BY month;
