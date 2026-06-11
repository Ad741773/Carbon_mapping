from flask import Blueprint
from app.utils.jwt_utils import jwt_required, get_jwt_identity
from app.services.prediction_service import predict_12_months
from app.utils.helpers import success

pred_bp = Blueprint("prediction", __name__)

@pred_bp.get("/")
@jwt_required()
def prediction():
    return success(predict_12_months(get_jwt_identity()))
