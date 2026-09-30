-- One row per order, with a single product per order in this demo.
-- Integer cents and half-up rounding avoid floating-point currency drift.
CREATE VIEW sales_fact AS
WITH amounts AS (
    SELECT *,
        CAST((quantity * unit_price_cents * (100 - discount_pct) + 50) / 100 AS INTEGER)
            AS order_value_cents,
        quantity * unit_cost_cents AS order_cost_cents
    FROM orders
)
SELECT *,
    CASE WHEN status = 'Completed' THEN order_value_cents ELSE 0 END AS revenue_cents,
    CASE WHEN status = 'Completed' THEN order_cost_cents ELSE 0 END AS cogs_cents,
    CASE WHEN status = 'Completed' THEN order_value_cents - order_cost_cents ELSE 0 END
        AS profit_cents
FROM amounts;
