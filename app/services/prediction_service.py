from datetime import date, timedelta
from calendar import month_abbr
import numpy as np
from app.db import fetchall


def predict_12_months(user_id: int) -> dict:
    since = (date.today() - timedelta(days=90)).isoformat()
    rows  = fetchall(
        "SELECT date, total_emissions FROM carbon_records "
        "WHERE user_id=? AND date>=? ORDER BY date",
        (user_id, since)
    )

    if len(rows) < 7:
        return {
            "message":  "Need at least 7 days of data for prediction.",
            "months":   [], "predictions_kg": [],
            "annual_forecast": 0, "annual_forecast_tonnes": 0,
        }

    base = date.fromisoformat(rows[0]["date"])
    weekly: dict = {}
    for r in rows:
        wk = (date.fromisoformat(r["date"]) - base).days // 7
        weekly.setdefault(wk, []).append(r["total_emissions"])

    xs = sorted(weekly)
    ys = [sum(weekly[w]) / len(weekly[w]) for w in xs]

    x  = np.array(xs, dtype=float)
    y  = np.array(ys, dtype=float)
    xm, ym = x.mean(), y.mean()
    slope     = float(np.dot(x-xm, y-ym) / (np.dot(x-xm, x-xm) + 1e-9))
    intercept = float(ym - slope * xm)

    last_x = float(x[-1])
    today  = date.today()
    months, preds = [], []
    for m in range(1, 13):
        fx        = last_x + m * 4.33
        daily_avg = max(0.0, intercept + slope * fx)
        monthly   = round(daily_avg * 30, 2)
        mi        = (today.month - 1 + m) % 12
        months.append(month_abbr[mi + 1])
        preds.append(monthly)

    trend = "decreasing 📉" if slope < -0.01 else ("increasing 📈" if slope > 0.01 else "stable ➡️")

    return {
        "trend":                  trend,
        "slope_per_week":         round(slope, 4),
        "months":                 months,
        "predictions_kg":         preds,
        "annual_forecast":        round(sum(preds), 2),
        "annual_forecast_tonnes": round(sum(preds) / 1000, 3),
    }
