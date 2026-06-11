from datetime import date
from flask import Blueprint, request
from app.db import fetchall, fetchone, execute
from app.utils.jwt_utils import jwt_required, get_jwt_identity
from app.utils.helpers import success, error, validate_required

goals_bp = Blueprint("goals", __name__)


def _fmt(g: dict) -> dict:
    g = dict(g)
    tv = g["target_value"] or 0
    cv = g["current_value"] or 0
    g["achievement_pct"] = round(min(cv / tv * 100, 100), 1) if tv > 0 else 0
    return g


@goals_bp.post("/")
@jwt_required()
def create_goal():
    uid  = get_jwt_identity()
    d    = request.get_json(silent=True) or {}
    miss = validate_required(d, ["title", "target_value"])
    if miss:
        return error(f"Missing: {', '.join(miss)}", 422)

    end_date = None
    if d.get("end_date"):
        try:
            date.fromisoformat(d["end_date"])
            end_date = d["end_date"]
        except ValueError:
            return error("Invalid end_date. Use YYYY-MM-DD.", 422)

    gid = execute(
        """INSERT INTO goals
           (user_id,title,description,category,target_value,current_value,start_date,end_date)
           VALUES (?,?,?,?,?,?,?,?)""",
        (uid, d["title"], d.get("description"), d.get("category","overall"),
         float(d["target_value"]), float(d.get("current_value",0)),
         date.today().isoformat(), end_date)
    )
    return success(_fmt(fetchone("SELECT * FROM goals WHERE id=?", (gid,))), "Goal created.", 201)


@goals_bp.get("/")
@jwt_required()
def list_goals():
    uid = get_jwt_identity()
    return success([_fmt(g) for g in fetchall(
        "SELECT * FROM goals WHERE user_id=? ORDER BY created_at DESC", (uid,))])


@goals_bp.get("/<int:gid>")
@jwt_required()
def get_goal(gid):
    uid = get_jwt_identity()
    g   = fetchone("SELECT * FROM goals WHERE id=? AND user_id=?", (gid, uid))
    return success(_fmt(g)) if g else error("Goal not found.", 404)


@goals_bp.put("/<int:gid>")
@jwt_required()
def update_goal(gid):
    uid = get_jwt_identity()
    g   = fetchone("SELECT * FROM goals WHERE id=? AND user_id=?", (gid, uid))
    if not g:
        return error("Goal not found.", 404)
    d    = request.get_json(silent=True) or {}
    sets, vals = [], []
    for f in ("title","description","category"):
        if f in d: sets.append(f"{f}=?"); vals.append(d[f])
    for f in ("target_value","current_value"):
        if f in d: sets.append(f"{f}=?"); vals.append(float(d[f]))
    if "end_date" in d:
        sets.append("end_date=?"); vals.append(d["end_date"])
    if not sets:
        return error("Nothing to update.", 422)
    sets.append("updated_at=datetime('now')")
    # Auto-complete
    cv = float(d.get("current_value", g["current_value"]))
    tv = float(d.get("target_value",  g["target_value"]))
    if cv >= tv:
        sets.append("is_completed=1")
    vals.append(gid)
    execute(f"UPDATE goals SET {', '.join(sets)} WHERE id=?", vals)
    return success(_fmt(fetchone("SELECT * FROM goals WHERE id=?", (gid,))), "Goal updated.")


@goals_bp.delete("/<int:gid>")
@jwt_required()
def delete_goal(gid):
    uid = get_jwt_identity()
    if not fetchone("SELECT id FROM goals WHERE id=? AND user_id=?", (gid, uid)):
        return error("Goal not found.", 404)
    execute("DELETE FROM goals WHERE id=?", (gid,))
    return success(message="Goal deleted.")


@goals_bp.get("/<int:gid>/status")
@jwt_required()
def goal_status(gid):
    uid = get_jwt_identity()
    g   = fetchone("SELECT * FROM goals WHERE id=? AND user_id=?", (gid, uid))
    if not g:
        return error("Goal not found.", 404)
    out = _fmt(g)
    out["remaining_kg"] = round(max(0, g["target_value"] - g["current_value"]), 3)
    if g["end_date"]:
        out["days_left"] = (date.fromisoformat(g["end_date"]) - date.today()).days
    return success(out)
