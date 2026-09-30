# Upwork portfolio copy

## Project title

Sales Analytics Dashboard | Python, SQL & Streamlit

## Role

Data analysis, SQL transformations, dashboard development, and validation

## Short description

Built an interactive retail sales dashboard using Python, SQL, and Streamlit. The demo processes 7,806 fictional orders and tracks revenue, gross profit, average order value, and returns. Users can filter by date, region, category, and channel, compare equal-length periods, inspect products, and export filtered orders. Includes reproducible data generation, documented KPI definitions, data quality checks, and 14 automated tests. Personal portfolio project with synthetic data; no client results are claimed.

## Suggested skills

Python · SQL · Data Analysis · Data Visualization · Dashboard

## Detailed project story

### The problem

A retail manager needs a consistent view of sales performance across channels and
product categories. Spreadsheet totals can be misleading when cancelled orders,
returns, duplicate records, and discounts are handled differently.

### The approach

This portfolio demonstration starts with a reproducible fictional dataset. Python
trims text fields, removes exact duplicates, and validates dates, identifiers,
categories, and numeric ranges. A SQLite view calculates recognized revenue and
product costs in integer centimes. Streamlit presents the results with interactive
filters, charts, product breakdowns, and a CSV export.

### What is demonstrated

- Translating business questions into explicit KPI formulas.
- Cleaning 7,824 source rows into 7,806 validated orders.
- Excluding cancelled and fully returned orders from recognized revenue.
- Comparing periods consistently and handling missing or zero baselines.
- Separating reusable calculation logic from the dashboard interface.
- Testing calculations and filter behavior with 14 automated tests.

### Deliverables

A working local application, Python and SQL source, synthetic dataset, metric
dictionary, reproducible findings report, screenshot, setup guide, and tests.

### Scope and limitations

This is a personal demonstration, not a paid client engagement. Its sales figures
are generated and do not represent actual business performance. Public hosting,
arbitrary data uploads, forecasting, and a native Power BI report are future work.

## Media

Use `docs/screenshots/dashboard.png`, an actual capture of the running application.
Its default view covers Q4 2025; the findings document covers all of 2025.

## Project link

https://github.com/ibtissamlabyady/data-analysis-dashboard
