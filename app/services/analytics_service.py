from datetime import date, timedelta
from collections import defaultdict
from app.db import fetchall


def _sum_field(rows, field):
    return round(sum(r[field] for r in rows), 3)


def get_analytics(user_id: int) -> dict:
    today = date.today().isoformat()

    def fetch(since):
        return fetchall(
            "SELECT * FROM carbon_records WHERE user_id=? AND date>=? ORDER BY date",
            (user_id, since)
        )

    daily   = fetch(today)
    weekly  = fetch((date.today() - timedelta(days=7)).isoformat())
    monthly = fetch((date.today() - timedelta(days=30)).isoformat())
    yearly  = fetch((date.today() - timedelta(days=365)).isoformat())

    def summary(rows):
        return {
            "total":       _sum_field(rows, "total_emissions"),
            "transport":   _sum_field(rows, "transport_emissions"),
            "electricity": _sum_field(rows, "electricity_emissions"),
            "food":        _sum_field(rows, "food_emissions"),
            "fuel":        _sum_field(rows, "fuel_emissions"),
            "records":     len(rows),
        }

    # Monthly trend
    trend: dict = defaultdict(float)
    for r in yearly:
        key = r["date"][:7]   # YYYY-MM
        trend[key] += r["total_emissions"]
    monthly_trend = [{"month": k, "kg": round(v, 3)} for k, v in sorted(trend.items())]

    # Category breakdown (30 days)
    cat = {
        "Transport":   _sum_field(monthly, "transport_emissions"),
        "Electricity": _sum_field(monthly, "electricity_emissions"),
        "Food":        _sum_field(monthly, "food_emissions"),
        "Fuel":        _sum_field(monthly, "fuel_emissions"),
    }
    grand = sum(cat.values()) or 1
    breakdown = [{"category": k, "kg": v, "pct": round(v/grand*100,1)}
                 for k, v in cat.items()]

    from app.services.score_engine import compute_score
    score = compute_score(user_id)

    return {
        "daily":              summary(daily),
        "weekly":             summary(weekly),
        "monthly":            summary(monthly),
        "yearly":             summary(yearly),
        "monthly_trend":      monthly_trend,
        "category_breakdown": breakdown,
        "sustainability_score": score,
    }
