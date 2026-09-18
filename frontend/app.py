"""
Streamlit chat UI for Darukaa.Earth Biodiversity AI.
Talks to the FastAPI backend at localhost:8000.
"""
import streamlit as st
import requests
import os

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
    use_location = st.checkbox("Auto-fetch environmental data from coordinates")

    lat, lon = None, None
    if use_location:
        lat = st.number_input("Latitude", value=18.52, format="%.4f", min_value=-90.0, max_value=90.0)
        lon = st.number_input("Longitude", value=73.85, format="%.4f", min_value=-180.0, max_value=180.0)
        st.caption("Tip: 18.52, 73.85 = Pune, India")

    st.divider()
    st.header("🌱 Environmental Profile (optional)")

    land_use = st.selectbox(
        "Land use type",
        ["", "cropland", "degraded_cropland", "forest", "grassland", "wetland", "urban", "plantation"],
    )

    st.markdown("**Soil**")
    soil_ph = st.number_input("pH", 0.0, 14.0, 0.0, 0.1)
    soil_soc = st.number_input("Organic carbon (%)", 0.0, 20.0, 0.0, 0.1)
    soil_moisture = st.selectbox("Moisture level", ["", "very_dry", "dry", "optimal", "wet"])

    st.markdown("**Climate**")
    rainfall = st.number_input("Annual rainfall (mm)", 0.0, 6000.0, 0.0, 10.0)
    temp = st.number_input("Avg temperature (°C)", -10.0, 50.0, 0.0, 0.5)

    st.markdown("**Biodiversity**")
    species_richness = st.selectbox("Species richness", ["", "very_low", "low", "medium", "high"])
    habitat_diversity = st.selectbox("Habitat diversity", ["", "very_low", "low", "medium", "high"])

    st.divider()
    show_reasoning = st.checkbox("Show reasoning trace", value=False)
    if st.button("🗑️ Clear conversation"):
        st.session_state.messages = []
        st.session_state.last_result = None
        st.rerun()


def build_payload(query: str) -> dict:
    payload = {"query": query, "conversation_id": st.session_state.conversation_id}

    if use_location and lat is not None and lon is not None:
        payload["location"] = {"lat": lat, "lon": lon}

    if land_use:
        payload["land_use"] = land_use

    soil = {}
    if soil_ph > 0:
        soil["ph"] = soil_ph
    if soil_soc > 0:
        soil["organic_carbon_pct"] = soil_soc
    if soil_moisture:
        soil["moisture_status"] = soil_moisture
    if soil:
        payload["soil"] = soil

    climate = {}
    if rainfall > 0:
        climate["rainfall_mm"] = rainfall
    if temp != 0:
        climate["temp_c"] = temp
    if climate:
        payload["climate"] = climate

    biodiversity = {}
    if species_richness:
        biodiversity["species_richness"] = species_richness
    if habitat_diversity:
        biodiversity["habitat_diversity"] = habitat_diversity
    if biodiversity:
        payload["biodiversity"] = biodiversity

    return payload


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
    with st.chat_message("assistant"):
        with st.spinner("Analyzing environmental data and retrieving scientific evidence..."):
            try:
                r = requests.post(f"{API_URL}/api/chat", json=payload, timeout=TIMEOUT)
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

                if show_reasoning and data.get("reasoning_trace"):
                    with st.expander("🧠 Reasoning trace (scientific thinking)"):
                        st.text(data["reasoning_trace"])

                st.session_state.messages.append({
                    "role": "assistant",
                    "content": data.get("response", ""),
                    "recommendations": recommendations,
                    "follow_ups": follow_ups,
                })
                st.session_state.last_result = data

            except requests.exceptions.ConnectionError:
                st.error(
                    "❌ Cannot reach the API. Is uvicorn running?\n\n"
                    "Open another terminal and run: `uvicorn app.main:app --reload --port 8000`"
                )
            except requests.exceptions.Timeout:
                st.error("⏱️ Request timed out. The reasoning engine can take 1–2 minutes.")
            except Exception as e:
                st.error(f"❌ Error: {type(e).__name__}: {e}")