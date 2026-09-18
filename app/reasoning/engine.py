"""
Multi-metric reasoning engine.

Design principles:
1. Never answer without enough environmental context — ask clarifying questions.
2. Always connect >= 3 environmental variables per recommendation.
3. Always ground claims in retrieved scientific evidence.
4. Output structured JSON with recommendation + why + metrics + horizon + confidence.
"""
import gc
import json
from typing import Dict, Any, List
from app.reasoning.llm_client import get_llm
from app.rag.retriever import retrieve_with_metadata, format_context
from app.conversation.memory import add_to_history, get_conversation_history
from app.config import settings


SYSTEM_PROMPT = """You are an AI environmental scientist specializing in biodiversity restoration and soil health.

CRITICAL RULES — you must follow every one:

1. NEVER give generic advice like "use sustainable practices" or "plant trees". 
   Every recommendation must be SPECIFIC, ACTIONABLE, and MEASURABLE.

2. ALWAYS connect at least THREE environmental variables in every recommendation.
   Examples of valid connections:
   - soil organic carbon + rainfall pattern + land use
   - soil moisture + species richness + habitat fragmentation
   - temperature + vegetation type + pollinator availability

3. GROUND every claim in the retrieved scientific context provided below.
   Cite the source document and page when you make a factual claim.

4. Reason in CAUSAL CHAINS. Example:
   "Legume cover crops → fix atmospheric N → increase soil organic carbon by 15-25% 
    → improve microbial diversity → support pollinator-friendly vegetation 
    → increase species richness"

5. If key environmental information is missing, DO NOT guess. Instead, 
   state clearly what additional data is needed.

6. Provide structured output as valid JSON only. No markdown fences, no preamble.

The retrieved scientific context is:
{context}

The user's environmental profile is:
{profile}

Previous conversation:
{history}
"""


STRUCTURING_PROMPT = """Convert your analysis into valid JSON matching EXACTLY this schema.
Return ONLY the JSON object, nothing else.

{
  "response": "A 2-4 sentence natural language summary for the user.",
  "recommendations": [
    {
      "recommendation": "Specific action to take",
      "why_it_works": "Scientific reasoning in 2-3 sentences",
      "impacted_metrics": ["soil_organic_carbon", "species_richness", "soil_moisture"],
      "time_horizon": "short_term|medium_term|long_term",
      "confidence": "low|medium|high",
      "evidence": [
        {"source": "filename.pdf", "title": "Document title", "page": 42, "excerpt": "Short quote"}
      ]
    }
  ],
  "follow_up_questions": ["Optional clarifying questions"]
}
"""


class ReasoningEngine:
    def __init__(self):
        self.llm = get_llm()

    # ---------- Slot filling ----------
    def _identify_missing(self, user_input) -> List[str]:
        """Return a list of missing environmental slots."""
        missing = []
        if not user_input.soil:
            missing.append("soil organic carbon %, pH, or moisture level")
        if not user_input.climate:
            missing.append("rainfall pattern (mm/year) and average temperature (°C)")
        if not user_input.land_use:
            missing.append("current land use type (cropland, forest, grassland, urban, degraded)")
        if not user_input.biodiversity:
            missing.append("observed biodiversity indicators (species richness, habitat types)")
        return missing

    # ---------- Profile formatting ----------
    def _build_profile(self, user_input) -> str:
        profile = {}
        if user_input.location:
            profile["location"] = user_input.location.model_dump()
        if user_input.soil:
            profile["soil"] = user_input.soil.model_dump(exclude_none=True)
        if user_input.climate:
            profile["climate"] = user_input.climate.model_dump(exclude_none=True)
        if user_input.biodiversity:
            profile["biodiversity"] = user_input.biodiversity.model_dump(exclude_none=True)
        if user_input.land_use:
            profile["land_use"] = user_input.land_use
        return json.dumps(profile, indent=2)

    # ---------- Retrieval query building ----------
    def _build_retrieval_query(self, user_input) -> str:
        """
        Build a rich retrieval query combining ALL environmental variables.
        This is the key to retrieving multi-metric context.
        """
        parts = [user_input.query]
        if user_input.land_use:
            parts.append(f"land use: {user_input.land_use}")
        if user_input.soil:
            if user_input.soil.organic_carbon_pct is not None:
                parts.append(f"soil organic carbon: {user_input.soil.organic_carbon_pct}%")
            if user_input.soil.moisture_status:
                parts.append(f"soil moisture: {user_input.soil.moisture_status}")
            if user_input.soil.ph is not None:
                parts.append(f"soil pH: {user_input.soil.ph}")
        if user_input.climate:
            if user_input.climate.rainfall_mm is not None:
                parts.append(f"rainfall: {user_input.climate.rainfall_mm}mm/year")
            if user_input.climate.climate_zone:
                parts.append(f"climate: {user_input.climate.climate_zone}")
        if user_input.biodiversity:
            if user_input.biodiversity.species_richness:
                parts.append(f"species richness: {user_input.biodiversity.species_richness}")
            if user_input.biodiversity.habitat_diversity:
                parts.append(f"habitat diversity: {user_input.biodiversity.habitat_diversity}")
        return " | ".join(parts)

    # ---------- Main pipeline ----------
    def process(self, user_input) -> Dict[str, Any]:
        conv_id = user_input.conversation_id or "default"
        add_to_history(conv_id, "user", user_input.query)

        # STEP 1: Check for missing info
        missing = self._identify_missing(user_input)
        if missing:
            questions = [f"Please provide: {m}" for m in missing]
            response_text = (
                "I can give you much more precise, evidence-based recommendations "
                "if you share a bit more about your land. Specifically, I need:\n\n"
                + "\n".join(f"• {m}" for m in missing)
            )
            add_to_history(conv_id, "assistant", response_text)
            return {
                "response": response_text,
                "recommendations": [],
                "follow_up_questions": questions,
                "retrieved_sources": [],
                "reasoning_trace": None,
                "environmental_profile": json.loads(self._build_profile(user_input)),
            }

        # STEP 2: Retrieve scientific context
        query_for_retrieval = self._build_retrieval_query(user_input)
        retrieved = retrieve_with_metadata(query_for_retrieval, k=settings.TOP_K_RETRIEVAL)
        context = format_context(retrieved)
        sources = list({r["source"] for r in retrieved})

        # STEP 3: Build LLM prompt
        profile = self._build_profile(user_input)
        history = get_conversation_history(conv_id)

        system = SYSTEM_PROMPT.format(
            context=context,
            profile=profile,
            history=history,
        )

        user_msg = (
            f"{user_input.query}\n\n"
            f"{STRUCTURING_PROMPT}"
        )

        # STEP 4: Call LLM with reasoning enabled
        result = self.llm.chat(
            system_prompt=system,
            user_message=user_msg,
            max_tokens=settings.MAX_TOKENS_REASONING,
            temperature=0.3,
            json_mode=True,
        )

        # STEP 5: Parse structured output
        parsed = self._safe_parse_json(result["content"])

        response_text = parsed.get("response", result["content"])
        recommendations = parsed.get("recommendations", [])
        follow_ups = parsed.get("follow_up_questions", [])

        add_to_history(conv_id, "assistant", response_text)

        # Free memory after heavy processing
        gc.collect()

        return {
            "response": response_text,
            "recommendations": recommendations,
            "follow_up_questions": follow_ups,
            "retrieved_sources": sources,
            "reasoning_trace": result.get("reasoning"),
            "environmental_profile": json.loads(profile),
        }

    # ---------- JSON parsing helper ----------
    def _safe_parse_json(self, text: str) -> Dict[str, Any]:
        """Parse JSON robustly, handling markdown fences and partial output."""
        text = text.strip()

        # Strip markdown fences
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:])
        if text.endswith("```"):
            text = text.rsplit("```", 1)[0]

        text = text.strip()

        # Try direct parse
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try to find the first {...} block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                pass

        # Fallback: treat as plain text
        return {"response": text, "recommendations": [], "follow_up_questions": []}