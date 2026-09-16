"""
Provider-agnostic LLM client.
Works with Groq (free) or OpenAI (paid).
Captures reasoning trace when available.
"""
from typing import Optional, Dict, Any
from groq import Groq
from openai import OpenAI
from app.config import settings


class LLMClient:
    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()

        if self.provider == "groq":
            self.client = Groq(api_key=settings.GROQ_API_KEY)
            self.model = settings.GROQ_MODEL
        elif self.provider == "openai":
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "gpt-4o-mini"
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER: {self.provider}")

    def chat(
        self,
        system_prompt: str,
        user_message: str,
        max_tokens: int = 1500,
        temperature: float = 0.3,
        json_mode: bool = False,
    ) -> Dict[str, Any]:
        """
        Send a chat request. Returns dict with:
        - content: the model's answer
        - reasoning: the model's internal reasoning (if available)
        - model: model id used
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        kwargs: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            response = self.client.chat.completions.create(**kwargs)
        except Exception as e:
            # Fallback: retry without JSON mode if the provider rejected it
            if json_mode and "json_validate_failed" in str(e):
                print("[llm_client] JSON mode failed, retrying without response_format...")
                kwargs.pop("response_format", None)
                kwargs["messages"][-1]["content"] = (
                    kwargs["messages"][-1]["content"]
                    + "\n\nIMPORTANT: Return ONLY the raw JSON object. "
                    "Do not wrap in markdown fences. Do not add commentary."
                )
                response = self.client.chat.completions.create(**kwargs)
            else:
                raise

        message = response.choices[0].message
        reasoning = getattr(message, "reasoning", None)

        return {
            "content": message.content or "",
            "reasoning": reasoning,
            "model": response.model,
            "usage": response.usage.total_tokens if response.usage else None,
        }


_llm_instance: Optional[LLMClient] = None


def get_llm() -> LLMClient:
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = LLMClient()
    return _llm_instance