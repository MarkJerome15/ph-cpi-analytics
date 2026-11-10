"""Compare the API download (data/api) with the hand-downloaded CSVs (data/raw),
matching rows by place + item code instead of by position."""
import glob
import numpy as np
import pandas as pd


def read(path):
    df = pd.read_csv(path, skiprows=1, dtype=str, encoding="utf-8-sig")
    df["code"] = df.iloc[:, 1].str.split(" - ").str[0].str.strip()   # '01.1.1.12 - Rice' -> '01.1.1.12'
    df["place"] = df.iloc[:, 0].str.strip()
    return df.set_index(["place", "code"]).sort_index()


def numbers(df):
    return df.iloc[:, 2:].replace("..", np.nan).apply(pd.to_numeric, errors="coerce")


tables = [
    ("Consumer*Price*Index*All*Income*", "CPI"),
    ("*Year-on-Year*", "Year-on-year"),
    ("*Weights*", "Weights"),
]

for pattern, name in tables:
    manual = read(glob.glob(f"data/raw/{pattern}")[0])
    api = read(glob.glob(f"data/api/{pattern}")[0])

    print(f"\n{name}")
    only_m = manual.index.difference(api.index)
    only_a = api.index.difference(manual.index)
    print("  rows only in manual:", len(only_m), list(only_m[:3]))
    print("  rows only in api:   ", len(only_a), list(only_a[:3]))

    common = manual.index.intersection(api.index)
    a = numbers(manual.loc[common])
    b = numbers(api.loc[common])
    both = a.notna() & b.notna()
    gap = (a - b).abs()[both]
    print("  rows matched:        ", f"{len(common):,}")
    print("  values compared:     ", f"{int(both.sum().sum()):,}")
    print("  biggest gap:         ", np.nanmax(gap.values))
    print("  missing in only one: ", int((a.isna() != b.isna()).sum().sum()))