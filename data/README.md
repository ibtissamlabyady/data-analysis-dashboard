# Dataset and provenance

`sales_raw.csv` is generated entirely by `scripts/generate_data.py` using Python's
standard library and random seed **42**. Atlas Retail is a fictional business.
There are no real customers, employers, transactions, or scraped records.

Coverage: **2024-01-01 through 2025-12-31**, including every calendar day. The
generator deliberately increases order volume in 2025, in November/December,
and on weekends. Any observed growth is a property of the generator, not a
real market finding or a forecast.

The file includes **18 exact duplicates** and padded region labels to demonstrate
cleaning. The clean dataset retains one row per order; each order has one product.

## Data dictionary

| Field | Type / unit | Meaning |
| --- | --- | --- |
| order_id | Text | Synthetic unique order identifier after deduplication |
| order_date | YYYY-MM-DD | Original order date |
| region | North, Central, South, West | Fictional sales region |
| channel | Online, Store | Sales channel |
| product | Text | Fictional product name |
| category | Electronics, Home, Office, Accessories | Product category |
| quantity | Positive integer | Units per order |
| unit_price_cents | Positive integer, MAD centimes | Price per unit before discount |
| unit_cost_cents | Nonnegative integer, MAD centimes | Product cost per unit |
| discount_pct | Integer 0–100 | Percentage discount |
| status | Completed, Returned, Cancelled | Final order state |

SQL adds order value, order cost, recognized revenue, recognized cost, and gross
profit in integer centimes. See [metric definitions](../docs/metric-definitions.md).

To regenerate the committed CSV from the repository root:

```bash
python -m scripts.generate_data
```

The first version does not accept arbitrary uploaded CSV files. To replace the
source, adapt this documented schema and its allowed-value rules, then rerun the
validation tests. Dataset regeneration intentionally overwrites `sales_raw.csv`.
