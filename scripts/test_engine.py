import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
from app.reasoning.engine import ReasoningEngine
from app.models.schemas import (
    UserInput, Location, SoilMetrics, ClimateMetrics, BiodiversityMetrics
)

engine = ReasoningEngine()

print("=" * 70)
print("TEST 1: Insufficient info — should ask clarifying questions")
print("=" * 70)
partial = UserInput(query="Biodiversity is declining on my land")
result = engine.process(partial)
print("RESPONSE:", result["response"][:400])
print("FOLLOW-UPS:", result["follow_up_questions"])
print()

print("=" * 70)
print("TEST 2: Full profile — should give multi-metric recommendations")
print("=" * 70)
full = UserInput(
    query="How can I improve biodiversity on my degraded cropland?",
    location=Location(lat=18.52, lon=73.85),
    soil=SoilMetrics(ph=6.2, organic_carbon_pct=0.7, moisture_status="dry"),
    climate=ClimateMetrics(rainfall_mm=850, temp_c=26, climate_zone="tropical_seasonal"),
    biodiversity=BiodiversityMetrics(species_richness="low", habitat_diversity="low"),
    land_use="degraded_cropland",
)
result = engine.process(full)
print("RESPONSE:", result["response"][:500])
print()
print(f"Recommendations returned: {len(result['recommendations'])}")
for i, rec in enumerate(result["recommendations"], 1):
    print(f"\n--- Recommendation {i} ---")
    if isinstance(rec, dict):
        print(json.dumps(rec, indent=2)[:800])
    else:
        print(rec)
print()
print("SOURCES:", result["retrieved_sources"])
print()
print("REASONING TRACE (first 300 chars):")
print((result.get("reasoning_trace") or "")[:300])