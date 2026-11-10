"""Run the SQL queries and save the results as CSVs for Power BI."""
import os
import sqlite3
import pandas as pd

os.makedirs("outputs", exist_ok=True)
con = sqlite3.connect("data/processed/ph_cpi.db")

files = {
    "contribution_latest":   "sql/05_contribution.sql",
    "headline_vs_excluding": "sql/08_headline_vs_excluding.sql",
    "regions_latest":        "sql/09_regions.sql",
    "seasonality":           "sql/10_seasonality.sql",
    "contribution_monthly":  "sql/11_contribution_monthly.sql",
    "regions_monthly":       "sql/12_regions_monthly.sql",
}

for name, path in files.items():
    df = pd.read_sql(open(path).read(), con)
    df.to_csv(f"outputs/{name}.csv", index=False)
    print(f"outputs/{name}.csv  ({len(df):,} rows)")

# Seasonality with average AND median (SQLite has no MEDIAN, so pandas does it)
s = pd.read_sql("""
    SELECT date, cpi FROM cpi
    WHERE geo_level = 'national' AND code = '0'
    ORDER BY date
""", con, parse_dates=["date"])
s["mom"] = s["cpi"].pct_change() * 100
s["month"] = s["date"].dt.month
g = s.dropna().groupby("month")["mom"].agg(["mean", "median"]).round(2).reset_index()
g["month_name"] = pd.to_datetime(g["month"].astype(str), format="%m").dt.strftime("%b")
g.to_csv("outputs/seasonality_stats.csv", index=False)
print(f"outputs/seasonality_stats.csv  ({len(g)} rows)")

con.close()