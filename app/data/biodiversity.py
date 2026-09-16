"""
GBIF biodiversity data client.
Fetches species occurrence data to estimate species richness
and infer habitat diversity for a location.
API docs: https://techdocs.gbif.org/en/openapi/
"""
import math
import requests
from typing import Dict, Any, List


GBIF_OCCURRENCE_API = "https://api.gbif.org/v1/occurrence/search"


def get_species_richness(lat: float, lon: float, radius_km: float = 10.0) -> Dict[str, Any]:
    """
    Fetch species occurrence records from GBIF around a location.
    Returns unique species count and a sample of species names.
    """
    # Convert radius in km to a bounding box (approx)
    delta = radius_km / 111.0

    params = {
        "decimalLatitude": f"{lat - delta},{lat + delta}",
        "decimalLongitude": f"{lon - delta},{lon + delta}",
        "limit": 300,
        "hasCoordinate": "true",
        "hasGeospatialIssue": "false",
    }

    try:
        response = requests.get(GBIF_OCCURRENCE_API, params=params, timeout=20)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        total_count = data.get("count", 0)

        # Extract unique species
        species_set = set()
        species_sample: List[Dict[str, Any]] = []
        kingdom_count: Dict[str, int] = {}

        for occ in results:
            species_name = occ.get("species") or occ.get("acceptedScientificName")
            kingdom = occ.get("kingdom", "Unknown")

            if species_name:
                if species_name not in species_set:
                    species_set.add(species_name)
                    species_sample.append({
                        "name": species_name,
                        "kingdom": kingdom,
                        "year": occ.get("year"),
                    })
                kingdom_count[kingdom] = kingdom_count.get(kingdom, 0) + 1

        unique_count = len(species_set)

        if unique_count > 50:
            richness_indicator = "high"
        elif unique_count > 20:
            richness_indicator = "medium"
        elif unique_count > 5:
            richness_indicator = "low"
        else:
            richness_indicator = "very_low"

        return {
            "total_occurrences": total_count,
            "unique_species_sampled": unique_count,
            "species_sample": species_sample[:20],
            "kingdom_distribution": kingdom_count,
            "richness_indicator": richness_indicator,
        }

    except requests.RequestException as e:
        print(f"GBIF API error: {e}")
        return {}
    except Exception as e:
        print(f"GBIF parse error: {e}")
        return {}


def get_habitat_diversity(species_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Infer habitat diversity from species composition using
    a Shannon-like diversity proxy across kingdoms.
    """
    if not species_data or not species_data.get("kingdom_distribution"):
        return {}

    kingdom_count = species_data["kingdom_distribution"]
    total = sum(kingdom_count.values())
    if total == 0:
        return {"habitat_diversity": "unknown"}

    # Shannon diversity index
    shannon = -sum(
        (c / total) * math.log(c / total)
        for c in kingdom_count.values() if c > 0
    )

    if shannon > 1.0:
        habitat = "high"
    elif shannon > 0.5:
        habitat = "medium"
    elif shannon > 0.2:
        habitat = "low"
    else:
        habitat = "very_low"

    return {
        "kingdom_richness": len(kingdom_count),
        "shannon_proxy": round(shannon, 3),
        "habitat_diversity": habitat,
    }


# ---------- Self-test ----------
if __name__ == "__main__":
    lat, lon = 18.52, 73.85  # Pune, India
    print(f"Fetching GBIF biodiversity data for ({lat}, {lon})...\n")
    species = get_species_richness(lat, lon, radius_km=10.0)

    if not species:
        print("No data returned. Try again or check internet connection.")
    else:
        print(f"Total occurrences recorded:  {species['total_occurrences']:,}")
        print(f"Unique species in sample:    {species['unique_species_sampled']}")
        print(f"Richness indicator:          {species['richness_indicator']}")
        print(f"Kingdom distribution:        {species['kingdom_distribution']}")

        print("\nSample species:")
        for sp in species["species_sample"][:10]:
            print(f"  - {sp['name']} ({sp['kingdom']})")

        print("\nHabitat diversity:")
        habitat = get_habitat_diversity(species)
        for k, v in habitat.items():
            print(f"  {k}: {v}")