"""
Streamlit chat UI for Darukaa.Earth Biodiversity AI.
Talks to the FastAPI backend via API_URL env var.
"""
import streamlit as st
import requests
import os
import json

# ---------- Config ----------
API_URL = os.getenv("API_URL", "http://localhost:8000")
TIMEOUT = 240

st.set_page_config(
    page_title="Darukaa.Earth Biodiversity AI",
    page_icon="🌿",
    layout="wide",
)

st.title("🌿 Darukaa.Earth Biodiversity Intelligence")
st.caption(
    "An AI environmental scientist — evidence-backed recommendations for biodiversity restoration"
)

# ---------- Session state ----------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = "session_1"
if "last_result" not in st.session_state:
    st.session_state.last_result = None

# ---------- Sidebar ----------
with st.sidebar:
    st.header("📍 Location (optional)")
    use_location = st.checkbox(
        "Auto-fetch environmental data from coordinates",
        key="use_location",
    )

    if use_location:
        lat = st.number_input(
            "Latitude", value=18.52, format="%.4f",
            min_value=-90.0, max_value=90.0, key="lat",
        )
        lon = st.number_input(
            "Longitude", value=73.85, format="%.4f",
            min_value=-180.0, max_value=180.0, key="lon",
        )
        st.caption("Tip: 18.52, 73.85 = Pune, India")
    else:
        lat, lon = None, None

    st.divider()
    st.header("🌱 Environmental Profile (optional)")

    land_use = st.selectbox(
        "Land use type",
        ["", "cropland", "degraded_cropland", "forest", "grassland", "wetland", "urban", "plantation"],
        key="land_use",
    )

    st.markdown("**Soil**")
    soil_ph = st.number_input(
        "pH", min_value=0.0, max_value=14.0, value=0.0, step=0.1, key="soil_ph"
    )
    soil_soc = st.number_input(
        "Organic carbon (%)", min_value=0.0, max_value=20.0, value=0.0, step=0.1, key="soil_soc"
    )
    soil_moisture = st.selectbox(
        "Moisture level",
        ["", "very_dry", "dry", "optimal", "wet"],
        key="soil_moisture",
    )

    st.markdown("**Climate**")
    rainfall = st.number_input(
        "Annual rainfall (mm)", min_value=0.0, max_value=6000.0,
        value=0.0, step=10.0, key="rainfall",
    )
    temp = st.number_input(
        "Avg temperature (°C)", min_value=-10.0, max_value=50.0,
        value=0.0, step=0.5, key="temp",
    )

    st.markdown("**Biodiversity**")
    species_richness = st.selectbox(
        "Species richness",
        ["", "very_low", "low", "medium", "high"],
        key="species_richness",
    )
    habitat_diversity = st.selectbox(
        "Habitat diversity",
        ["", "very_low", "low", "medium", "high"],
        key="habitat_diversity",
    )

    st.divider()
    show_reasoning = st.checkbox("Show reasoning trace", value=False, key="show_reasoning")
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.session_state.last_result = None
        st.rerun()


# ---------- Build payload from session state ----------
def build_payload(query: str) -> dict:
    payload = {
        "query": query,
        "conversation_id": st.session_state.conversation_id,
    }

    # Location
    if st.session_state.get("use_location"):
        if st.session_state.get("lat") and st.session_state.get("lon"):
            payload["location"] = {
                "lat": st.session_state.lat,
                "lon": st.session_state.lon,
            }

    # Land use
    if st.session_state.get("land_use"):
        payload["land_use"] = st.session_state.land_use

    # Soil — read directly from session state (more reliable than local vars)
    soil = {}
    if st.session_state.get("soil_ph", 0) > 0:
        soil["ph"] = st.session_state.soil_ph
    if st.session_state.get("soil_soc", 0) > 0:
        soil["organic_carbon_pct"] = st.session_state.soil_soc
    if st.session_state.get("soil_moisture"):
        soil["moisture_status"] = st.session_state.soil_moisture
    if soil:
        payload["soil"] = soil

    # Climate
    climate = {}
    if st.session_state.get("rainfall", 0) > 0:
        climate["rainfall_mm"] = st.session_state.rainfall
    if st.session_state.get("temp", 0) != 0:
        climate["temp_c"] = st.session_state.temp
    if climate:
        payload["climate"] = climate

    # Biodiversity
    biodiversity = {}
    if st.session_state.get("species_richness"):
        biodiversity["species_richness"] = st.session_state.species_richness
    if st.session_state.get("habitat_diversity"):
        biodiversity["habitat_diversity"] = st.session_state.habitat_diversity
    if biodiversity:
        payload["biodiversity"] = biodiversity

    return payload


# ---------- Render recommendation card ----------
def render_recommendation(idx: int, rec: dict):
    title_preview = rec.get("recommendation", "")[:90]
    with st.expander(f"**Recommendation {idx}:** {title_preview}..."):
        st.markdown("### ✅ What to do")
        st.markdown(rec.get("recommendation", "N/A"))

        st.markdown("### 🧪 Why it works")
        st.markdown(rec.get("why_it_works", "N/A"))

        col1, col2, col3 = st.columns(3)
        with col1:
            metrics = rec.get("impacted_metrics", [])
            if isinstance(metrics, list) and metrics:
                st.markdown("**📊 Impacted metrics**")
                for m in metrics:
                    st.markdown(f"- `{m}`")
        with col2:
            st.markdown("**⏳ Time horizon**")
            st.markdown(f"`{rec.get('time_horizon', 'N/A')}`")
        with col3:
            st.markdown("**🎯 Confidence**")
            st.markdown(f"`{rec.get('confidence', 'N/A')}`")

        evidence = rec.get("evidence", [])
        if evidence:
            st.markdown("### 📚 Evidence")
            for ev in evidence:
                if isinstance(ev, dict):
                    src = ev.get("source", "unknown")
                    page = ev.get("page")
                    title = ev.get("title", "")
                    excerpt = ev.get("excerpt", "")
                    line = f"**{src}**"
                    if page:
                        line += f" (page {page})"
                    if title:
                        line += f" — {title}"
                    st.markdown(f"- {line}")
                    if excerpt:
                        st.caption(f"> {excerpt}")


# ---------- Chat history ----------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg["role"] == "assistant" and msg.get("recommendations"):
            for i, rec in enumerate(msg["recommendations"], 1):
                render_recommendation(i, rec)
        if msg["role"] == "assistant" and msg.get("follow_ups"):
            st.markdown("### ❓ To give better advice, I need:")
            for q in msg["follow_ups"]:
                st.markdown(f"- {q}")


# ---------- Chat input ----------
if prompt := st.chat_input("Describe your environmental concern..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    payload = build_payload(prompt)

    # Show what's being sent (helpful for debugging)
    with st.expander("🔍 Request payload (debug)", expanded=False):
        st.json(payload)

    with st.chat_message("assistant"):
        with st.spinner("Analyzing environmental data and retrieving scientific evidence..."):
            try:
                r = requests.post(
                    f"{API_URL}/api/chat",
                    json=payload,
                    timeout=TIMEOUT,
                )
                r.raise_for_status()
                data = r.json()

                st.markdown(data.get("response", "No response"))

                recommendations = data.get("recommendations", [])
                for i, rec in enumerate(recommendations, 1):
                    render_recommendation(i, rec)

                follow_ups = data.get("follow_up_questions", [])
                if follow_ups:
                    st.markdown("### ❓ To give better advice, I need:")
                    for q in follow_ups:
                        st.markdown(f"- {q}")

                sources = data.get("retrieved_sources", [])
                if sources:
                    with st.expander("📖 Sources retrieved from knowledge base"):
                        for s in sources:
                            st.markdown(f"- `{s}`")

                if st.session_state.get("show_reasoning") and data.get("reasoning_trace"):
                    with st.expander("🧠 Reasoning trace (scientific thinking)"):
                        st.text(data["reasoning_trace"])

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data.get("response", ""),
                    "recommendations": recommendations,
                    "follow_ups": follow_ups,
                })
                st.session_state.last_result = data

            except requests.exceptions.ConnectionError as e:
                st.error(
                    f"❌ **Cannot reach the backend at `{API_URL}`**\n\n"
                    "Possible causes:\n"
                    "- The backend service is asleep (Render free tier) — wait 60s and try again\n"
                    "- The backend crashed due to memory limits (512 MB on free tier)\n"
                    "- Wrong `API_URL` in Streamlit Cloud secrets\n\n"
                    "**If this is the deployed demo:** the free-tier backend is insufficient for "
                    "the embedding model + vector DB. See the project README for local setup, "
                    "which runs the full system."
                )
                st.info(
                    "💡 **Tip:** The system works reliably when run locally. "
                    "Clone the repo and follow the Local Setup instructions in the README."
                )

            except requests.exceptions.Timeout:
                st.error(
                    "⏱️ **Request timed out after 240 seconds.**\n\n"
                    "This is expected on the free-tier backend, which has only 0.1 CPU and 512 MB RAM. "
                    "The reasoning engine needs ~500 MB just for the embedding model and vector store.\n\n"
                    "For the full experience, run locally — see the README."
                )

            except requests.exceptions.HTTPError as e:
                status = e.response.status_code if e.response is not None else "unknown"
                st.error(
                    f"❌ **Backend returned HTTP {status}**\n\n"
                    f"URL: `{API_URL}/api/chat`\n\n"
                    "**If this is 502 Bad Gateway:** the backend was killed mid-request — "
                    "most likely due to the 512 MB memory limit on Render's free tier. "
                    "This is a known platform constraint for ML workloads.\n\n"
                    "The system runs fully locally — see the README for setup instructions."
                )
                st.info(
                    "📸 Screenshots of the working system are available in the "
                    "GitHub repository under `docs/screenshots/`."
                )

            except json.JSONDecodeError:
                st.error("❌ Backend returned invalid JSON. The LLM may have generated malformed output. Try again.")

            except Exception as e:
                st.error(f"❌ Unexpected error: `{type(e).__name__}: {e}`")