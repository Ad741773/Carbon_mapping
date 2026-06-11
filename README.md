                                      # 🌿 EcoTrace — Carbon Intelligence Platform

Production-ready carbon footprint tracking and sustainability platform that helps users calculate, monitor, analyze, and reduce their environmental impact.

🌐 Live Demo: https://ecotrac.onrender.com/

📂 GitHub Repository: https://github.com/Ad741773/Carbon_mapping

---

## Chosen Vertical

### Sustainability & Climate Technology

EcoTrace is designed to help individuals understand their carbon footprint through intelligent tracking, analytics, prediction, and sustainability recommendations.

The platform combines environmental awareness with data analytics and AI-driven insights to encourage sustainable living habits.

---

## Approach and Logic

The solution follows a modular architecture consisting of a modern frontend dashboard and a Flask-based backend API.

### User Flow

1. User creates an account and logs in securely.
2. User enters lifestyle and consumption data.
3. Carbon emissions are calculated using emission factors.
4. Records are stored and analyzed.
5. Dashboard visualizes trends and insights.
6. AI and rule-based recommendations are generated.
7. Sustainability score is calculated.
8. Future emissions are predicted using machine learning logic.
9. Users can set goals and track progress.

---

## How the Solution Works

### Authentication System

- User Registration
- Login
- JWT-based Authentication
- Secure Session Management

### Carbon Footprint Calculator

Calculates emissions from:

- Transportation
- Electricity Usage
- Fuel Consumption
- Food Habits

### Dashboard Analytics

Provides:

- Daily Emissions
- Weekly Emissions
- Monthly Emissions
- Yearly Emissions
- Category Breakdown
- Emission Trends

### Sustainability Score

Generates a score between 0–100 based on:

- Emission Levels
- Consumption Patterns
- Environmental Impact

### AI Recommendations

Provides personalized suggestions to reduce emissions through:

- Rule-Based Analysis
- Gemini AI Integration (Optional)

### Goal Tracking

Users can:

- Set Sustainability Goals
- Monitor Progress
- Track Achievement Status

### Carbon Offset Module

Calculates:

- Trees Required
- Carbon Offset Requirements
- Sustainability Improvements

### ML Prediction

Forecasts future emissions using historical user data and trend analysis.

### Reports

Users can export:

- CSV Reports
- PDF Reports

---

## Key Features

✅ Carbon Footprint Calculator

✅ Sustainability Dashboard

✅ JWT Authentication

✅ AI Recommendations

✅ Sustainability Score

✅ Goal Tracking

✅ Carbon Offset Calculator

✅ Leaderboard System

✅ Emission Prediction

✅ CSV Export

✅ PDF Report Generation

✅ Responsive User Interface

---

## Technology Stack

### Frontend

- HTML5
- CSS3
- JavaScript
- Chart.js

### Backend

- Flask
- SQLite
- PyJWT
- NumPy

### AI Integration

- Google Gemini API (Optional)

### Deployment

- Render

---

## Assumptions Made

- User-provided data is assumed to be accurate.
- Standard carbon emission factors are used for calculations.
- SQLite is sufficient for demonstration and prototype purposes.
- Prediction results are trend-based estimates.
- Sustainability scores are intended for awareness and comparison purposes.

---

## Future Enhancements

- Advanced Machine Learning Models
- Mobile Application
- IoT Device Integration
- Renewable Energy Tracking
- Organization-Level Dashboards
- Community Sustainability Challenges
- Carbon Credit Marketplace Integration

---

## Project Structure

```text
ecotrace/
├── run.py
├── requirements.txt
├── Dockerfile
├── app/
│   ├── routes/
│   ├── services/
│   ├── utils/
│   └── db.py
├── docs/
└── README.md
