# 🌿 EcoTrace — Carbon Footprint Platform Backend

Production-ready Flask REST API for tracking, analysing, and reducing carbon footprints.
Zero heavy dependencies — runs on **Flask + PyJWT + SQLite + numpy**.

---

## Project Structure

```
ecotrace/
├── run.py                              ← Entry point
├── requirements.txt
├── .env.example
├── Dockerfile
│
├── app/
│   ├── __init__.py                     ← App factory, CORS, blueprints
│   ├── db.py                           ← SQLite3 connection pool + schema
│   │
│   ├── routes/
│   │   ├── auth.py                     ← Register, login, refresh, profile
│   │   ├── calculator.py               ← Emission calculation endpoints
│   │   ├── tracking.py                 ← CRUD for daily carbon records
│   │   ├── dashboard.py                ← Analytics aggregation
│   │   ├── goals.py                    ← Goal tracking CRUD
│   │   ├── recommendations.py          ← AI / rule-based tips
│   │   ├── leaderboard.py              ← User ranking
│   │   ├── offset.py                   ← Tree & offset calculator
│   │   ├── prediction.py               ← 12-month ML forecast
│   │   └── reports.py                  ← CSV + PDF export
│   │
│   ├── services/
│   │   ├── emission_calculator.py      ← Factors + formulas
│   │   ├── score_engine.py             ← 0-100 sustainability score
│   │   ├── recommendation_engine.py    ← Rule-based + Gemini AI tips
│   │   ├── prediction_service.py       ← Linear regression forecast
│   │   └── analytics_service.py        ← Dashboard aggregation
│   │
│   └── utils/
│       ├── jwt_utils.py                ← PyJWT helpers + @jwt_required
│       └── helpers.py                  ← success/error response builders
│
└── docs/
    └── API.md                          ← Full API documentation
```

---

## Quick Start

```bash
# 1. Enter directory
cd ecotrace

# 2. Copy env config
cp .env.example .env
# ✏️  Edit .env — set SECRET_KEY and JWT_SECRET_KEY

# 3. Install dependencies (all minimal / likely pre-installed)
pip install flask pyjwt python-dotenv numpy werkzeug
pip install reportlab        # optional — PDF export
pip install google-generativeai  # optional — Gemini AI tips

# 4. Run
python run.py
```

Server at → **http://localhost:5000**

---

## Feature Overview

| Feature | Endpoint | Details |
|---------|----------|---------|
| **JWT Auth** | `/api/auth/*` | Register, login, refresh; bcrypt passwords |
| **Calculator** | `/api/calculator/calculate` | 9 transport modes, electricity, LPG/CNG/PNG, 4 food types |
| **Tracking** | `/api/tracking/*` | Full CRUD — log and manage daily records |
| **Dashboard** | `/api/dashboard/` | Daily/weekly/monthly/yearly + trend + breakdown |
| **Score** | embedded in dashboard | 0–100 grade with A+→F and global percentile |
| **Recommendations** | `/api/recommendations/` | Rule engine (always) or Gemini AI (if key set) |
| **Leaderboard** | `/api/leaderboard/` | Rank by score or lowest footprint; shows your rank |
| **Goals** | `/api/goals/*` | Create, track progress, auto-complete at 100% |
| **Offset** | `/api/offset/` | Trees, solar kW, carbon credits |
| **Prediction** | `/api/prediction/` | 12-month linear regression forecast |
| **CSV Export** | `/api/reports/csv` | Download records as CSV |
| **PDF Report** | `/api/reports/pdf` | ReportLab PDF with score + table |

---

## Environment Variables

| Variable | Required | Default |
|----------|----------|---------|
| `SECRET_KEY` | ✅ | — |
| `JWT_SECRET_KEY` | ✅ | — |
| `DATABASE_URL` | ❌ | `ecotrace.db` |
| `JWT_ACCESS_TOKEN_EXPIRES` | ❌ | `86400` (24 h) |
| `GEMINI_API_KEY` | ❌ | blank → rule engine |

---

## Production Deployment

```bash
# Gunicorn
gunicorn "run:app" -w 4 -b 0.0.0.0:5000 --timeout 120

# Docker
docker build -t ecotrace .
docker run -p 5000:5000 --env-file .env ecotrace
```

---

## Sample API Calls

```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Priya","email":"priya@test.com","password":"Test@1234"}'

# Calculate footprint
curl -X POST http://localhost:5000/api/calculator/calculate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"trips":[{"mode":"petrol_car","distance_km":40}],
       "electricity_kwh":200,"fuel":{"lpg_cylinders":1},"food_type":"vegetarian"}'

# Get dashboard
curl http://localhost:5000/api/dashboard/ \
  -H "Authorization: Bearer <token>"
```

See `docs/API.md` for complete documentation.
