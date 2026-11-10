import os
import sqlite3
import pandas as pd
import matplotlib.pyplot as plt

# 1. Get the data with SQL
con = sqlite3.connect("data/processed/ph_cpi.db")
q = """
SELECT date,
       (cpi / LAG(cpi, 12) OVER (ORDER BY date) - 1) * 100 AS yoy
FROM cpi
WHERE geo_level = 'national' AND code = '0'
ORDER BY date
"""
df = pd.read_sql(q, con, parse_dates=["date"]).dropna()
con.close()

# 2. Draw the chart
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(df["date"], df["yoy"], color="#2a78d6", linewidth=2)
ax.set_title("Philippine inflation is back near its 2023 peak")
ax.set_ylabel("Year-on-year inflation (%)")
ax.grid(axis="y", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)

# Label the peak and the latest month
peak = df.loc[df["yoy"].idxmax()]
last = df.iloc[-1]

ax.scatter([peak["date"], last["date"]], [peak["yoy"], last["yoy"]], color="#2a78d6", zorder=3)
ax.annotate(f"Peak {peak['yoy']:.1f}%\n{peak['date']:%b %Y}",
            xy=(peak["date"], peak["yoy"]), xytext=(-75, -5), textcoords="offset points")
ax.annotate(f"{last['yoy']:.1f}%\n{last['date']:%b %Y}",
            xy=(last["date"], last["yoy"]), xytext=(8, -10), textcoords="offset points")

ax.set_ylim(0, df["yoy"].max() * 1.15)

# 3. Save it
os.makedirs("images", exist_ok=True)
fig.savefig("images/01_inflation_trend.png", dpi=150, bbox_inches="tight")
print("Saved images/01_inflation_trend.png")

# ===== Chart 2: what drives inflation (latest month) =====
con = sqlite3.connect("data/processed/ph_cpi.db")
c = pd.read_sql(open("sql/05_contribution.sql").read(), con)
con.close()

short = {"01": "Food", "04": "Housing & utilities", "07": "Transport", "11": "Restaurants & hotels"}
c["label"] = c["code"].map(short).fillna("All other categories")
c = c.groupby("label", as_index=False)["contribution_pts"].sum()
c["is_other"] = c["label"] == "All other categories"
c = c.sort_values(["is_other", "contribution_pts"], ascending=[False, True])

total = c["contribution_pts"].sum()
big3 = c[c["label"].isin(["Food", "Housing & utilities", "Transport"])]["contribution_pts"].sum()
colors = ["#9a9993" if l == "All other categories" else "#2a78d6" for l in c["label"]]

fig, ax = plt.subplots(figsize=(10, 5))
ax.barh(c["label"], c["contribution_pts"], color=colors)
for i, v in enumerate(c["contribution_pts"]):
    ax.text(v + 0.03, i, f"{v:.2f} pts", va="center")

ax.set_title(f"Food, utilities and transport explain {big3 / total:.0%} of the {total:.1f}% inflation")
ax.set_xlabel("Contribution to year-on-year inflation (percentage points), Oct 2026")
ax.set_xlim(0, c["contribution_pts"].max() * 1.15)
ax.spines[["top", "right"]].set_visible(False)

fig.savefig("images/02_contribution.png", dpi=150, bbox_inches="tight")
print("Saved images/02_contribution.png")

# ===== Chart 3: inflation by region (latest month) =====
con = sqlite3.connect("data/processed/ph_cpi.db")
r = pd.read_sql(open("sql/09_regions.sql").read(), con)
con.close()

r["name"] = r["region"].str.extract(r"\((.*)\)")[0].fillna(r["region"])
r = r.sort_values("yoy_pct")
nat = df["yoy"].iloc[-1]                        # national rate, from chart 1's data

colors = ["#eb6834" if v > nat else "#2a78d6" for v in r["yoy_pct"]]
fig, ax = plt.subplots(figsize=(10, 7))
ax.barh(r["name"], r["yoy_pct"], color=colors)
for i, v in enumerate(r["yoy_pct"]):
    ax.text(v + 0.1, i, f"{v:.1f}%", va="center")
ax.axvline(nat, color="black", linestyle="--", linewidth=1)
ax.text(nat + 0.1, len(r) - 0.5, f"National {nat:.1f}%", va="bottom")

above = (r["yoy_pct"] > nat).sum()
ax.set_title(f"{above} of {len(r)} regions have inflation above the national {nat:.1f}%")
ax.set_xlabel("Year-on-year inflation, Oct 2026 (%)  ·  orange = above national")
ax.set_xlim(0, r["yoy_pct"].max() * 1.12)
ax.spines[["top", "right"]].set_visible(False)

fig.savefig("images/03_regions.png", dpi=150, bbox_inches="tight")
print("Saved images/03_regions.png")

# ===== Chart 4: headline vs inflation excluding food, transport, utilities =====
con = sqlite3.connect("data/processed/ph_cpi.db")
x = pd.read_sql(open("sql/08_headline_vs_excluding.sql").read(), con, parse_dates=["date"]).dropna()
con.close()

series = [
    ("headline_yoy",                  "Headline",                               "#2a78d6"),
    ("ex_food_transport_yoy",         "Excluding food & transport",             "#eb6834"),
    ("ex_food_transport_housing_yoy", "Excluding food, transport & utilities",  "#1baf7a"),
]

fig, ax = plt.subplots(figsize=(10, 5))
for col, name, color in series:
    ax.plot(x["date"], x[col], color=color, linewidth=2, label=name)

last = x.iloc[-1]
ax.set_title(f"Even without food, transport and utilities, inflation is "
             f"{last['ex_food_transport_housing_yoy']:.1f}% and rising")
ax.set_ylabel("Year-on-year inflation (%)")
ax.legend(frameon=False, loc="upper left")
ax.set_ylim(bottom=0)
ax.grid(axis="y", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)

fig.savefig("images/04_headline_vs_excluding.png", dpi=150, bbox_inches="tight")
print("Saved images/04_headline_vs_excluding.png")

# ===== Chart 5: seasonality - average vs median monthly price change =====
con = sqlite3.connect("data/processed/ph_cpi.db")
s = pd.read_sql("""
    SELECT date, cpi FROM cpi
    WHERE geo_level = 'national' AND code = '0'
    ORDER BY date
""", con, parse_dates=["date"])
con.close()

s["mom"] = s["cpi"].pct_change() * 100
s["month"] = s["date"].dt.month
g = s.dropna().groupby("month")["mom"].agg(["mean", "median"])

fig, ax = plt.subplots(figsize=(10, 5))
ax.bar(g.index - 0.2, g["mean"],   width=0.4, color="#9a9993", label="Average")
ax.bar(g.index + 0.2, g["median"], width=0.4, color="#2a78d6", label="Median (not swayed by one-off shocks)")
ax.set_xticks(range(1, 13))
ax.set_xticklabels(["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
ax.axhline(0, color="black", linewidth=0.8)

ax.set_title("Prices rise most in January; April's average is inflated by the 2026 shock")
ax.set_ylabel("Month-on-month price change (%), 2018–2026")
ax.legend(frameon=False)
ax.spines[["top", "right"]].set_visible(False)

fig.savefig("images/05_seasonality.png", dpi=150, bbox_inches="tight")
print("Saved images/05_seasonality.png")