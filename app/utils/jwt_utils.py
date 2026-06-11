"""JWT helpers using PyJWT (stdlib available in environment)."""
import jwt as _jwt
import os
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import request, current_app
from app.utils.helpers import error
from app.db import fetchone

SECRET = lambda: os.getenv("JWT_SECRET_KEY", "jwt-secret-change-me")
EXP    = lambda: int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", 86400))


def create_token(user_id: int, refresh=False) -> str:
    exp = timedelta(days=30 if refresh else 1) if refresh else timedelta(seconds=EXP())
    payload = {
        "sub":  str(user_id),
        "type": "refresh" if refresh else "access",
        "iat":  datetime.now(timezone.utc),
        "exp":  datetime.now(timezone.utc) + exp,
    }
    return _jwt.encode(payload, SECRET(), algorithm="HS256")


def decode_token(token: str) -> dict:
    return _jwt.decode(token, SECRET(), algorithms=["HS256"])


def jwt_required(refresh=False):
    """Decorator that protects a route with JWT."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return error("Missing or malformed Authorization header.", 401)
            token = auth.split(" ", 1)[1]
            try:
                payload = decode_token(token)
            except _jwt.ExpiredSignatureError:
                return error("Token has expired.", 401)
            except _jwt.InvalidTokenError as e:
                return error(f"Invalid token: {e}", 401)

            expected = "refresh" if refresh else "access"
            if payload.get("type") != expected:
                return error("Wrong token type.", 401)

            request.current_user_id = int(payload["sub"])
            # ensure the user referenced by the token still exists
            if not fetchone("SELECT id FROM users WHERE id=?", (request.current_user_id,)):
                return error("User not found.", 401)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_jwt_identity() -> int:
    return request.current_user_id
