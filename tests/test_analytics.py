import sqlite3
import unittest
from datetime import date

import pandas as pd

from scripts.generate_data import generate_rows
from src.analytics import (
    ROOT, build_database, clean_orders, daily_sales, filter_sales,
    metrics, percent_change, previous_period,
)


def sample_orders():
    base = dict(order_date="2025-01-01", region="North", channel="Online", product="Test product",
                category="Home", quantity=2, unit_price_cents=10000, unit_cost_cents=6000,
                discount_pct=10, status="Completed")
    return pd.DataFrame([
        dict(base, order_id="A"),
        dict(base, order_id="B", order_date="2025-01-02", quantity=1, unit_cost_cents=4000, discount_pct=0),
        dict(base, order_id="C", status="Returned"),
        dict(base, order_id="D", status="Cancelled"),
    ])


def facts(raw):
    clean, _ = clean_orders(raw)
    conn = build_database(clean)
    try:
        frame = pd.read_sql_query("SELECT * FROM sales_fact", conn)
    finally:
        conn.close()
    frame["order_date"] = pd.to_datetime(frame["order_date"])
    return frame


class AnalyticsTests(unittest.TestCase):
    def test_revenue_profit_and_weighted_margin_exclude_returns_and_cancellations(self):
        result = metrics(facts(sample_orders()))
        self.assertEqual(result["revenue"], 280)
        self.assertEqual(result["profit"], 120)
        self.assertEqual(result["orders"], 2)
        self.assertEqual(result["aov"], 140)
        self.assertAlmostEqual(result["margin"], 120 / 280)
        self.assertAlmostEqual(result["return_rate"], 1 / 3)

    def test_whitespace_and_exact_duplicates_are_cleaned(self):
        raw = sample_orders()
        raw.loc[0, "region"] = " North "
        raw = pd.concat([raw, raw.iloc[[0]]], ignore_index=True)
        clean, report = clean_orders(raw)
        self.assertEqual(len(clean), 4)
        self.assertEqual(report.duplicates_removed, 1)
        self.assertEqual(report.whitespace_cells_fixed, 2)
        self.assertEqual(set(clean.region), {"North"})

    def test_conflicting_order_ids_fail(self):
        raw = sample_orders()
        raw.loc[1, "order_id"] = "A"
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            clean_orders(raw)

    def test_invalid_data_fails_instead_of_silent_exclusion(self):
        cases = [("order_date", "2025-02-30"), ("order_date", "01/02/2025"),
                 ("status", "Refunded"), ("region", None), ("product", " "),
                 ("quantity", 0), ("quantity", 1.5), ("discount_pct", 101),
                 ("unit_cost_cents", -1), ("unit_price_cents", float("inf"))]
        for column, value in cases:
            with self.subTest(column=column, value=value):
                raw = sample_orders().astype(object)
                raw.loc[0, column] = value
                with self.assertRaises(ValueError):
                    clean_orders(raw)

    def test_missing_columns_and_empty_source_fail(self):
        for raw in [sample_orders().drop(columns="status"), sample_orders().iloc[:0]]:
            with self.assertRaises(ValueError):
                clean_orders(raw)

    def test_cent_rounding_is_half_up(self):
        raw = sample_orders().iloc[[0]].copy()
        raw.loc[0, ["quantity", "unit_price_cents", "discount_pct"]] = [1, 101, 50]
        self.assertEqual(facts(raw).iloc[0].revenue_cents, 51)

    def test_filters_are_inclusive_and_empty_selection_means_no_orders(self):
        sales = facts(sample_orders())
        chosen = filter_sales(sales, date(2025, 1, 2), date(2025, 1, 2), ["North"], ["Home"], ["Online"])
        self.assertEqual(chosen.order_id.tolist(), ["B"])
        empty = filter_sales(sales, date(2025, 1, 1), date(2025, 1, 2), [], ["Home"], ["Online"])
        self.assertTrue(empty.empty)
        self.assertIsNone(metrics(empty)["aov"])
        self.assertIsNone(metrics(empty)["margin"])

    def test_previous_period_handles_leap_year_and_zero_baseline(self):
        self.assertEqual(previous_period(date(2024, 3, 1), date(2024, 3, 2)), (date(2024, 2, 28), date(2024, 2, 29)))
        self.assertIsNone(percent_change(10, 0))
        self.assertEqual(percent_change(120, 100), 20)

    def test_time_series_includes_zero_sales_days(self):
        trend = daily_sales(facts(sample_orders()), date(2025, 1, 1), date(2025, 1, 3))
        self.assertEqual(trend.Revenue.tolist(), [180, 100, 0])

    def test_sql_monthly_report_matches_hand_calculated_totals(self):
        clean, _ = clean_orders(sample_orders())
        conn = build_database(clean)
        try:
            result = conn.execute((ROOT / "sql/monthly_sales.sql").read_text(), {"start": "2025-01-01", "end": "2025-01-31"}).fetchall()
        finally:
            conn.close()
        self.assertEqual(result, [("2025-01", 2, 280.0, 120.0)])

    def test_zero_revenue_margin_is_undefined(self):
        raw = sample_orders().iloc[[0]].copy()
        raw["discount_pct"] = 100
        result = metrics(facts(raw))
        self.assertEqual(result["aov"], 0)
        self.assertIsNone(result["margin"])

    def test_generator_is_reproducible_and_covers_every_day(self):
        rows = generate_rows()
        self.assertEqual(rows, generate_rows())
        clean, report = clean_orders(pd.DataFrame(rows))
        self.assertEqual(report.duplicates_removed, 18)
        self.assertEqual(clean.order_date.nunique(), 731)


if __name__ == "__main__":
    unittest.main()
