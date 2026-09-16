"""
ChromaDB vector store with local embeddings.
Uses sentence-transformers for free, local embedding generation.
"""
import os
os.environ["ANONYMIZED_TELEMETRY"] = "False"


from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import settings


_embeddings_instance = None
_vector_store_instance = None


def get_embeddings():
    """Lazy-load the embedding model (downloads once, ~80MB)."""
    global _embeddings_instance
    if _embeddings_instance is None:
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL}...")
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": "cpu"},
            encode_kwargs={"normalize_embeddings": True},
        )
        print("Embedding model ready.")
    return _embeddings_instance


def get_vector_store():
    """Lazy-load the ChromaDB vector store."""
    global _vector_store_instance
    if _vector_store_instance is None:
        _vector_store_instance = Chroma(
            persist_directory=settings.CHROMA_PERSIST_DIR,
            embedding_function=get_embeddings(),
            collection_name="environmental_knowledge",
        )
    return _vector_store_instance