from datetime import date, timedelta
from flask import Blueprint, request
from app.db import fetchall, fetchone
from app.utils.jwt_utils import jwt_required, get_jwt_identity
from app.services.score_engine import compute_score
from app.utils.helpers import success

lb_bp = Blueprint("leaderboard", __name__)


@lb_bp.get("/")
@jwt_required()
def leaderboard():
    mode  = request.args.get("mode", "score")
    limit = min(int(request.args.get("limit", 20)), 100)
    my_id = get_jwt_identity()

    today = date.today().isoformat()
    since = (date.today() - timedelta(days=30)).isoformat()

    users = fetchall("SELECT * FROM users WHERE is_active=1")
    board = []
    for u in users:
        rows = fetchall(
            "SELECT total_emissions, date FROM carbon_records WHERE user_id=? AND date>=?",
            (u["id"], since)
        )
        if not rows:
            continue
        monthly_kg = round(sum(r["total_emissions"] for r in rows), 2)
        sc         = compute_score(u["id"])
        board.append({
            "user_id":       u["id"],
            "name":          u["name"],
            "city":          u["city"] or "—",
            "country":       u["country"] or "—",
            "score":         sc["score"],
            "grade":         sc["grade"],
            "monthly_kg":    monthly_kg,
            "reduction_pct": _reduction(u["id"]),
        })

    if mode == "footprint":
        board.sort(key=lambda x: x["monthly_kg"])
    else:
        board.sort(key=lambda x: x["score"], reverse=True)

    for i, e in enumerate(board):
        e["rank"] = i + 1

    my_entry = next((e for e in board if e["user_id"] == my_id), None)
    return success({"leaderboard": board[:limit], "my_rank": my_entry})


def _reduction(user_id: int) -> float:
    today = date.today()
    t_start = today.replace(day=1)
    l_end   = t_start
    l_start = (t_start - timedelta(days=1)).replace(day=1)

    def avg(s, u):
        rows = fetchall(
            "SELECT total_emissions FROM carbon_records WHERE user_id=? AND date>=? AND date<?",
            (user_id, s.isoformat(), u.isoformat())
        )
        return sum(r["total_emissions"] for r in rows) / len(rows) if rows else 0

    last = avg(l_start, l_end)
    curr = avg(t_start, today + timedelta(days=1))
    return round((last - curr) / last * 100, 1) if last > 0 else 0.0
