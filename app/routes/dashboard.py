"""Dashboard route."""
from flask import Blueprint
from app.utils.jwt_utils import jwt_required, get_jwt_identity
from app.services.analytics_service import get_analytics
from app.utils.helpers import success

dash_bp = Blueprint("dashboard", __name__)

@dash_bp.get("/")
@jwt_required()
def dashboard():
    return success(get_analytics(get_jwt_identity()))
