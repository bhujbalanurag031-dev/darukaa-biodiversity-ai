@'
# 🌿 Darukaa.Earth — AI Biodiversity Intelligence

**An AI environmental scientist that reasons about real-world environmental problems with grounded, evidence-backed recommendations.**

**🌐 Live Frontend:** https://darukaa-biodiversity-ai-gm4rlvxbaqzglge5aappu4v.streamlit.app/

**📦 GitHub Repo:** https://github.com/bhujbalanurag031-dev/darukaa-biodiversity-ai

**📖 API Docs:** https://darukaa-biodiversity-ai.onrender.com/docs

Built for the [Darukaa.Earth AI Biodiversity Intelligence Challenge](https://darukaa.com).

---

## 🎯 What It Does

The system behaves like an environmental scientist, not a chatbot:

- **Asks clarifying questions** when environmental inputs are incomplete
- **Retrieves** relevant scientific literature (IPCC, FAO, IPBES reports) via RAG
- **Connects** soil, climate, land use, and biodiversity data into causal chains
- **Produces** structured, actionable recommendations with scientific citations
- **Never** gives generic advice like "use sustainable practices"

### Example: Before vs After

**❌ What we DON'T do:**

> "Use sustainable practices to improve biodiversity."

**✅ What we DO:**

> **Recommendation:** Plant a 3-year rotation of white clover (legume) and native millet as cover crops, establish a 10% agroforestry strip of Acacia / Eucalyptus along field edges, and construct a 200 m² rainwater harvesting pond.
>
> **Why it works:** Cover crops fix atmospheric nitrogen → raise soil organic carbon by 15–25% → enhance microbial diversity → support pollinator-friendly vegetation → boost species richness. Agroforestry adds habitat diversity and provides shade, improving soil moisture and reducing evaporation. Rainwater harvesting increases soil moisture during dry periods, further stimulating microbial activity and carbon sequestration.
>
> **Impacted metrics:** soil_organic_carbon, species_richness, soil_moisture, microbial_diversity
>
> **Time horizon:** medium_term (2–3 years)
>
> **Confidence:** high
>
> **Evidence:** IPCC_SRCCL_SPM.pdf p.41; IPCC_AR6_Chapter7_Land.pdf p.31

---

## 🏗️ Architecture



```
┌────────────────────────────────────────────────────────────┐
│  1. PRESENTATION LAYER — Streamlit Frontend                │
│     • Sidebar: soil, climate, biodiversity, land use       │
│     • Chat: free-text environmental query                  │
│     • Debug panel: shows request payload being sent        │
└────────────────────────────┬───────────────────────────────┘
                             │ POST /api/chat 
                             ▼
┌────────────────────────────────────────────────────────────┐
│  2. ORCHESTRATION LAYER — FastAPI + Reasoning Engine       │
│                                                            │
│     Stage 1: Slot Filler                                   │
│       └─ Checks if soil/climate/land/biodiversity present  │
│       └─ If missing → returns clarifying questions         │
│                                                            │
│     Stage 2: Query Planner                                 │
│       └─ Combines all variables into retrieval query       │
│                                                            │
│     Stage 3: RAG Retriever                                 │
│       └─ Fetches top-3 chunks + page numbers               │
│                                                            │
│     Stage 4: LLM Reasoner (gpt-oss-20b via Groq)           │
│       └─ Enforces ≥3-variable causal chains                │
│       └─ Returns structured JSON with citations            │
│                                                            │
│     Stage 5: Output Formatter (Pydantic)                   │
│       └─ Validates schema, guarantees all fields present   │
└────────────────────────────┬───────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              ▼                             ▼
┌──────────────────────────┐   ┌────────────────────────────┐
│  3A. STRUCTURED DATA     │   │  3B. VECTOR DB (RAG)       │
│  ──────────────────────  │   │  ─────────────────────────  │
│  • Open-Meteo            │   │  • ChromaDB                │
│    (soil moisture)       │   │  • 1,934 embedded chunks   │
│  • NASA POWER            │   │  • IPCC AR6, SRCCL         │
│    (temp, rainfall)      │   │  • FAO soil reports        │
│  • GBIF                  │   │  • IPBES biodiversity      │
│    (species richness)    │   │                            │
│  • SoilGrids             │   │  Embedding: MiniLM-L6-v2   │
│    (pH, SOC)             │   │  Top-K: 3 chunks           │
└──────────────────────────┘   └────────────────────────────┘
```



---

## 📚 Knowledge System Design

### Two-layer knowledge base

The system uses **two complementary knowledge sources**, not just an LLM prompt:

#### 1. Structured environmental data (real-time, real-world)

| Source | Variables Provided | Coverage |
|--------|-------------------|----------|
| Open-Meteo | Soil moisture, soil temperature | Global, hourly |
| NASA POWER | Temperature, rainfall, climate zone | Global, 40+ year climatology |
| GBIF | Species occurrences, richness indicator | Global, 2B+ records |
| SoilGrids | Soil pH, organic carbon, nitrogen (when available) | Global, 250m |

#### 2. Scientific literature (RAG, embedded)

The system indexes **1,934 chunks** from authoritative climate and biodiversity reports:

- **IPCC AR6** — Working Group III, Chapter 7 (Land)
- **IPCC SRCCL** — Special Report on Climate Change and Land (SPM)
- **FAO** — Soil Organic Carbon and Cover Crops reports
- **IPBES** — Global Biodiversity Assessment (Summary for Policymakers)

**Embedding model:** all-MiniLM-L6-v2 (384-dim, local, free)

**Vector DB:** ChromaDB (persistent, on-disk)

**Chunk size:** 500 tokens with 50-token overlap

**Retrieval:** Semantic similarity, top-3 chunks (configurable via TOP_K_RETRIEVAL)

### Retrieval pipeline

```python
query_for_retrieval = build_retrieval_query(user_input)
retrieved = retrieve_with_metadata(query_for_retrieval, k=settings.TOP_K_RETRIEVAL)
context = format_context(retrieved)

The retrieved context is fed to the LLM along with the environmental profile and conversation history. Every recommendation cites specific chunks from these documents.

🧠 Multi-Metric Reasoning (Core Differentiator)
The system never answers a single-variable question. Every recommendation connects at least 3 environmental variables.

Example causal chain built by the reasoning engine:


Legume cover crops
    → fix atmospheric N
    → raise soil organic carbon (15–25% over 2–3 years)
    → improve soil microbial diversity
    → support pollinator-friendly vegetation
    → increase species richness
Variables connected: soil carbon + nitrogen + microbial diversity + pollinator habitat + species richness (5 variables).

The system prompt forbids single-variable answers, and the output schema requires impacted_metrics to contain a list.

💬 Conversational Intelligence
Slot filling
When key environmental inputs are missing, the system refuses to answer and asks for specific data instead:

User: "Biodiversity is declining on my land."

System: "I can give you much more precise, evidence-based recommendations if you share a bit more about your land. Specifically, I need:

soil organic carbon %, pH, or moisture level

rainfall pattern (mm/year) and average temperature (°C)

current land use type (cropland, forest, grassland, urban, degraded)

observed biodiversity indicators (species richness, habitat types)"

Conversation memory
Multi-turn conversations are supported via per-conversation_id history (capped at 12 messages, injected into the LLM system prompt).

Auto-enrichment
If the user provides only geo-coordinates, the system auto-fetches soil, climate, and biodiversity data from the APIs before reasoning — no manual entry required.

📋 Output Format
Every response conforms to a strict Pydantic schema:


{
  "response": "Natural-language 2-4 sentence summary",
  "recommendations": [
    {
      "recommendation": "Specific, actionable, measurable action",
      "why_it_works": "Scientific reasoning (causal chain)",
      "impacted_metrics": ["metric1", "metric2", "metric3"],
      "time_horizon": "short_term | medium_term | long_term",
      "confidence": "low | medium | high",
      "evidence": [{"source": "IPCC_SRCCL_SPM.pdf", "page": 41}]
    }
  ],
  "follow_up_questions": ["..."],
  "retrieved_sources": ["..."],
  "reasoning_trace": "..."
}
Bonus: With the gpt-oss-20b model on Groq, the system captures the model's reasoning trace — the internal chain-of-thought before the answer. This is exposed in the UI via a "Show reasoning trace" toggle.

🛠️ Tech Stack
Layer	Technology
LLM	Groq (openai/gpt-oss-20b) — free, fast, reasoning-capable
Embeddings	sentence-transformers/all-MiniLM-L6-v2 (local)
Vector DB	ChromaDB
Backend	FastAPI + Uvicorn
Frontend	Streamlit
Data APIs	Open-Meteo, NASA POWER, GBIF, SoilGrids
Validation	Pydantic v2
Environment	Python 3.10
Provider-agnostic LLM client: Switch between Groq and OpenAI by setting LLM_PROVIDER in .env.

🌐 Live Demo
Frontend (Streamlit Cloud):
https://darukaa-biodiversity-ai-gm4rlvxbqzg!ge5aappu4v.streamlit.app

Backend API (Render):
https://darukaa-biodiversity-ai.onrender.com

API Documentation:
https://darukaa-biodiversity-ai.onrender.com/docs

⚠️ Note on free-tier limitations: The backend runs on Render's free tier (0.1 CPU, 512 MB RAM, auto-sleep after 15 min). The reasoning pipeline requires ~650 MB RAM at peak, so /api/chat may return HTTP 502 due to the free-tier memory ceiling. This is a platform constraint, not a code defect. The frontend's error message explains this to end users and points to local setup instructions. All screenshots in docs/screenshots/ were captured from live local runs proving the full system works.

🚀 Local Setup
Prerequisites
Python 3.10+

A free Groq API key

Installation

git clone https://github.com/bhujbalanurag031-dev/darukaa-biodiversity-ai.git
cd darukaa-biodiversity-ai
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate
pip install -r requirements.txt

Configuration
Create a .env file in the project root:

LLM_PROVIDER=groq
GROQ_API_KEY=gsk_your_key_here
GROQ_MODEL=openai/gpt-oss-20b
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL=all-MiniLM-L6-v2
TOP_K_RETRIEVAL=3

Build the knowledge base

python scripts/download_docs.py
python -m app.rag.ingest
Expected: ~1,900 chunks indexed in data/chroma/.

Run the system
Terminal 1 — Backend:

uvicorn app.main:app --reload --port 8000
Terminal 2 — Frontend:

streamlit run frontend/app.py --server.port 8501
Open http://localhost:8501 in your browser.

📖 API Usage
POST /api/chat

curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "How can I improve biodiversity on my degraded cropland?", "land_use": "degraded_cropland"}'
POST /api/enrich

curl -X POST http://localhost:8000/api/enrich \
  -H "Content-Type: application/json" \
  -d '{"lat": 18.52, "lon": 73.85}'

  📸 Screenshots
View	Description
https://docs/screenshots/test1_clarifying_questions.png	System asks for missing environmental data instead of guessing
https://docs/screenshots/test2_recommendations.png	Structured recommendation cards with expandable details
https://docs/screenshots/evidence_citations.png	Scientific citations with PDF source and page number
https://docs/screenshots/rag_sources.png	Retrieved chunks from the vector DB
https://docs/screenshots/deployed_payload.png	Live deployment showing request payload reaching the backend

🎯 How This Meets the Challenge Criteria
Criterion	Weight	How We Address It
Depth of Reasoning	30%	Every recommendation connects ≥3 environmental variables through a causal chain.
Scientific Grounding	25%	Every claim cites specific chunks from IPCC/FAO/IPBES reports.
Knowledge System Design	20%	Two-layer knowledge base: real-time API data + RAG over 1,934 chunks.
Conversational Intelligence	15%	Slot-filling refuses to answer incomplete queries. Multi-turn memory.
Output Clarity	10%	Strict Pydantic schema with all required fields.

📂 Project Structure

darukaa-hackathon/
├── app/
│   ├── main.py                    # FastAPI app with all endpoints
│   ├── config.py                  # Settings loaded from .env
│   ├── data/                      # Soil, climate, biodiversity clients
│   ├── rag/                       # ChromaDB, ingest, retriever
│   ├── reasoning/                 # Engine, LLM client
│   ├── conversation/              # Memory
│   └── models/                    # Pydantic schemas
├── frontend/
│   └── app.py                     # Streamlit chat UI
├── scripts/                       # Tests + document download
├── data/
│   ├── raw/                       # Downloaded PDFs (gitignored)
│   └── chroma/                    # Vector DB (committed for deploy)
├── docs/
│   └── screenshots/
├── requirements.txt
└── README.md

🚢 Deployment Notes
Current Status
The system is fully functional locally (verified with all 5 screenshots above). A live deployment is available on Render's free tier, but /api/chat may return HTTP 502 due to memory constraints.

Why the Live Demo May Be Slow
The backend requires the following to serve each /api/chat request:

Embedding model in memory (~80 MB — all-MiniLM-L6-v2)

ChromaDB vector store (~12 MB on disk)

Multi-source API calls (4 sequential requests)

LLM inference via Groq (30–60 seconds)

Total resource requirement: ~650 MB RAM at peak.

Render's free tier provides only 0.1 CPU, 512 MB RAM, auto-sleep after 15 min.

Optimizations Applied for Free-Tier Deployment
Lazy loading — embedding model loads only on first request

Single-thread torch — reduces CPU scheduling overhead

Reduced TOP_K — from 5 to 3 chunks

Explicit garbage collection — after each heavy stage

Despite these, the pipeline peaks at ~650 MB under load. A production deployment requires at least 2 GB RAM.

Why We Report This Honestly
We could have hidden the limitation by pointing the live URL to a cached response. We chose not to, because honest engineering is more valuable than a working demo with hidden mocks.

Deployment Options for Production

Platform	                 Why	                                Est. Cost
Hugging Face Spaces (Pro)	 16 GB RAM, always-on, ML-optimized	  $9/mo
Render (Standard)        	 2 GB RAM, no sleep	                  $25/mo
AWS ECS / GCP Cloud Run	   Auto-scaling, GPU support	          Pay-per-use
Self-hosted VPS	           Full control, cheapest at scale	    $5–10/mo

👤 Author
Anurag Bhujbal

GitHub: @bhujbalanurag031-dev

Submitted for the Darukaa.Earth AI Biodiversity Intelligence Challenge.