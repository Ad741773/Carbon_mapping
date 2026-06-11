import json
from datetime import date
from flask import Blueprint, request
from app.db import fetchall, fetchone, execute
from app.utils.jwt_utils import jwt_required, get_jwt_identity
from app.services.emission_calculator import EmissionCalculator
from app.utils.helpers import success, error

track_bp = Blueprint("tracking", __name__)


@track_bp.post("/log")
@jwt_required()
def log_record():
    uid  = get_jwt_identity()
    d    = request.get_json(silent=True) or {}
    trips     = d.get("trips", [])
    kwh       = float(d.get("electricity_kwh", 0))
    fuel      = d.get("fuel", {})
    food_type = d.get("food_type", "vegetarian")
    rec_date  = d.get("date", date.today().isoformat())

    try:
        date.fromisoformat(rec_date)
    except ValueError:
        return error("Invalid date. Use YYYY-MM-DD.", 422)

    calc = EmissionCalculator.calculate_monthly(trips, kwh, fuel, food_type)
    t_em = round(calc["transport_emissions"]   / 30, 4)
    e_em = round(calc["electricity_emissions"] / 30, 4)
    f_em = round(calc["food_emissions"]        / 30, 4)
    u_em = round(calc["fuel_emissions"]        / 30, 4)
    tot  = round(t_em + e_em + f_em + u_em, 4)

    rid = execute(
        """INSERT INTO carbon_records
           (user_id,date,transport_emissions,electricity_emissions,
            food_emissions,fuel_emissions,total_emissions,
            transport_details,electricity_kwh,fuel_details,food_type)
           VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
        (uid, rec_date, t_em, e_em, f_em, u_em, tot,
         json.dumps(trips), kwh, json.dumps(fuel), food_type)
    )
    row = fetchone("SELECT * FROM carbon_records WHERE id=?", (rid,))
    return success(_fmt(row), "Record logged.", 201)


@track_bp.get("/records")
@jwt_required()
def get_records():
    uid  = get_jwt_identity()
    page = max(1, int(request.args.get("page", 1)))
    per  = 20
    rows = fetchall(
        "SELECT * FROM carbon_records WHERE user_id=? ORDER BY date DESC LIMIT ? OFFSET ?",
        (uid, per, (page-1)*per)
    )
    total = fetchone("SELECT COUNT(*) as n FROM carbon_records WHERE user_id=?", (uid,))["n"]
    import math
    return success({
        "items":    [_fmt(r) for r in rows],
        "total":    total,
        "page":     page,
        "pages":    math.ceil(total / per),
        "per_page": per,
    })


@track_bp.get("/records/<int:rid>")
@jwt_required()
def get_record(rid):
    uid = get_jwt_identity()
    row = fetchone("SELECT * FROM carbon_records WHERE id=? AND user_id=?", (rid, uid))
    if not row:
        return error("Record not found.", 404)
    return success(_fmt(row))


@track_bp.put("/records/<int:rid>")
@jwt_required()
def update_record(rid):
    uid = get_jwt_identity()
    row = fetchone("SELECT * FROM carbon_records WHERE id=? AND user_id=?", (rid, uid))
    if not row:
        return error("Record not found.", 404)
    d    = request.get_json(silent=True) or {}
    sets, vals = [], []
    for f in ("transport_emissions","electricity_emissions","food_emissions","fuel_emissions"):
        if f in d:
            sets.append(f"{f}=?"); vals.append(float(d[f]))
    if not sets:
        return error("Nothing to update.", 422)
    # Recalculate total
    updated = {**row, **{f.rstrip("?"): v for f, v in zip(sets, vals)}}
    tot = round(
        float(updated.get("transport_emissions", row["transport_emissions"])) +
        float(updated.get("electricity_emissions", row["electricity_emissions"])) +
        float(updated.get("food_emissions", row["food_emissions"])) +
        float(updated.get("fuel_emissions", row["fuel_emissions"])), 4
    )
    sets.append("total_emissions=?"); vals.append(tot)
    vals.append(rid)
    execute(f"UPDATE carbon_records SET {', '.join(sets)} WHERE id=?", vals)
    return success(_fmt(fetchone("SELECT * FROM carbon_records WHERE id=?", (rid,))), "Updated.")


@track_bp.delete("/records/<int:rid>")
@jwt_required()
def delete_record(rid):
    uid = get_jwt_identity()
    row = fetchone("SELECT id FROM carbon_records WHERE id=? AND user_id=?", (rid, uid))
    if not row:
        return error("Record not found.", 404)
    execute("DELETE FROM carbon_records WHERE id=?", (rid,))
    return success(message="Record deleted.")


def _fmt(r: dict) -> dict:
    import json as _json
    out = dict(r)
    for f in ("transport_details", "fuel_details"):
        if isinstance(out.get(f), str):
            try:
                out[f] = _json.loads(out[f])
            except Exception:
                out[f] = {}
    return out
