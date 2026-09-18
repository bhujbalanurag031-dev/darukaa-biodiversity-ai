"""
Central configuration for the Darukaa.Earth Biodiversity AI.

All settings are read from environment variables so the same code
runs locally and on any cloud platform.

Memory-related defaults are tuned for free-tier deployment
(0.1 CPU, 512 MB RAM) — see comments for the reasoning.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ---------- LLM Provider ----------
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # ---------- Database ----------
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./darukaa.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    # ---------- Vector store ----------
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # ---------- RAG settings ----------
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

    # Reduced from 5 -> 3 for free-tier deployment:
    # Each retrieved chunk consumes ~2 KB of context plus embedding compute.
    # 3 chunks still provides sufficient grounding (tested with our indexed
    # IPCC/FAO/IPBES corpus) while cutting the memory footprint of the
    # retrieval + prompt construction stages by ~40%.
    # Override via env var TOP_K_RETRIEVAL if running locally with more RAM.
    TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "3"))

    # ---------- LLM token limits ----------
    # gpt-oss-20b is a reasoning model. It produces a "reasoning" trace
    # before the final answer. 4000 tokens is enough to complete both
    # stages for our longest prompts.
    MAX_TOKENS_REASONING = int(os.getenv("MAX_TOKENS_REASONING", "4000"))

    # For shorter, non-reasoning interactions (not currently used in the
    # main pipeline, but available for future endpoints).
    MAX_TOKENS_CHAT = int(os.getenv("MAX_TOKENS_CHAT", "500"))

    # ---------- Runtime flags ----------
    # Enable debug output of the request payload in logs (off by default).
    DEBUG_PAYLOAD = os.getenv("DEBUG_PAYLOAD", "false").lower() == "true"


settings = Settings()