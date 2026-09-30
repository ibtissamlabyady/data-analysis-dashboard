"""Pure data logic. Money stays in integer cents until presentation."""

import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "sales_raw.csv"
TEXT_COLUMNS = ["order_id", "order_date", "region", "channel", "product", "category", "status"]
NUMBER_COLUMNS = ["quantity", "unit_price_cents", "unit_cost_cents", "discount_pct"]
ALLOWED = {
    "region": {"North", "Central", "South", "West"},
    "channel": {"Online", "Store"},
    "category": {"Electronics", "Home", "Office", "Accessories"},
    "status": {"Completed", "Returned", "Cancelled"},
}


@dataclass(frozen=True)
class QualityReport:
    source_rows: int
    clean_rows: int
    duplicates_removed: int
    whitespace_cells_fixed: int


def clean_orders(raw: pd.DataFrame) -> tuple[pd.DataFrame, QualityReport]:
    required = TEXT_COLUMNS + NUMBER_COLUMNS
    missing = set(required) - set(raw.columns)
    if missing:
        raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")
    if raw.empty:
        raise ValueError("The source dataset is empty.")
    df = raw[required].copy()
    if df.isna().any().any():
        raise ValueError("Required fields contain missing values.")
    whitespace = 0
    for column in TEXT_COLUMNS:
        original = df[column].astype(str)
        stripped = original.str.strip()
        whitespace += int(original.ne(stripped).sum())
        df[column] = stripped
        if stripped.eq("").any():
            raise ValueError(f"Blank values in {column}.")
    before = len(df)
    df = df.drop_duplicates().copy()
    if df["order_id"].duplicated().any():
        raise ValueError("Conflicting rows share an order_id; resolve them at the source.")
    # Strict ISO date contract; do not guess day/month ordering.
    if not df["order_date"].str.fullmatch(r"\d{4}-\d{2}-\d{2}").all():
        raise ValueError("Dates must use YYYY-MM-DD.")
    try:
        df["order_date"] = pd.to_datetime(df["order_date"], format="%Y-%m-%d", errors="raise")
    except (ValueError, TypeError) as exc:
        raise ValueError("Invalid order date.") from exc
    for column in NUMBER_COLUMNS:
        numbers = pd.to_numeric(df[column], errors="coerce")
        # Bounds also keep the SQL integer products within a safe range.
        maximum = 100 if column == "discount_pct" else (10000 if column == "quantity" else 100000000)
        if not (numbers.between(0, maximum) & numbers.mod(1).eq(0)).all():
            raise ValueError(f"Invalid integer or out-of-range value in {column}.")
        df[column] = numbers.astype("int64")
    if df["quantity"].eq(0).any() or df["unit_price_cents"].eq(0).any():
        raise ValueError("Quantity and unit price must be positive.")
    for column, allowed in ALLOWED.items():
        if not df[column].isin(allowed).all():
            raise ValueError(f"Unknown value in {column}.")
    df = df.sort_values(["order_date", "order_id"]).reset_index(drop=True)
    return df, QualityReport(before, len(df), before - len(df), whitespace)


def build_database(clean: pd.DataFrame) -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    table = clean.copy()
    table["order_date"] = table["order_date"].dt.strftime("%Y-%m-%d")
    table.to_sql("orders", connection, index=False, if_exists="replace")
    connection.executescript((ROOT / "sql" / "sales_fact.sql").read_text(encoding="utf-8"))
    return connection


def load_sales(path: Path = DATA_PATH) -> tuple[pd.DataFrame, QualityReport]:
    clean, report = clean_orders(pd.read_csv(path, dtype={"order_id": str}))
    connection = build_database(clean)
    try:
        sales = pd.read_sql_query("SELECT * FROM sales_fact ORDER BY order_date, order_id", connection)
    finally:
        connection.close()
    sales["order_date"] = pd.to_datetime(sales["order_date"])
    return sales, report


def filter_sales(sales, start, end, regions, categories, channels):
    if start > end:
        raise ValueError("Start date must not be after end date.")
    return sales.loc[
        sales["order_date"].between(pd.Timestamp(start), pd.Timestamp(end))
        & sales["region"].isin(regions)
        & sales["category"].isin(categories)
        & sales["channel"].isin(channels)
    ].copy()


def metrics(sales: pd.DataFrame) -> dict:
    completed = int(sales["status"].eq("Completed").sum())
    returned = int(sales["status"].eq("Returned").sum())
    revenue = int(sales["revenue_cents"].sum()) / 100
    profit = int(sales["profit_cents"].sum()) / 100
    return {
        "revenue": revenue,
        "profit": profit,
        "orders": completed,
        "aov": revenue / completed if completed else None,
        "margin": profit / revenue if revenue else None,
        "return_rate": returned / (completed + returned) if completed + returned else None,
        "returned": returned,
        "cancelled": int(sales["status"].eq("Cancelled").sum()),
    }


def previous_period(start: date, end: date) -> tuple[date, date]:
    days = (end - start).days + 1
    return start - timedelta(days=days), start - timedelta(days=1)


def percent_change(current, previous):
    if current is None or previous is None or previous == 0:
        return None
    return (current - previous) / abs(previous) * 100


def daily_sales(sales, start, end):
    days = pd.date_range(start, end, freq="D", name="order_date")
    daily = sales.groupby("order_date")[["revenue_cents", "profit_cents"]].sum()
    daily = daily.reindex(days, fill_value=0).div(100)
    return daily.rename(columns={"revenue_cents": "Revenue", "profit_cents": "Gross profit"}).reset_index()


def segment_sales(sales, dimension):
    if dimension not in {"category", "region", "channel", "product"}:
        raise ValueError("Unsupported breakdown dimension.")
    completed = sales.loc[sales["status"].eq("Completed")]
    result = completed.groupby(dimension).agg(
        revenue_cents=("revenue_cents", "sum"),
        profit_cents=("profit_cents", "sum"),
        orders=("order_id", "count"),
    ).reset_index()
    result["Revenue (MAD)"] = result["revenue_cents"] / 100
    result["Gross profit (MAD)"] = result["profit_cents"] / 100
    result["Margin"] = result["profit_cents"] / result["revenue_cents"].replace(0, float("nan"))
    return result.sort_values(["revenue_cents", dimension], ascending=[False, True])
