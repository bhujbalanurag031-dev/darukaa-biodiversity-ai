import requests
import json

URL = "https://darukaa-biodiversity-ai.onrender.com"

print("1. Health check...")
health = requests.get(URL + "/", timeout=180)
print("   ", health.json())

print("\n2. Chat request (may take 60-180s on cold start)...")
payload = {
    "query": "How can I improve biodiversity on my degraded cropland?",
    "land_use": "degraded_cropland",
    "soil": {"ph": 6.2, "organic_carbon_pct": 0.7, "moisture_status": "dry"},
    "climate": {"rainfall_mm": 850, "temp_c": 26, "climate_zone": "tropical_seasonal"},
    "biodiversity": {"species_richness": "low", "habitat_diversity": "low"},
}
r = requests.post(URL + "/api/chat", json=payload, timeout=300)
print("   Status:", r.status_code)

data = r.json()
print("\n3. Results:")
print("   Response:", data.get("response", "")[:400])
print("   Recommendations:", len(data.get("recommendations", [])))
print("   Sources:", data.get("retrieved_sources", []))