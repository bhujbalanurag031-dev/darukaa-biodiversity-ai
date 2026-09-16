import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import requests
import json

print("Sending request to /api/enrich...")
try:
    r = requests.post(
        "http://localhost:8000/api/enrich",
        json={"lat": 18.52, "lon": 73.85},
        timeout=60,
    )
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
except requests.exceptions.ConnectionError:
    print("ERROR: Cannot connect to http://localhost:8000")
    print("Is uvicorn still running in the other terminal?")
except requests.exceptions.Timeout:
    print("ERROR: Request timed out after 60s")
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")