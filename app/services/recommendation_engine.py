"""AI Recommendation Engine — rule-based with optional Gemini AI."""
import os, json
from datetime import date, timedelta
from app.db import fetchall

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")


def rule_based_tips(profile: dict) -> list:
    tips = []
    t    = profile.get("avg_transport",   0)
    e    = profile.get("avg_electricity", 0)
    f    = profile.get("avg_fuel",        0)
    food = profile.get("food_type",       "vegetarian")

    if t > 3.0:
        tips.append("🚌 Use public transport (bus/train) at least twice a week — saves up to 2.4 kg CO₂/day.")
    if t > 5.0:
        tips.append("🚗 Carpool on your daily commute — sharing halves your transport emissions.")
    tips.append("🚴 Replace trips under 3 km with cycling or walking — zero emissions, great for health!")

    if e > 1.5:
        tips.append("💡 Switch all bulbs to LED — they use 75% less energy and last 15× longer.")
    if e > 2.0:
        tips.append("❄️ Set AC to 24°C — each degree lower raises energy use by ~6%.")
    tips.append("🔌 Unplug idle chargers and appliances — standby power can add 10% to your electricity bill.")

    if f > 1.0:
        tips.append("♨️ Use a pressure cooker — cuts LPG/PNG usage by up to 50%.")
    if f > 2.0:
        tips.append("☀️ Install a solar water heater to replace gas-based water heating.")

    if food == "non_veg":
        tips.append("🥗 Try 'Meatless Monday' — one plant-based day/week saves ~0.55 kg CO₂ per meal.")
        tips.append("🌾 Cut red-meat meals to twice a week — beef produces 20× more CO₂ than tofu.")
    elif food == "vegetarian":
        tips.append("🌱 Try fully vegan meals a few days a week — saves ~0.2 kg CO₂ per meal.")

    tips.append("♻️ Compost kitchen waste to prevent methane release from landfill.")
    tips.append("🌳 Plant a tree or fund verified reforestation to offset unavoidable emissions.")
    return tips[:8]


def gemini_tips(profile: dict) -> list:
    if not GEMINI_API_KEY:
        return rule_based_tips(profile)
    try:
        import urllib.request
        prompt = (
            "You are a sustainability expert. Monthly carbon profile:\n"
            f"- Transport: {profile.get('avg_transport',0):.2f} kg CO2e/day\n"
            f"- Electricity: {profile.get('avg_electricity',0):.2f} kg CO2e/day\n"
            f"- Cooking fuel: {profile.get('avg_fuel',0):.2f} kg CO2e/day\n"
            f"- Food ({profile.get('food_type','vegetarian')}): {profile.get('avg_food',0):.2f} kg CO2e/day\n"
            f"- Sustainability score: {profile.get('score',50)}/100\n\n"
            "Give exactly 6 concise personalised tips to reduce carbon footprint. "
            "Return ONLY a JSON array of strings, no markdown."
        )
        payload = json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.7, "maxOutputTokens": 512}
        }).encode()
        url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
               f"gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}")
        req = urllib.request.Request(url, data=payload,
                                     headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
        text = text.replace("```json","").replace("```","").strip()
        tips = json.loads(text)
        if isinstance(tips, list) and tips:
            return [str(t) for t in tips[:8]]
    except Exception as exc:
        print(f"[Gemini] {exc} — falling back to rule engine.")
    return rule_based_tips(profile)


def generate_recommendations(user_id: int) -> dict:
    since = (date.today() - timedelta(days=30)).isoformat()
    rows  = fetchall(
        "SELECT * FROM carbon_records WHERE user_id=? AND date>=?",
        (user_id, since)
    )
    if rows:
        n = len(rows)
        profile = {
            "avg_transport":   sum(r["transport_emissions"]   for r in rows) / n,
            "avg_electricity": sum(r["electricity_emissions"] for r in rows) / n,
            "avg_food":        sum(r["food_emissions"]        for r in rows) / n,
            "avg_fuel":        sum(r["fuel_emissions"]        for r in rows) / n,
            "food_type":       rows[-1]["food_type"] or "vegetarian",
        }
    else:
        profile = {"avg_transport":2,"avg_electricity":1.5,
                   "avg_food":2.5,"avg_fuel":0.5,"food_type":"vegetarian"}

    from app.services.score_engine import compute_score
    profile["score"] = compute_score(user_id).get("score", 50)

    source = "gemini_ai" if GEMINI_API_KEY else "rule_engine"
    tips   = gemini_tips(profile) if GEMINI_API_KEY else rule_based_tips(profile)
    return {"tips": tips, "source": source, "profile_snapshot": profile}
