"""
Pydantic schemas for request/response contracts.
These enforce the structured output the judges asked for.
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class TimeHorizon(str, Enum):
    SHORT = "short_term"     # < 1 year
    MEDIUM = "medium_term"   # 1-3 years
    LONG = "long_term"       # > 3 years


class Confidence(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


# ---------- Input ----------
class Location(BaseModel):
    lat: float = Field(..., ge=-90, le=90)
    lon: float = Field(..., ge=-180, le=180)


class SoilMetrics(BaseModel):
    ph: Optional[float] = None
    organic_carbon_pct: Optional[float] = None
    moisture_status: Optional[str] = None
    soil_moisture_m3_m3: Optional[float] = None
    soil_temperature_c: Optional[float] = None


class ClimateMetrics(BaseModel):
    rainfall_mm: Optional[float] = None
    temp_c: Optional[float] = None
    climate_zone: Optional[str] = None


class BiodiversityMetrics(BaseModel):
    species_richness: Optional[str] = None
    habitat_diversity: Optional[str] = None
    unique_species_count: Optional[int] = None
    key_species: Optional[List[str]] = None


class UserInput(BaseModel):
    query: str
    location: Optional[Location] = None
    soil: Optional[SoilMetrics] = None
    land_use: Optional[str] = None
    climate: Optional[ClimateMetrics] = None
    biodiversity: Optional[BiodiversityMetrics] = None
    conversation_id: Optional[str] = "default"


# ---------- Output ----------
class Evidence(BaseModel):
    source: str
    title: Optional[str] = None
    page: Optional[int] = None
    excerpt: Optional[str] = None


class Recommendation(BaseModel):
    recommendation: str
    why_it_works: str
    impacted_metrics: List[str]
    time_horizon: TimeHorizon
    confidence: Confidence
    evidence: List[Evidence] = []


class ChatResponse(BaseModel):
    response: str
    recommendations: List[Recommendation] = []
    follow_up_questions: List[str] = []
    retrieved_sources: List[str] = []
    reasoning_trace: Optional[str] = None
    environmental_profile: dict = {}