import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # LLM Provider
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./darukaa.db")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Vector store
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

    # RAG settings
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
    TOP_K_RETRIEVAL = int(os.getenv("TOP_K_RETRIEVAL", "5"))

    # Model token limits
    MAX_TOKENS_REASONING = 4000 
    MAX_TOKENS_CHAT = 500


settings = Settings()