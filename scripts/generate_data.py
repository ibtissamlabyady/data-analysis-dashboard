"""Generate fictional orders, including deliberate duplicate/whitespace issues."""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 42
START = date(2024, 1, 1)
END = date(2025, 12, 31)
PRODUCTS = [
    ("Wireless headphones", "Electronics", 49900, 29000),
    ("Bluetooth speaker", "Electronics", 34900, 21000),
    ("Desk lamp", "Home", 24900, 12500),
    ("Storage set", "Home", 17900, 9500),
    ("Laptop stand", "Office", 29900, 16000),
    ("Notebook pack", "Office", 8900, 4000),
    ("Travel bag", "Accessories", 39900, 23000),
    ("Phone case", "Accessories", 9900, 3500),
]


def generate_rows():
    rng = random.Random(SEED)
    rows = []
    day = START
    while day <= END:
        count = rng.randint(5, 12) + (2 if day.year == 2025 else 0)
        count += (4 if day.month in (11, 12) else 0) + (2 if day.weekday() >= 5 else 0)
        for _ in range(count):
            product, category, price, cost = rng.choice(PRODUCTS)
            rows.append({
                "order_id": f"ORD-{len(rows) + 1:06d}",
                "order_date": day.isoformat(),
                "region": rng.choices(["North", "Central", "South", "West"], [2, 4, 2, 3])[0],
                "channel": rng.choices(["Online", "Store"], [3, 2])[0],
                "product": product,
                "category": category,
                "quantity": rng.randint(1, 4),
                "unit_price_cents": price,
                "unit_cost_cents": cost,
                "discount_pct": rng.choices([0, 10, 15, 20], [6, 2, 1, 1])[0],
                "status": rng.choices(["Completed", "Returned", "Cancelled"], [90, 6, 4])[0],
            })
        day += timedelta(days=1)
    for i in range(0, len(rows), 79):
        rows[i]["region"] = f" {rows[i]['region']} "
    rows.extend(dict(row) for row in rows[:18])
    return rows


def main():
    destination = ROOT / "data" / "sales_raw.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)
    rows = generate_rows()
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys(), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows):,} synthetic rows to {destination}")


if __name__ == "__main__":
    main()
