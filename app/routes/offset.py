"""Tree offset calculator."""
from flask import Blueprint, request
from app.utils.jwt_utils import jwt_required
from app.services.emission_calculator import EmissionCalculator, KG_CO2_PER_TREE_PER_YEAR
from app.utils.helpers import success, error

offset_bp = Blueprint("offset", __name__)


@offset_bp.post("/")
@jwt_required()
def calculate_offset():
    d  = request.get_json(silent=True) or {}
    kg = float(d.get("annual_kg", 0))
    t  = float(d.get("annual_tonnes", 0))
    if kg == 0 and t == 0:
        return error("Provide annual_kg or annual_tonnes.", 422)
    if t > 0:
        kg = t * 1000
    trees   = EmissionCalculator.trees_to_offset(kg)
    area_m2 = round(trees * 25, 1)
    return success({
        "annual_kg":         kg,
        "trees_required":    trees,
        "area_m2":           area_m2,
        "area_hectares":     round(area_m2 / 10_000, 4),
        "kg_per_tree_year":  KG_CO2_PER_TREE_PER_YEAR,
        "offset_options": [
            {"method": "Plant trees",            "units": trees,
             "unit_label": "trees"},
            {"method": "Rooftop solar (kW)",     "units": round(kg/850, 2),
             "unit_label": "kW"},
            {"method": "Verified carbon credits","units": round(kg/1000, 3),
             "unit_label": "tonnes CO2e"},
        ]
    })
