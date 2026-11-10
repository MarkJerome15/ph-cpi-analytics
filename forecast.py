import os                                   # NEW
import sqlite3
import pandas as pd

# 1. National headline CPI as a time series (date -> cpi)
con = sqlite3.connect("data/processed/ph_cpi.db")
s = pd.read_sql("""
    SELECT date, cpi FROM cpi
    WHERE geo_level = 'national' AND code = '0'
    ORDER BY date
""", con, parse_dates=["date"], index_col="date")["cpi"]
s = s.asfreq("MS")
con.close()

# 2. Pretend it's October 2025: split into what we "knew" and what came after
train = s[:"2025-10-01"]
test = s["2025-11-01":]

# 3. Baseline forecast: prices keep rising at the same pace as the last 12 months
growth_12m = train.iloc[-1] / train.iloc[-13]
monthly = growth_12m ** (1 / 12)
forecast = pd.Series([train.iloc[-1] * monthly ** k for k in range(1, len(test) + 1)],
                     index=test.index)

# 4. How wrong was it?
result = pd.DataFrame({"actual": test, "forecast": forecast.round(1)})
result["error_pct"] = ((result["forecast"] - result["actual"]) / result["actual"] * 100).round(2)
print(result)
print("Average error (MAPE):", round(result["error_pct"].abs().mean(), 2), "%")

# ===== Part 2: rolling backtest, simple trend vs Seasonal ARIMA =====
import warnings
import numpy as np
from statsmodels.tsa.statespace.sarimax import SARIMAX
warnings.filterwarnings("ignore")


def trend_forecast(train, h):
    """Prices keep rising at the last 12 months' pace."""
    monthly = (train.iloc[-1] / train.iloc[-13]) ** (1 / 12)
    return [train.iloc[-1] * monthly ** k for k in range(1, h + 1)]


def sarima_forecast(train, h):
    """Seasonal ARIMA on log prices: recent changes + same month last year."""
    model = SARIMAX(np.log(train), order=(1, 1, 1), seasonal_order=(0, 1, 1, 12))
    fit = model.fit(disp=False)
    return list(np.exp(fit.forecast(h)))


rows = []
for origin in s["2022-12-01":"2025-10-01"].index:
    train = s[:origin]
    future = s[origin:].iloc[1:13]
    for name, fn in [("Simple trend", trend_forecast), ("Seasonal ARIMA", sarima_forecast)]:
        fc = fn(train, 12)
        for h in (1, 3, 6, 12):
            if h <= len(future):
                actual = future.iloc[h - 1]
                rows.append({"model": name, "months_ahead": h,
                             "error_pct": abs(fc[h - 1] - actual) / actual * 100})

bt = pd.DataFrame(rows)
print("\nAverage error (%) by how far ahead we forecast:")
print(bt.pivot_table(index="model", columns="months_ahead", values="error_pct", aggfunc="mean").round(2))

# ===== Part 3: forecast Nov 2026 - Oct 2027 =====
import matplotlib.pyplot as plt

fit = SARIMAX(np.log(s), order=(1, 1, 1), seasonal_order=(0, 1, 1, 12)).fit(disp=False)
pred = fit.get_forecast(12)
fc = np.exp(pred.predicted_mean)
ci = np.exp(pred.conf_int(alpha=0.2))
trend = pd.Series(trend_forecast(s, 12), index=fc.index)

out = pd.DataFrame({"sarima": fc, "low_80": ci.iloc[:, 0],
                    "high_80": ci.iloc[:, 1], "trend": trend}).round(1)

os.makedirs("outputs", exist_ok=True)                       # NEW
out.to_csv("outputs/forecast.csv", index_label="date")      # NEW
print("Saved outputs/forecast.csv")                         # NEW

print("\nForecast:")
print(out)
sarima_yoy = (out["sarima"].iloc[-1] / s.iloc[-1] - 1) * 100
trend_yoy = (out["trend"].iloc[-1] / s.iloc[-1] - 1) * 100
print(f"Implied inflation by Oct 2027: Seasonal ARIMA {sarima_yoy:.1f}%, simple trend {trend_yoy:.1f}%")

# Chart 6
recent = s["2023-01-01":]
fig, ax = plt.subplots(figsize=(10, 5))
ax.plot(recent.index, recent, color="#2a78d6", linewidth=2, label="Actual CPI")
ax.fill_between(out.index, out["low_80"], out["high_80"], color="#eb6834", alpha=0.2,
                label="80% range (Seasonal ARIMA)")
ax.plot(out.index, out["sarima"], color="#eb6834", linewidth=2, label="Seasonal ARIMA forecast")
ax.plot(out.index, out["trend"], color="#9a9993", linewidth=2, linestyle="--",
        label="Simple trend (2026 pace continues)")

ax.set_title(f"By Oct 2027, inflation could be {sarima_yoy:.1f}% to {trend_yoy:.1f}%, depending on the assumption")
ax.set_ylabel("CPI (2018 = 100)")
ax.legend(frameon=False, loc="upper left")
ax.grid(axis="y", alpha=0.3)
ax.spines[["top", "right"]].set_visible(False)
fig.savefig("images/06_forecast.png", dpi=150, bbox_inches="tight")
print("Saved images/06_forecast.png")