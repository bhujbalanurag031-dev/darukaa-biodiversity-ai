"""
Soil data client with multiple providers.

Primary: Open-Meteo (reliable, no key required)
Secondary: SoilGrids (optional, may time out)
"""
import requests
from typing import Optional, Dict, Any


# ---------- Open-Meteo (Primary) ----------
OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"


def get_soil_moisture_openmeteo(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch soil moisture and temperature from Open-Meteo.
    Returns current values plus a simple health indicator.
    """
    params = {
        "latitude": lat,
        "longitude": lon,
        "hourly": "soil_moisture_0_to_7cm,soil_temperature_0_to_7cm",
        "forecast_days": 1,
    }

    try:
        response = requests.get(OPEN_METEO_BASE, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()

        hourly = data.get("hourly", {})
        moisture_values = hourly.get("soil_moisture_0_to_7cm", [])
        temp_values = hourly.get("soil_temperature_0_to_7cm", [])

        # Get latest non-null value
        moisture = None
        for v in reversed(moisture_values):
            if v is not None:
                moisture = round(v, 3)
                break

        soil_temp = None
        for v in reversed(temp_values):
            if v is not None:
                soil_temp = round(v, 1)
                break

        result: Dict[str, Any] = {
            "soil_moisture_m3_m3": moisture,
            "soil_temperature_c": soil_temp,
            "source": "open-meteo",
        }

        # Interpretation
        if moisture is not None:
            if moisture < 0.1:
                result["moisture_status"] = "very_dry"
            elif moisture < 0.2:
                result["moisture_status"] = "dry"
            elif moisture < 0.35:
                result["moisture_status"] = "optimal"
            else:
                result["moisture_status"] = "wet"

        return result

    except requests.RequestException as e:
        print(f"Open-Meteo soil error: {e}")
        return {}
    except Exception as e:
        print(f"Open-Meteo soil parse error: {e}")
        return {}


# ---------- SoilGrids (Optional Fallback) ----------
SOILGRIDS_BASE = "https://rest.isric.org/soilgrids/v2.0/properties/query"


def get_soil_properties_soilgrids(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch soil properties from SoilGrids. May time out.
    Use as a bonus source, not primary.
    """
    params = {
        "lon": lon,
        "lat": lat,
        "property": ["phh2o", "soc", "nitrogen"],
        "depth": ["0-5cm"],
        "value": ["mean"],
    }

    try:
        response = requests.get(SOILGRIDS_BASE, params=params, timeout=8)
        response.raise_for_status()
        data = response.json()

        result: Dict[str, Any] = {}
        layers = data.get("properties", {}).get("layers", [])
        for layer in layers:
            name = layer.get("name")
            depths = layer.get("depths", [])
            if not depths:
                continue
            raw = depths[0].get("values", {}).get("mean")
            if raw is None:
                continue

            if name == "phh2o":
                result["ph"] = round(raw / 10.0, 2)
            elif name == "soc":
                result["organic_carbon_pct"] = round(raw / 100.0, 3)
            elif name == "nitrogen":
                result["nitrogen_g_per_kg"] = round(raw / 100.0, 2)

        if result:
            result["source"] = "soilgrids"
        return result

    except requests.RequestException:
        # Expected — SoilGrids is unreliable
        return {}
    except Exception:
        return {}


# ---------- Unified Interface ----------
def get_soil_properties(lat: float, lon: float) -> Dict[str, Any]:
    """
    Unified soil data fetch. Tries Open-Meteo first (reliable),
    then optionally enriches with SoilGrids if available.
    """
    soil = get_soil_moisture_openmeteo(lat, lon)

    # Try to enrich with SoilGrids (non-blocking, may fail)
    soilgrids_data = get_soil_properties_soilgrids(lat, lon)
    if soilgrids_data:
        soil.update(soilgrids_data)

    return soil


def interpret_soil_health(soil: Dict[str, Any]) -> Dict[str, str]:
    """Qualitative health indicators from raw soil values."""
    interpretation: Dict[str, str] = {}

    ph = soil.get("ph")
    if ph is not None:
        if ph < 5.5:
            interpretation["ph_status"] = "acidic"
        elif ph > 7.5:
            interpretation["ph_status"] = "alkaline"
        else:
            interpretation["ph_status"] = "neutral_optimal"

    soc = soil.get("organic_carbon_pct")
    if soc is not None:
        if soc < 0.5:
            interpretation["carbon_status"] = "very_low"
        elif soc < 1.0:
            interpretation["carbon_status"] = "low"
        elif soc < 2.0:
            interpretation["carbon_status"] = "medium"
        else:
            interpretation["carbon_status"] = "high"

    moisture = soil.get("moisture_status")
    if moisture:
        interpretation["moisture_status"] = moisture

    return interpretation


# ---------- Self-test ----------
if __name__ == "__main__":
    lat, lon = 18.52, 73.85
    print(f"Fetching soil data for ({lat}, {lon})...")
    soil = get_soil_properties(lat, lon)
    print("Raw soil data:")
    for k, v in soil.items():
        print(f"  {k}: {v}")
    print("\nInterpretation:")
    for k, v in interpret_soil_health(soil).items():
        print(f"  {k}: {v}")