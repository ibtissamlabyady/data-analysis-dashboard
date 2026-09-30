### Metric definitions

The unit of analysis is **one order with one product**. Quantities may exceed one.
All money is in **Moroccan dirhams (MAD)**, stored as integer centimes. The demo has
one currency and no currency conversion.

| Metric | Definition |
| --- | --- |
| Net revenue | Sum of quantity × unit price × (1 − discount / 100), for Completed orders only. Each order is rounded half up to the nearest centime. |
| Gross profit | Net revenue − quantity × unit cost for Completed orders. This is not net profit. |
| Completed orders | Count of unique orders with status Completed. |
| Average order value | Net revenue / completed orders. N/A when there are no completed orders. |
| Gross margin | Total gross profit / total net revenue. N/A when revenue is zero. It is not the mean of individual order margins. |
| Return rate | Returned orders / (Completed + Returned orders), grouped by original order date. Cancelled orders are excluded from the denominator. |
| Cancelled orders | Count of orders with status Cancelled. |
| Prior-period change | (Current − previous) / abs(previous) × 100, using the same segments and an immediately preceding interval of equal inclusive day count. Unavailable if that interval exceeds source coverage or the baseline is zero. |

### Accounting assumptions

- Returned orders are fully refunded and their product cost is fully reversed. They contribute zero revenue and gross profit.
- Cancelled orders contribute zero revenue and cost. No partial refunds are modeled.
- Order dates describe cohorts; there is no separate return event date or cash-flow accounting.
- Taxes, shipping, marketing, payment fees, and operating expenses are not modeled.
- All filters apply to KPIs, charts, product tables, prior-period comparisons, and the export.
- Daily charts fill days without matching orders with zero. Weekly buckets start on Monday; monthly buckets start on the first day. Boundary buckets can be partial.

### Data quality rules

Whitespace is trimmed from text fields and exact duplicate records are removed.
Missing fields, blank values, conflicting order IDs, invalid ISO dates, unknown
categories/statuses, fractional quantities, and invalid monetary ranges fail
validation with an error. Invalid records are not silently dropped.

This is a **synthetic portfolio demonstration**, not evidence of business impact.
