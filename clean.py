import glob
import os
import sqlite3
import pandas as pd


def read_psa(pattern):
    """Find a PSA file by name pattern and read it, skipping the title row."""
    path = glob.glob(f"data/raw/{pattern}")[0]
    return pd.read_csv(path, skiprows=1, dtype=str, encoding="utf-8-sig")


def to_number(s):
    """Turn PSA's '..' into missing, then text into numbers."""
    return pd.to_numeric(s.replace("..", pd.NA), errors="coerce")


def melt_months(df, value_name):
    """Wide (one column per month) -> long (one row per month)."""
    cols = [c for c in df.columns[2:] if not c.endswith("Ave")]
    long = df.melt(id_vars=["Geolocation", "Commodity Description"], value_vars=cols,
                   var_name="period", value_name="raw")
    long[value_name] = to_number(long["raw"])
    long = long.dropna(subset=[value_name])
    long["date"] = pd.to_datetime(long["period"], format="%Y %b").dt.strftime("%Y-%m-%d")
    return long.drop(columns=["raw", "period"])


def add_labels(df):
    """Split '....Abra' and '01.1.1.12 - Rice' into clean columns."""
    g = df["Geolocation"]
    df["geo_name"] = g.str.lstrip(".").str.strip()
    dots = g.str.len() - g.str.lstrip(".").str.len()
    df["geo_level"] = dots.map({0: "national", 2: "region", 4: "province"})
    df["is_aggregate"] = df["geo_name"].str.startswith("Areas Outside")
    parts = df["Commodity Description"].str.extract(r"^\s*([\d.]+)\s*-\s*(.*?)\s*$")
    df["code"] = parts[0]
    df["item"] = parts[1]
    df["level"] = df["code"].str.count(r"\.") + 1
    df.loc[df["code"] == "0", "level"] = 0
    return df


# ---- build each table ----
cpi = add_labels(melt_months(read_psa("Consumer*Price*Index*All*Income*"), "cpi"))
yoy = add_labels(melt_months(read_psa("*Year-on-Year*"), "yoy_pct"))

w = add_labels(read_psa("*Weights*"))
w["weight"] = to_number(w["Weights"])
w = w.dropna(subset=["weight"])

# ---- save to SQLite ----
os.makedirs("data/processed", exist_ok=True)
con = sqlite3.connect("data/processed/ph_cpi.db")
cpi[["geo_name", "geo_level", "is_aggregate", "code", "item", "level", "date", "cpi"]] \
    .to_sql("cpi", con, if_exists="replace", index=False)
yoy[["geo_name", "code", "date", "yoy_pct"]] \
    .to_sql("yoy_published", con, if_exists="replace", index=False)
w[["geo_name", "geo_level", "code", "item", "level", "weight"]] \
    .to_sql("weights", con, if_exists="replace", index=False)
con.execute("CREATE INDEX IF NOT EXISTS ix_cpi ON cpi (geo_name, code, date)")
con.commit()
con.close()

print(f"cpi: {len(cpi):,} rows | yoy_published: {len(yoy):,} | weights: {len(w):,}")