"""Data-quality gate: run the validation queries and stop the pipeline if any check fails."""
import sqlite3
import sys
import pandas as pd

con = sqlite3.connect("data/processed/ph_cpi.db")


def first_row(sql_file):
    """Run a saved SQL file and return its (single) result row."""
    return pd.read_sql(open(sql_file).read(), con).iloc[0]


yoy = first_row("sql/03_validate_yoy.sql")
wts = first_row("sql/04_weights_check.sql")
ctb = first_row("sql/06_validate_contribution.sql")
info = pd.read_sql("SELECT COUNT(*) AS n, MAX(date) AS latest FROM cpi", con).iloc[0]
con.close()

checks = [
    (f"CPI table loaded ({int(info['n']):,} rows, latest month {info['latest']})",
     info["n"] > 3_000_000),
    (f"Our YoY matches PSA's in all {int(yoy['months_checked'])} months (worst gap {yoy['worst_gap']})",
     yoy["months_off"] == 0 and yoy["months_checked"] >= 90),
    (f"Weights: {int(wts['categories'])} categories adding up to {wts['total_weight']}",
     wts["categories"] == 13 and abs(wts["total_weight"] - 100) < 0.5),
    (f"Contributions add up to headline inflation (worst gap {ctb['worst_gap']})",
     ctb["worst_gap"] < 0.2),
]

failed = False
for message, ok in checks:
    print(("PASS  " if ok else "FAIL  ") + message)
    if not ok:
        failed = True

if failed:
    sys.exit("Data-quality check failed: pipeline stopped, outputs NOT updated.")
print("All data-quality checks passed.")