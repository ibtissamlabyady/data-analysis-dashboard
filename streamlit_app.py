"""Atlas Retail: a transparent sales analytics portfolio demo."""

from datetime import timedelta

import altair as alt
import streamlit as st

from src.analytics import (
    DATA_PATH, ROOT, daily_sales, filter_sales, load_sales, metrics,
    percent_change, previous_period, segment_sales,
)

st.set_page_config(page_title="Atlas Retail | Sales analytics", page_icon=":material/monitoring:", layout="wide")


@st.cache_data(max_entries=2, show_spinner="Validating sales data...")
def cached_sales(source_version):
    return load_sales()


def reset_filters():
    for key in ("dates", "regions", "categories", "channels"):
        st.session_state.pop(key, None)


def delta_text(current, baseline, comparable):
    change = percent_change(current, baseline) if comparable else None
    return f"{change:+.1f}% vs prior period" if change is not None else None


st.caption("ATLAS RETAIL  /  SALES INTELLIGENCE")
st.title("Sales performance")
st.caption("A portfolio demonstration by Ibtissam Labyady · All orders and business results are synthetic.")

try:
    sales, quality = cached_sales(DATA_PATH.stat().st_mtime_ns)
except (ValueError, OSError) as exc:
    st.error(f"Cannot load the demo dataset: {exc}")
    st.stop()

first, last = sales["order_date"].min().date(), sales["order_date"].max().date()
with st.sidebar:
    st.header("Atlas Retail", icon=":material/storefront:")
    st.badge("Synthetic dataset", color="orange")
    st.caption(f"Coverage: {first:%d %b %Y} – {last:%d %b %Y}")
    st.subheader("Explore sales")
    dates = st.date_input("Order date range", value=(last - timedelta(days=91), last), min_value=first, max_value=last, format="YYYY-MM-DD", key="dates")
    regions = st.multiselect("Regions", sorted(sales["region"].unique()), default=sorted(sales["region"].unique()), key="regions")
    categories = st.multiselect("Categories", sorted(sales["category"].unique()), default=sorted(sales["category"].unique()), key="categories")
    channels = st.multiselect("Sales channels", sorted(sales["channel"].unique()), default=sorted(sales["channel"].unique()), key="channels")
    st.button("Reset filters", icon=":material/restart_alt:", on_click=reset_filters, width="stretch")
    st.caption("Clear a selection to see no matching orders. Reset restores the last 92 days and all segments.")
    st.link_button("View source on GitHub", "https://github.com/ibtissamlabyady/data-analysis-dashboard", icon=":material/code:")

if len(dates) != 2:
    st.info("Select an end date to complete the reporting period.")
    st.stop()
start, end = dates
selected = filter_sales(sales, start, end, regions, categories, channels)
st.markdown(f"**{start:%d %b %Y} — {end:%d %b %Y}** · {len(selected):,} orders across all statuses · Currency: **MAD**")
if selected.empty:
    st.info("No orders match these filters. Choose another period or reset the filters.")
    st.stop()

prior_start, prior_end = previous_period(start, end)
comparable = prior_start >= first
previous = filter_sales(sales, prior_start, prior_end, regions, categories, channels)
current, baseline = metrics(selected), metrics(previous)
trend = daily_sales(selected, start, end)
if comparable:
    st.caption(f"Changes compare with {prior_start:%d %b %Y} – {prior_end:%d %b %Y}, using the same segment filters and number of days.")
else:
    st.caption("Prior-period changes are unavailable: the preceding period extends outside the dataset.")

with st.container(horizontal=True):
    st.metric("Net revenue", f"MAD {current['revenue']:,.0f}", delta_text(current["revenue"], baseline["revenue"], comparable), border=True, chart_data=trend["Revenue"], help="Completed orders after discounts; cancelled and fully returned orders are excluded.")
    st.metric("Gross profit", f"MAD {current['profit']:,.0f}", delta_text(current["profit"], baseline["profit"], comparable), border=True, chart_data=trend["Gross profit"], help="Net revenue minus product cost. Operating expenses, shipping and taxes are not modeled.")
    st.metric("Completed orders", f"{current['orders']:,}", delta_text(current["orders"], baseline["orders"], comparable), border=True)
    st.metric("Average order value", f"MAD {current['aov']:,.2f}" if current["aov"] is not None else "N/A", delta_text(current["aov"], baseline["aov"], comparable), border=True, help="Net revenue divided by completed orders.")

overview, details, methodology = st.tabs(["Performance", "Order explorer", "Data & definitions"])
with overview:
    left, right = st.columns([1.65, 1])
    with left, st.container(border=True):
        st.subheader("Revenue & gross profit")
        granularity = st.segmented_control("Aggregation", ["Daily", "Weekly", "Monthly"], default="Weekly", key="granularity") or "Weekly"
        rule = {"Daily": "D", "Weekly": "W-MON", "Monthly": "MS"}[granularity]
        chart_data = trend.set_index("order_date").resample(rule, label="left", closed="left").sum().reset_index()
        chart_data = chart_data.melt("order_date", var_name="Metric", value_name="MAD")
        chart = alt.Chart(chart_data).mark_line(point=True, strokeWidth=2.5).encode(
            x=alt.X("order_date:T", title="Period starting"),
            y=alt.Y("MAD:Q", title="MAD", axis=alt.Axis(format="~s"), scale=alt.Scale(zero=True)),
            color=alt.Color("Metric:N", scale=alt.Scale(domain=["Revenue", "Gross profit"], range=["#0F766E", "#2563EB"]), legend=alt.Legend(orient="top")),
            tooltip=[alt.Tooltip("order_date:T", title="Period starting", format="%d %b %Y"), "Metric:N", alt.Tooltip("MAD:Q", format=",.2f")],
        ).properties(height=260)
        st.altair_chart(chart)
        st.caption("Boundary buckets may be partial; only orders inside the selected date range are included.")
    with right, st.container(border=True):
        st.subheader("Where revenue comes from")
        dimension = st.selectbox("Break down by", ["Category", "Region", "Channel"], key="breakdown").lower()
        breakdown = segment_sales(selected, dimension)
        bars = alt.Chart(breakdown).mark_bar(color="#0F766E", cornerRadiusEnd=4).encode(
            y=alt.Y(f"{dimension}:N", sort="-x", title=None),
            x=alt.X("Revenue (MAD):Q", axis=alt.Axis(format="~s"), title="Net revenue (MAD)"),
            tooltip=[dimension, alt.Tooltip("Revenue (MAD):Q", format=",.2f"), alt.Tooltip("Margin:Q", format=".1%")],
        ).properties(height=260)
        st.altair_chart(bars)
        st.caption("Completed orders only, after discounts.")
    with st.container(horizontal=True):
        st.metric("Gross margin", f"{current['margin']:.1%}" if current["margin"] is not None else "N/A", border=True, help="Gross profit / net revenue; a weighted ratio, not an average of order margins.")
        st.metric("Return rate", f"{current['return_rate']:.1%}" if current["return_rate"] is not None else "N/A", border=True, help="Returned / (Completed + Returned) orders, grouped by original order date. Cancelled orders are excluded.")
        st.metric("Cancelled orders", str(current["cancelled"]), border=True)
    products = segment_sales(selected, "product")
    with st.container(border=True):
        st.subheader("Product performance")
        st.dataframe(products[["product", "orders", "Revenue (MAD)", "Gross profit (MAD)", "Margin"]].rename(columns={"product": "Product", "orders": "Completed orders"}), hide_index=True,
            column_config={"Revenue (MAD)": st.column_config.NumberColumn(format="%,.2f"), "Gross profit (MAD)": st.column_config.NumberColumn(format="%,.2f"), "Margin": st.column_config.NumberColumn(format="percent")})
    if not products.empty and current["revenue"] > 0:
        leader = products.iloc[0]
        st.info(f"In this synthetic selection, {leader['product']} accounts for {leader['Revenue (MAD)'] / current['revenue']:.1%} of net revenue. Compare its margin with the other products before drawing conclusions.", icon=":material/insights:")

with details:
    st.subheader("Inspect & export orders")
    st.caption("This table and its CSV export include all statuses within the sidebar filters. Revenue and profit are zero for returned and cancelled orders.")
    export = selected.copy()
    export["order_date"] = export["order_date"].dt.strftime("%Y-%m-%d")
    for column in ("revenue", "profit"):
        export[f"{column}_mad"] = export[f"{column}_cents"] / 100
    st.download_button("Download filtered orders", export.to_csv(index=False).encode("utf-8"), file_name=f"atlas-sales-{start}-{end}.csv", mime="text/csv", icon=":material/download:")
    st.dataframe(export[["order_id", "order_date", "product", "category", "region", "channel", "status", "quantity", "discount_pct", "revenue_mad", "profit_mad"]], hide_index=True, height=460,
        column_config={"revenue_mad": st.column_config.NumberColumn("Revenue (MAD)", format="%,.2f"), "profit_mad": st.column_config.NumberColumn("Gross profit (MAD)", format="%,.2f")})

with methodology:
    st.subheader("Know what the numbers mean")
    st.caption("The quality summary covers the full source dataset, before sidebar filters.")
    with st.container(horizontal=True):
        st.metric("Source rows", f"{quality.source_rows:,}", border=True)
        st.metric("Duplicate rows removed", quality.duplicates_removed, border=True)
        st.metric("Whitespace cells fixed", quality.whitespace_cells_fixed, border=True)
        st.metric("Validated orders", f"{quality.clean_rows:,}", border=True)
    st.markdown((ROOT / "docs" / "metric-definitions.md").read_text(encoding="utf-8"))
    st.caption("Source: deterministic fictional data generated with Python (seed 42). No customer data or client performance is represented.")

st.caption("Built with Python · pandas · SQLite · Streamlit · Altair | Demo v0.1")
