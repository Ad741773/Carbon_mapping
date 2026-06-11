from flask import Blueprint, request
from app.utils.jwt_utils import jwt_required
from app.services.emission_calculator import (
    EmissionCalculator, TRANSPORT_FACTORS, ELECTRICITY_FACTOR,
    FUEL_FACTORS, FOOD_FACTORS
)
from app.utils.helpers import success, error

calc_bp = Blueprint("calculator", __name__)

VALID_FOODS = ("vegan", "vegetarian", "pescatarian", "non_veg")


@calc_bp.post("/calculate")
@jwt_required()
def calculate():
    d         = request.get_json(silent=True) or {}
    trips     = d.get("trips", [])
    kwh       = float(d.get("electricity_kwh", 0))
    fuel      = d.get("fuel", {})
    food_type = d.get("food_type", "vegetarian")

    if food_type not in VALID_FOODS:
        return error(f"food_type must be one of {VALID_FOODS}", 422)

    result = EmissionCalculator.calculate_monthly(trips, kwh, fuel, food_type)
    result["trees_to_offset"]      = EmissionCalculator.trees_to_offset(result["total_annual_kg"])
    result["global_avg_annual_kg"] = 4500
    result["india_avg_annual_kg"]  = 1700
    return success(result)


@calc_bp.get("/factors")
def emission_factors():
    return success({
        "transport":   TRANSPORT_FACTORS,
        "electricity": ELECTRICITY_FACTOR,
        "fuel":        FUEL_FACTORS,
        "food":        FOOD_FACTORS,
    })


@calc_bp.post("/quick")
@jwt_required()
def quick_calc():
    d    = request.get_json(silent=True) or {}
    cat  = d.get("category")
    val  = float(d.get("value", 0))

    if cat == "transport":
        mode = d.get("mode", "petrol_car")
        return success({"kg_co2e": EmissionCalculator.transport(
            [{"mode": mode, "distance_km": val}]), "unit": "kg/trip"})
    if cat == "electricity":
        return success({"kg_co2e": EmissionCalculator.electricity(val), "unit": "kg/month"})
    if cat == "fuel":
        ft = d.get("fuel_type", "lpg_kg")
        return success({"kg_co2e": EmissionCalculator.fuel({ft: val}), "unit": "kg/input"})
    return error("category must be: transport | electricity | fuel", 422)
