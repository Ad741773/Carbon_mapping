# EcoTrace — Full API Documentation
**Version:** 1.0.0 | **Base URL:** `http://localhost:5000/api`

---

## Authentication
All 🔒 endpoints require the header:
```
Authorization: Bearer <access_token>
```

---

## 1. Auth  `/api/auth`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/register` | — | Create account |
| POST | `/login` | — | Get tokens |
| POST | `/refresh` | 🔒 refresh | New access token |
| GET | `/profile` | 🔒 | Get profile |
| PUT | `/profile` | 🔒 | Update profile / password |
| DELETE | `/account` | 🔒 | Delete account |

### POST `/register`
```json
// Request
{
  "name": "Priya Sharma",
  "email": "priya@example.com",
  "password": "Secure@123",
  "city": "Mumbai",
  "country": "India"
}
// Response 201
{
  "success": true,
  "data": {
    "user": { "id":1, "name":"Priya Sharma", "email":"...", "city":"Mumbai" },
    "access_token":  "eyJ...",
    "refresh_token": "eyJ..."
  }
}
```

### POST `/login`
```json
{ "email": "priya@example.com", "password": "Secure@123" }
// → same response shape as /register
```

---

## 2. Calculator  `/api/calculator`

### POST `/calculate` 🔒
```json
// Request
{
  "trips": [
    { "mode": "petrol_car", "distance_km": 40 },
    { "mode": "bus",        "distance_km": 20 },
    { "mode": "train",      "distance_km": 15 }
  ],
  "electricity_kwh": 200,
  "fuel": {
    "lpg_cylinders": 1,
    "png_m3": 0,
    "cng_kg": 0
  },
  "food_type": "vegetarian"
}

// Response
{
  "transport_emissions":   8.68,
  "electricity_emissions": 164.0,
  "fuel_emissions":        42.47,
  "food_emissions":        51.0,
  "total_monthly_kg":      266.15,
  "total_annual_kg":       3193.8,
  "total_annual_tonnes":   3.194,
  "breakdown_pct": {
    "transport": 3.3, "electricity": 61.6, "fuel": 15.9, "food": 19.2
  },
  "trees_to_offset":       146,
  "global_avg_annual_kg":  4500,
  "india_avg_annual_kg":   1700
}
```

**Transport modes:** `petrol_car | diesel_car | cng_car | electric_car | bike | bus | train | flight_short | flight_long`

**Food types:** `vegan | vegetarian | pescatarian | non_veg`

### GET `/factors` (public)
Returns all emission factor constants.

### POST `/quick` 🔒
Single-field calculation.
```json
{ "category": "transport", "mode": "petrol_car", "value": 25 }
{ "category": "electricity", "value": 150 }
{ "category": "fuel", "fuel_type": "lpg_kg", "value": 14.2 }
```

---

## 3. Tracking  `/api/tracking`

Same payload as `/calculator/calculate` plus optional `"date": "YYYY-MM-DD"`.
Stores daily fractions (monthly ÷ 30).

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/log` 🔒 | Log a carbon record |
| GET | `/records?page=1` 🔒 | Paginated records |
| GET | `/records/<id>` 🔒 | Single record |
| PUT | `/records/<id>` 🔒 | Update emissions |
| DELETE | `/records/<id>` 🔒 | Delete record |

---

## 4. Dashboard  `/api/dashboard`

### GET `/` 🔒
```json
{
  "daily":   { "total": 8.4, "transport": 3.1, "electricity": 2.8, "food": 1.7, "fuel": 0.8, "records": 1 },
  "weekly":  { "total": 58.8, ... },
  "monthly": { "total": 252.0, ... },
  "yearly":  { "total": 2940.0, ... },
  "monthly_trend": [
    { "month": "2025-01", "kg": 245.3 },
    { "month": "2025-02", "kg": 238.1 }
  ],
  "category_breakdown": [
    { "category": "Transport",   "kg": 85.2, "pct": 33.8 },
    { "category": "Electricity", "kg": 98.4, "pct": 39.0 },
    { "category": "Food",        "kg": 51.0, "pct": 20.2 },
    { "category": "Fuel",        "kg": 17.8, "pct": 7.1  }
  ],
  "sustainability_score": {
    "score": 72.5,
    "grade": "B",
    "label": "Getting Better",
    "percentile": 70,
    "avg_daily_kg": 8.4,
    "breakdown": {
      "transport":   { "earned": 18.5, "max": 25 },
      "electricity": { "earned": 14.2, "max": 25 }
    }
  }
}
```

---

## 5. Goals  `/api/goals`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/` 🔒 | Create goal |
| GET | `/` 🔒 | List goals |
| GET | `/<id>` 🔒 | Get goal |
| PUT | `/<id>` 🔒 | Update / advance progress |
| DELETE | `/<id>` 🔒 | Delete goal |
| GET | `/<id>/status` 🔒 | Detailed status |

### POST `/` 🔒
```json
{
  "title": "Reduce transport by 20%",
  "description": "Use train and bus more often",
  "category": "transport",
  "target_value": 50.0,
  "end_date": "2025-12-31"
}
// Response includes achievement_pct
```

### PUT `/<id>` 🔒  — update progress
```json
{ "current_value": 30.0 }
// → achievement_pct: 60.0, auto-sets is_completed when 100%
```

---

## 6. Recommendations  `/api/recommendations`

### POST `/` 🔒
Analyses last 30 days → returns personalised tips. Saves to DB.
```json
// Response
{
  "tips": [
    "🚌 Use public transport at least twice a week — saves 2.4 kg CO₂/day.",
    "💡 Switch all bulbs to LED — 75% less energy.",
    "🥗 Try Meatless Monday — saves ~0.55 kg CO₂ per meal.",
    "🔌 Unplug idle chargers — standby power adds 10% to your bill.",
    "♨️ Use a pressure cooker — cuts LPG usage by 50%.",
    "🌳 Fund reforestation to offset unavoidable emissions."
  ],
  "source": "rule_engine",
  "profile_snapshot": { "avg_transport": 2.4, "avg_electricity": 1.8, ... }
}
```
Set `GEMINI_API_KEY` in `.env` to upgrade source to `"gemini_ai"`.

### GET `/history` 🔒
Last 10 recommendation sets.

---

## 7. Leaderboard  `/api/leaderboard`

### GET `/?mode=score&limit=20` 🔒
```json
{
  "leaderboard": [
    { "rank":1, "name":"Priya Sharma", "city":"Mumbai", "score":94,
      "grade":"A+", "monthly_kg":120.5, "reduction_pct":28.0 },
    ...
  ],
  "my_rank": { "rank":6, "score":72, ... }
}
```
`mode=score` (default) or `mode=footprint` (lowest kg first).

---

## 8. Offset  `/api/offset`

### POST `/` 🔒
```json
// Request
{ "annual_kg": 3189 }
// or { "annual_tonnes": 3.189 }

// Response
{
  "annual_kg": 3189,
  "trees_required": 145,
  "area_m2": 3625,
  "area_hectares": 0.3625,
  "kg_per_tree_year": 22,
  "offset_options": [
    { "method": "Plant trees",             "units": 145,   "unit_label": "trees" },
    { "method": "Rooftop solar (kW)",      "units": 3.75,  "unit_label": "kW" },
    { "method": "Verified carbon credits", "units": 3.189, "unit_label": "tonnes CO2e" }
  ]
}
```

---

## 9. Prediction  `/api/prediction`

### GET `/` 🔒
Linear regression on last 90 days → 12-month forecast.
Requires ≥ 7 days of logged data.
```json
{
  "trend": "decreasing 📉",
  "slope_per_week": -0.042,
  "months": ["Aug","Sep","Oct","Nov","Dec","Jan","Feb","Mar","Apr","May","Jun","Jul"],
  "predictions_kg": [240.0, 234.2, 228.6, 223.1, 217.8, 212.6, 207.5, 202.5, 197.7, 193.0, 188.4, 183.9],
  "annual_forecast": 2529.3,
  "annual_forecast_tonnes": 2.529
}
```

---

## 10. Reports  `/api/reports`

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/csv?days=30` 🔒 | Download CSV |
| GET | `/pdf?days=30` 🔒 | Download PDF *(requires reportlab)* |
| GET | `/summary` 🔒 | JSON dashboard summary |

---

## Health

### GET `/api/health`  (public)
```json
{ "status": "ok", "service": "EcoTrace API", "version": "1.0.0" }
```

---

## Standard Error Shape
```json
{ "success": false, "message": "Descriptive error message", "details": {} }
```

| Code | Meaning |
|------|---------|
| 400 | Bad request |
| 401 | Invalid / expired token |
| 403 | Forbidden |
| 404 | Not found |
| 409 | Conflict (duplicate email) |
| 422 | Validation error |
| 500 | Server error |

---

## Database Schema

```
users                    carbon_records               goals
─────────────────────    ───────────────────────────  ────────────────────────
id  INTEGER PK           id  INTEGER PK               id  INTEGER PK
name  TEXT               user_id  INTEGER FK→users    user_id  INTEGER FK
email  TEXT UNIQUE       date  TEXT (YYYY-MM-DD)      title  TEXT
password_hash  TEXT      transport_emissions  REAL     description  TEXT
city  TEXT               electricity_emissions REAL    category  TEXT
country  TEXT            food_emissions  REAL          target_value  REAL
avatar_url  TEXT         fuel_emissions  REAL          current_value  REAL
is_active  INTEGER       total_emissions  REAL         start_date  TEXT
created_at  TEXT         transport_details  TEXT(JSON) end_date  TEXT
updated_at  TEXT         electricity_kwh  REAL         is_completed  INTEGER
                         fuel_details  TEXT (JSON)     created_at  TEXT
                         food_type  TEXT               updated_at  TEXT
                         created_at  TEXT
                                                        recommendations
                                                        ───────────────
                                                        id  INTEGER PK
                                                        user_id  INTEGER FK
                                                        tips  TEXT (JSON)
                                                        source  TEXT
                                                        created_at  TEXT
```

---

## Emission Factors Reference

| Mode | Factor | Unit |
|------|--------|------|
| Petrol car | 0.192 | kg CO₂e / km |
| Diesel car | 0.171 | kg CO₂e / km |
| CNG car | 0.115 | kg CO₂e / km |
| Electric car | 0.053 | kg CO₂e / km |
| Motorbike | 0.103 | kg CO₂e / km |
| Bus | 0.089 | kg CO₂e / km |
| Train | 0.041 | kg CO₂e / km |
| Flight (short) | 0.255 | kg CO₂e / km |
| Flight (long) | 0.195 | kg CO₂e / km |
| Electricity (India) | 0.82 | kg CO₂e / kWh |
| LPG | 2.983 | kg CO₂e / kg |
| LPG cylinder (14.2 kg) | 42.47 | kg CO₂e / cylinder |
| PNG | 2.204 | kg CO₂e / m³ |
| CNG | 2.540 | kg CO₂e / kg |
| Vegan diet | 1.5 | kg CO₂e / day |
| Vegetarian diet | 1.7 | kg CO₂e / day |
| Pescatarian diet | 2.3 | kg CO₂e / day |
| Non-vegetarian diet | 3.3 | kg CO₂e / day |
