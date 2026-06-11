import json
from flask import Blueprint
from app.db import fetchall, execute
from app.utils.jwt_utils import jwt_required, get_jwt_identity
from app.services.recommendation_engine import generate_recommendations
from app.utils.helpers import success

recs_bp = Blueprint("recommendations", __name__)


@recs_bp.post("/")
@jwt_required()
def get_recs():
    uid  = get_jwt_identity()
    data = generate_recommendations(uid)
    execute(
        "INSERT INTO recommendations (user_id, tips, source) VALUES (?,?,?)",
        (uid, json.dumps(data["tips"]), data["source"])
    )
    return success(data)


@recs_bp.get("/history")
@jwt_required()
def rec_history():
    uid  = get_jwt_identity()
    rows = fetchall(
        "SELECT * FROM recommendations WHERE user_id=? ORDER BY created_at DESC LIMIT 10",
        (uid,)
    )
    out = []
    for r in rows:
        r = dict(r)
        if isinstance(r["tips"], str):
            try: r["tips"] = json.loads(r["tips"])
            except Exception: r["tips"] = []
        out.append(r)
    return success(out)
