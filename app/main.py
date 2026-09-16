"""
FastAPI backend for the Darukaa.Earth Biodiversity AI.

Endpoints:
- GET  /                    -> health check
- GET  /api/health          -> detailed health
- POST /api/enrich          -> auto-fetch environmental data from lat/lon
- POST /api/chat            -> main reasoning endpoint
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import traceback

from app.models.schemas import (
    UserInput,
    ChatResponse,
    SoilMetrics,
    ClimateMetrics,
    BiodiversityMetrics,
)
from app.reasoning.engine import ReasoningEngine
from app.data.soil import get_soil_properties
from app.data.climate import get_climate_data
from app.data.biodiversity import get_species_richness, get_habitat_diversity


app = FastAPI(
    title="Darukaa.Earth Biodiversity AI",
    description="AI-powered environmental scientist with RAG-grounded reasoning",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


_engine: Optional[ReasoningEngine] = None


def get_engine() -> ReasoningEngine:
    global _engine
    if _engine is None:
        print("Initializing reasoning engine...")
        _engine = ReasoningEngine()
        print("Engine ready.")
    return _engine


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Darukaa.Earth Biodiversity AI",
        "version": "1.0.0",
    }


@app.get("/api/health")
def health():
    return {
        "status": "healthy",
        "engine_loaded": _engine is not None,
    }


class EnrichRequest(BaseModel):
    lat: float
    lon: float
    radius_km: float = 10.0


@app.post("/api/enrich")
def enrich(req: EnrichRequest):
    """Auto-fetch all available environmental data for a location."""
    try:
        soil_raw = get_soil_properties(req.lat, req.lon)
        climate_raw = get_climate_data(req.lat, req.lon)
        species_raw = get_species_richness(req.lat, req.lon, req.radius_km)
        habitat_raw = get_habitat_diversity(species_raw) if species_raw else {}

        return {
            "location": {"lat": req.lat, "lon": req.lon},
            "soil": soil_raw,
            "climate": climate_raw,
            "biodiversity": {
                "species": species_raw,
                "habitat": habitat_raw,
            },
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enrichment failed: {e}")


@app.post("/api/chat", response_model=ChatResponse)
def chat(user_input: UserInput):
    """Main reasoning endpoint."""
    try:
        if user_input.location and not user_input.soil:
            soil_raw = get_soil_properties(user_input.location.lat, user_input.location.lon)
            if soil_raw:
                user_input.soil = SoilMetrics(
                    ph=soil_raw.get("ph"),
                    organic_carbon_pct=soil_raw.get("organic_carbon_pct"),
                    moisture_status=soil_raw.get("moisture_status"),
                    soil_moisture_m3_m3=soil_raw.get("soil_moisture_m3_m3"),
                    soil_temperature_c=soil_raw.get("soil_temperature_c"),
                )

        if user_input.location and not user_input.climate:
            climate_raw = get_climate_data(user_input.location.lat, user_input.location.lon)
            if climate_raw:
                user_input.climate = ClimateMetrics(
                    rainfall_mm=climate_raw.get("annual_rainfall_mm"),
                    temp_c=climate_raw.get("avg_temp_c"),
                    climate_zone=climate_raw.get("climate_zone"),
                )

        if user_input.location and not user_input.biodiversity:
            species_raw = get_species_richness(user_input.location.lat, user_input.location.lon)
            if species_raw:
                habitat_raw = get_habitat_diversity(species_raw)
                user_input.biodiversity = BiodiversityMetrics(
                    species_richness=species_raw.get("richness_indicator"),
                    habitat_diversity=habitat_raw.get("habitat_diversity"),
                    unique_species_count=species_raw.get("unique_species_sampled"),
                )

        engine = get_engine()
        result = engine.process(user_input)
        return ChatResponse(**result)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))