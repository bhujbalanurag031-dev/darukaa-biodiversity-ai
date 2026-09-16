"""
NASA POWER API client.
Fetches climate data (temperature, rainfall) for a location.
API docs: https://power.larc.nasa.gov/docs/services/api/
"""
import requests
from typing import Optional, Dict, Any


NASA_POWER_BASE = "https://power.larc.nasa.gov/api/temporal/climatology/point"


def get_climate_data(lat: float, lon: float) -> Dict[str, Any]:
    """
    Fetch climatology data from NASA POWER.

    Returns:
    - avg_temp_c: annual average temperature
    - annual_rainfall_mm: annual total precipitation
    - climate_zone: simple Köppen-like classification
    """
    params = {
        "parameters": "T2M,PRECTOTCORR",
        "community": "AG",
        "longitude": lon,
        "latitude": lat,
        "format": "JSON",
    }

    try:
        response = requests.get(NASA_POWER_BASE, params=params, timeout=25)
        response.raise_for_status()
        data = response.json()

        params_data = data.get("properties", {}).get("parameter", {})

        # T2M: monthly average temperature (12 values, Jan-Dec)
        temps = params_data.get("T2M", {})
        temp_values = [v for v in temps.values() if isinstance(v, (int, float)) and v > -900]
        avg_temp = round(sum(temp_values) / len(temp_values), 1) if temp_values else None

        # PRECTOTCORR: monthly precipitation (mm/day). Annual = sum * days in month
        rains = params_data.get("PRECTOTCORR", {})
        # Each monthly value is mm/day; multiply by ~30.4 to get monthly total
        annual_rain = None
        if rains:
            valid = [v for v in rains.values() if isinstance(v, (int, float)) and v >= 0]
            if valid:
                annual_rain = round(sum(valid) * 30.4, 1)

        result: Dict[str, Any] = {
            "avg_temp_c": avg_temp,
            "annual_rainfall_mm": annual_rain,
        }
        result["climate_zone"] = classify_climate(avg_temp, annual_rain)
        return result

    except requests.RequestException as e:
        print(f"NASA POWER API error: {e}")
        return {}
    except Exception as e:
        print(f"NASA POWER parse error: {e}")
        return {}


def classify_climate(temp: Optional[float], rain: Optional[float]) -> str:
    """Simple Köppen-like climate classification."""
    if temp is None or rain is None:
        return "unknown"

    if temp > 20:
        if rain > 2000:
            return "tropical_wet"
        elif rain > 1000:
            return "tropical_seasonal"
        elif rain < 500:
            return "arid"
        else:
            return "tropical_dry"
    elif temp > 10:
        return "temperate"
    else:
        return "cold"


# ---- Quick self-test when run directly ----
if __name__ == "__main__":
    lat, lon = 18.52, 73.85
    print(f"Fetching climate data for ({lat}, {lon})...")
    climate = get_climate_data(lat, lon)
    for k, v in climate.items():
        print(f"  {k}: {v}")