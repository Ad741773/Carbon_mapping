import re
from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import fetchone, execute, tx
from app.utils.jwt_utils import create_token, jwt_required, get_jwt_identity
from app.utils.helpers import success, error, validate_required

auth_bp  = Blueprint("auth", __name__)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.post("/register")
def register():
    d = request.get_json(silent=True) or {}
    missing = validate_required(d, ["name", "email", "password"])
    if missing:
        return error(f"Missing: {', '.join(missing)}", 422)
    if not EMAIL_RE.match(d["email"]):
        return error("Invalid email address.", 422)
    if len(d["password"]) < 8:
        return error("Password must be at least 8 characters.", 422)

    email = d["email"].lower().strip()
    if fetchone("SELECT id FROM users WHERE email=?", (email,)):
        return error("Email already registered.", 409)

    pw  = generate_password_hash(d["password"])
    uid = execute(
        "INSERT INTO users (name, email, password_hash, city, country) VALUES (?,?,?,?,?)",
        (d["name"].strip(), email, pw, d.get("city"), d.get("country"))
    )
    user = fetchone("SELECT * FROM users WHERE id=?", (uid,))
    return success({
        "user":          _safe(user),
        "access_token":  create_token(uid),
        "refresh_token": create_token(uid, refresh=True),
    }, "Registration successful.", 201)


@auth_bp.post("/login")
def login():
    d = request.get_json(silent=True) or {}
    missing = validate_required(d, ["email", "password"])
    if missing:
        return error(f"Missing: {', '.join(missing)}", 422)

    user = fetchone("SELECT * FROM users WHERE email=?", (d["email"].lower().strip(),))
    if not user or not check_password_hash(user["password_hash"], d["password"]):
        return error("Invalid email or password.", 401)
    if not user["is_active"]:
        return error("Account deactivated.", 403)

    uid = user["id"]
    return success({
        "user":          _safe(user),
        "access_token":  create_token(uid),
        "refresh_token": create_token(uid, refresh=True),
    }, "Login successful.")


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    uid = get_jwt_identity()
    return success({"access_token": create_token(uid)})


@auth_bp.get("/profile")
@jwt_required()
def get_profile():
    uid  = get_jwt_identity()
    user = fetchone("SELECT * FROM users WHERE id=?", (uid,))
    if not user:
        return error("User not found.", 404)
    return success(_safe(user))


@auth_bp.put("/profile")
@jwt_required()
def update_profile():
    uid  = get_jwt_identity()
    d    = request.get_json(silent=True) or {}
    sets, vals = [], []
    for f in ("name", "city", "country", "avatar_url"):
        if f in d:
            sets.append(f"{f}=?"); vals.append(d[f])
    if "password" in d:
        if len(d["password"]) < 8:
            return error("Password must be at least 8 characters.", 422)
        sets.append("password_hash=?"); vals.append(generate_password_hash(d["password"]))
    if not sets:
        return error("Nothing to update.", 422)
    sets.append("updated_at=datetime('now')")
    vals.append(uid)
    execute(f"UPDATE users SET {', '.join(sets)} WHERE id=?", vals)
    user = fetchone("SELECT * FROM users WHERE id=?", (uid,))
    return success(_safe(user), "Profile updated.")


@auth_bp.delete("/account")
@jwt_required()
def delete_account():
    uid = get_jwt_identity()
    execute("DELETE FROM users WHERE id=?", (uid,))
    return success(message="Account deleted.")


def _safe(u: dict) -> dict:
    return {k: v for k, v in u.items() if k != "password_hash"}
