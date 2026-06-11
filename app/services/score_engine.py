"""Sustainability score engine — 0-100."""
from datetime import date, timedelta
from app.db import fetchall

BENCHMARKS = {"transport": 80.0, "electricity": 60.0, "food": 75.0, "fuel": 40.0}
WEIGHTS    = {"transport": 25,   "electricity": 25,   "food": 25,   "fuel": 10, "trend": 15}


def compute_score(user_id: int) -> dict:
    today = date.today()
    since = (today - timedelta(days=30)).isoformat()
    rows  = fetchall(
        "SELECT * FROM carbon_records WHERE user_id=? AND date>=? ORDER BY date",
        (user_id, since)
    )
    if not rows:
        return {"score": 50, "grade": "C", "label": "No data yet", "percentile": 50,
                "breakdown": {}, "trend_score": 7.5, "avg_daily_kg": 0}

    n   = len(rows)
    avg = {
        "transport":   sum(r["transport_emissions"]   for r in rows) / n,
        "electricity": sum(r["electricity_emissions"] for r in rows) / n,
        "food":        sum(r["food_emissions"]        for r in rows) / n,
        "fuel":        sum(r["fuel_emissions"]        for r in rows) / n,
    }

    def sub_score(actual, bench, weight):
        ratio = actual / bench if bench else 1
        s = max(0.0, min(1.0, 1 - (ratio - 0.5)))
        return round(s * weight, 2)

    breakdown = {k: sub_score(avg[k], BENCHMARKS[k], WEIGHTS[k]) for k in avg}

    mid  = (today - timedelta(days=15)).isoformat()
    fh   = [r for r in rows if r["date"] <  mid]
    sh   = [r for r in rows if r["date"] >= mid]
    trend_score = WEIGHTS["trend"] / 2
    if fh and sh:
        a1 = sum(r["total_emissions"] for r in fh) / len(fh)
        a2 = sum(r["total_emissions"] for r in sh) / len(sh)
        if a1 > 0:
            imp = (a1 - a2) / a1
            trend_score = max(0, min(WEIGHTS["trend"], WEIGHTS["trend"] * (0.5 + imp)))

    total = round(min(100, max(0, sum(breakdown.values()) + trend_score)), 1)

    grade = ("A+" if total>=90 else "A" if total>=80 else "B" if total>=70
             else "C" if total>=55 else "D" if total>=40 else "F")
    label = ("Eco Champion" if total>=85 else "Green Warrior" if total>=70
             else "Getting Better" if total>=55 else "Needs Improvement" if total>=40
             else "High Impact")

    return {
        "score":       total,
        "grade":       grade,
        "label":       label,
        "percentile":  _pct(total),
        "breakdown":   {k: {"earned": v, "max": WEIGHTS[k]} for k, v in breakdown.items()},
        "trend_score": round(trend_score, 2),
        "avg_daily_kg": round(sum(r["total_emissions"] for r in rows) / n, 3),
    }


def _pct(s):
    if s>=90: return 95
    if s>=80: return 85
    if s>=70: return 70
    if s>=55: return 50
    if s>=40: return 30
    return 15
