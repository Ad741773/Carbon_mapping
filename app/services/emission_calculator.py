"""
Emission Factors (kg CO2e per unit)
Sources: IPCC, UK DEFRA, IEA, India CEA
"""

TRANSPORT_FACTORS = {
    "petrol_car":   0.192,
    "diesel_car":   0.171,
    "cng_car":      0.115,
    "electric_car": 0.053,
    "bike":         0.103,
    "bus":          0.089,
    "train":        0.041,
    "flight_short": 0.255,
    "flight_long":  0.195,
}

ELECTRICITY_FACTOR = 0.82   # kg CO2e/kWh — India average

FUEL_FACTORS = {
    "lpg_kg":        2.983,
    "lpg_cylinders": 42.47,   # 14.2 kg cylinder
    "png_m3":        2.204,
    "cng_kg":        2.540,
}

FOOD_FACTORS = {
    "vegan":        1.5,
    "vegetarian":   1.7,
    "pescatarian":  2.3,
    "non_veg":      3.3,
}

KG_CO2_PER_TREE_PER_YEAR = 22.0


class EmissionCalculator:

    @staticmethod
    def transport(trips: list) -> float:
        total = 0.0
        for t in trips:
            mode   = str(t.get("mode", "")).lower()
            km     = float(t.get("distance_km", 0))
            factor = TRANSPORT_FACTORS.get(mode)
            if factor and km > 0:
                total += km * factor
        return round(total, 4)

    @staticmethod
    def electricity(kwh: float) -> float:
        return round(kwh * ELECTRICITY_FACTOR, 4)

    @staticmethod
    def fuel(inputs: dict) -> float:
        total  = float(inputs.get("lpg_kg", 0))        * FUEL_FACTORS["lpg_kg"]
        total += float(inputs.get("lpg_cylinders", 0)) * FUEL_FACTORS["lpg_cylinders"]
        total += float(inputs.get("png_m3", 0))        * FUEL_FACTORS["png_m3"]
        total += float(inputs.get("cng_kg", 0))        * FUEL_FACTORS["cng_kg"]
        return round(total, 4)

    @staticmethod
    def food(food_type: str, days: int = 30) -> float:
        factor = FOOD_FACTORS.get(food_type.lower(), FOOD_FACTORS["vegetarian"])
        return round(factor * days, 4)

    @classmethod
    def calculate_monthly(cls, trips, kwh, fuel_inputs, food_type) -> dict:
        t  = cls.transport(trips)
        e  = cls.electricity(kwh)
        f  = cls.fuel(fuel_inputs)
        fo = cls.food(food_type, 30)
        total = round(t + e + f + fo, 4)
        safe  = total or 1
        return {
            "transport_emissions":   t,
            "electricity_emissions": e,
            "fuel_emissions":        f,
            "food_emissions":        fo,
            "total_monthly_kg":      total,
            "total_annual_kg":       round(total * 12, 4),
            "total_annual_tonnes":   round(total * 12 / 1000, 4),
            "breakdown_pct": {
                "transport":   round(t  / safe * 100, 1),
                "electricity": round(e  / safe * 100, 1),
                "fuel":        round(f  / safe * 100, 1),
                "food":        round(fo / safe * 100, 1),
            },
        }

    @staticmethod
    def trees_to_offset(annual_kg: float) -> int:
        return max(1, round(annual_kg / KG_CO2_PER_TREE_PER_YEAR))
