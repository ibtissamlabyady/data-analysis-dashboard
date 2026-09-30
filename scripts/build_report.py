"""Export clean facts, SQL monthly results, and a reproducible findings note."""

from datetime import date
from pathlib import Path

import pandas as pd

from src.analytics import ROOT, DATA_PATH, build_database, clean_orders, filter_sales, load_sales, metrics, segment_sales


def main():
    sales, quality = load_sales()
    clean, _ = clean_orders(pd.read_csv(DATA_PATH))
    conn = build_database(clean)
    try:
        monthly = pd.read_sql_query(
            (ROOT / "sql" / "monthly_sales.sql").read_text(encoding="utf-8"),
            conn, params={"start": "2025-01-01", "end": "2025-12-31"},
        )
    finally:
        conn.close()
    selected = filter_sales(sales, date(2025, 1, 1), date(2025, 12, 31),
                            sales.region.unique(), sales.category.unique(), sales.channel.unique())
    result = metrics(selected)
    products = segment_sales(selected, "product")
    top = products.iloc[0]
    output = ROOT / "output"
    output.mkdir(exist_ok=True)
    sales.to_csv(output / "sales_clean.csv", index=False, date_format="%Y-%m-%d")
    monthly.to_csv(output / "monthly_sales_2025.csv", index=False)
    report = f"""# Reproducible demo findings

Scope: **1 January–31 December 2025**, all regions, categories and channels.
These results describe generated data only; they are not client outcomes.

| Metric | Value |
| --- | --- |
| Net revenue | MAD {result['revenue']:,.2f} |
| Gross profit | MAD {result['profit']:,.2f} |
| Completed orders | {result['orders']:,} |
| Average order value | MAD {result['aov']:,.2f} |
| Gross margin | {result['margin']:.2%} |
| Return rate | {result['return_rate']:.2%} |

The highest-revenue product in this generated sample is **{top['product']}**,
with MAD {top['Revenue (MAD)']:,.2f} in net revenue and {top['Margin']:.2%} gross margin.
Revenue leadership alone is not a recommendation to increase inventory: demand,
stock availability, and operating costs are not represented in the dataset.

Across the full two-year source, validation retains **{quality.clean_rows:,}** orders
from {quality.source_rows:,} rows, removes **{quality.duplicates_removed}** exact duplicates,
and trims **{quality.whitespace_cells_fixed}** padded text cells.

## Reproduce

```bash
python -m scripts.generate_data
python -m scripts.build_report
```

The second command writes `output/sales_clean.csv`, `output/monthly_sales_2025.csv`,
and this file. Output CSVs are local artifacts and are excluded from Git.
The monthly aggregation executes `sql/monthly_sales.sql` in SQLite.

## Interpretation limits

- Order growth and seasonal patterns are deliberately programmed into the generator.
- Gross profit excludes operating expenses and is not net profit.
- Returns are fully reversed and attributed to the original order date.
- No time-saving, forecasting accuracy, or production-performance claim is made.
"""
    path = ROOT / "docs" / "demo-findings.md"
    path.write_text(report, encoding="utf-8")
    print(f"Report: {path}")
    print(f"2025 revenue: MAD {result['revenue']:,.2f}; completed orders: {result['orders']:,}")


if __name__ == "__main__":
    main()
