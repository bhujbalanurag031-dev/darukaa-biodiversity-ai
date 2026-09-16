"""
Download free environmental science PDFs and reports
to build our RAG knowledge base.
"""
import os
import requests
from urllib.parse import urlparse

DOCS_DIR = "data/raw"

# Curated free documents from authoritative sources
DOCUMENT_SOURCES = [
    # IPCC AR6 - Land & Agriculture (very authoritative)
    {
        "name": "IPCC_AR6_Chapter7_Land.pdf",
        "url": "https://www.ipcc.ch/report/ar6/wg3/downloads/report/IPCC_AR6_WGIII_Chapter07.pdf",
    },
    # IPBES Global Biodiversity Assessment (Summary for Policymakers)
    {
        "name": "IPBES_Biodiversity_SPM.pdf",
        "url": "https://www.ipbes.net/sites/default/files/2020-02/ipbes_global_assessment_report_summary_for_policymakers.pdf",
    },
    # FAO - Soil Organic Carbon and Agriculture
    {
        "name": "FAO_Soil_Organic_Carbon.pdf",
        "url": "https://www.fao.org/3/i6937e/i6937e.pdf",
    },
    # FAO - Cover Crops and Ecosystem Services
    {
        "name": "FAO_Cover_Crops.pdf",
        "url": "https://www.fao.org/3/ca8000en/ca8000en.pdf",
    },
    # IPCC Special Report on Climate Change and Land (SPM)
    {
        "name": "IPCC_SRCCL_SPM.pdf",
        "url": "https://www.ipcc.ch/site/assets/uploads/2019/08/4.-SPM_Approved_Microsite_FINAL.pdf",
    },
]


def download_document(name: str, url: str) -> bool:
    """Download a single document to data/raw/."""
    os.makedirs(DOCS_DIR, exist_ok=True)
    filepath = os.path.join(DOCS_DIR, name)

    if os.path.exists(filepath):
        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"  Already exists: {name} ({size_mb:.1f} MB)")
        return True

    try:
        print(f"  Downloading: {name}...")
        response = requests.get(url, timeout=60, stream=True)
        response.raise_for_status()

        with open(filepath, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        size_mb = os.path.getsize(filepath) / (1024 * 1024)
        print(f"  ✓ Saved: {name} ({size_mb:.1f} MB)")
        return True

    except requests.RequestException as e:
        print(f"  ✗ Failed: {name} — {e}")
        # Delete partial file if exists
        if os.path.exists(filepath):
            os.remove(filepath)
        return False


def main():
    print("Downloading environmental science documents...\n")
    success = 0
    for doc in DOCUMENT_SOURCES:
        if download_document(doc["name"], doc["url"]):
            success += 1

    print(f"\n{success}/{len(DOCUMENT_SOURCES)} documents downloaded successfully.")
    print(f"Location: {os.path.abspath(DOCS_DIR)}")


if __name__ == "__main__":
    main()