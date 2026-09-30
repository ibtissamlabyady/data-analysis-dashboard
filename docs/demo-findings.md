# Reproducible demo findings

Scope: **1 January–31 December 2025**, all regions, categories and channels.
These results describe generated data only; they are not client outcomes.

| Metric | Value |
| --- | --- |
| Net revenue | MAD 2,443,505.90 |
| Gross profit | MAD 1,030,655.90 |
| Completed orders | 3,828 |
| Average order value | MAD 638.32 |
| Gross margin | 42.18% |
| Return rate | 6.20% |

The highest-revenue product in this generated sample is **Wireless headphones**,
with MAD 543,336.15 in net revenue and 38.78% gross margin.
Revenue leadership alone is not a recommendation to increase inventory: demand,
stock availability, and operating costs are not represented in the dataset.

Across the full two-year source, validation retains **7,806** orders
from 7,824 rows, removes **18** exact duplicates,
and trims **100** padded text cells.

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
