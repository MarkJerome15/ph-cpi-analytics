import glob
import pandas as pd

path = glob.glob("data/raw/Consumer*Price*Index*All*Income*")[0]
print("Reading:", path)

df = pd.read_csv(path, skiprows=1, dtype=str, encoding="utf-8-sig")
print(df.head())
print(df.shape)

print(df.columns[:6].tolist())
print(df.columns[-3:].tolist())

month_cols = df.columns[2:]
missing = (df[month_cols] == "..").sum().sum()
total = df[month_cols].size
print(f"Missing cells: {missing:,} of {total:,} ({missing / total:.1%})")

by_col = (df[month_cols] == "..").mean().sort_values(ascending=False)
print(by_col.head(6))

df["n_missing"] = (df[month_cols] == "..").sum(axis=1)
df["geo_clean"] = df["Geolocation"].str.strip(".")
print(df.groupby("geo_clean")["n_missing"].mean().sort_values(ascending=False).head(8))