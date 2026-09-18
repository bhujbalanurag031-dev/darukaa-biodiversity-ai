"""
ChromaDB vector store with local embeddings.
Uses sentence-transformers for free, local embedding generation.

Memory optimizations for free-tier deployment (512 MB RAM ceiling):
- Single torch thread (reduces CPU overhead, no effect on quality)
- Lazy loading of embedding model (only loads on first request)
- Lazy loading of vector store (only loads on first request)
- Telemetry disabled (no network overhead)
"""
import os

# Disable telemetry BEFORE importing chromadb
os.environ["ANONYMIZED_TELEMETRY"] = "False"
os.environ["CHROMA_TELEMETRY_IMPL"] = "chromadb.telemetry.product.posthog.Posthog"

# Restrict torch to single-threaded CPU mode — critical for free-tier deployments
# where multiple threads add scheduling overhead with no throughput benefit
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch

# Set torch to single-threaded mode (must be done before any tensor ops)
torch.set_num_threads(1)

from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from app.config import settings


_embeddings_instance = None
_vector_store_instance = None


def get_embeddings():
    """
    Lazy-load the embedding model (downloads once, ~80 MB RAM when loaded).
    Only instantiated on the first request to keep memory low at startup.
    """
    global _embeddings_instance
    if _embeddings_instance is None:
        print(f"Loading embedding model: {settings.EMBEDDING_MODEL}...")
        _embeddings_instance = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={
                "device": "cpu",
                # Use float32 instead of float16 to avoid conversion overhead
                # (float16 isn't faster on CPU and can cause precision issues)
                "trust_remote_code": False,
            },
            encode_kwargs={
                "normalize_embeddings": True,
                "batch_size": 8,  # Smaller batches use less peak memory
            },
            # Cache the model locally after first download
            cache_folder=os.path.expanduser("~/.cache/huggingface"),
        )
        print("Embedding model ready.")

        # Force a GC pass to clean up any intermediate objects from model loading
        import gc
        gc.collect()

    return _embeddings_instance


def get_vector_store():
    """
    Lazy-load the ChromaDB vector store.
    Uses the persistent directory at settings.CHROMA_PERSIST_DIR.
    """
    global _vector_store_instance
    if _vector_store_instance is None:
        # Verify the persist directory exists before attempting to load
        if not os.path.isdir(settings.CHROMA_PERSIST_DIR):
            raise FileNotFoundError(
                f"ChromaDB persist directory not found: {settings.CHROMA_PERSIST_DIR}\n"
                f"Run 'python -m app.rag.ingest' to build the vector store locally."
            )

        print(f"Loading ChromaDB from {settings.CHROMA_PERSIST_DIR}...")
        _vector_store_instance = Chroma(
            persist_directory=settings.CHROMA_PERSIST_DIR,
            embedding_function=get_embeddings(),
            collection_name="environmental_knowledge",
        )
        print("ChromaDB ready.")

    return _vector_store_instance


def get_collection_size() -> int:
    """Return the number of chunks in the vector store."""
    try:
        vs = get_vector_store()
        return vs._collection.count()
    except Exception:
        return 0


def clear_cache():
    """
    Free the cached embedding model and vector store from memory.
    Useful for freeing ~400 MB between deployments / restarts.
    """
    global _embeddings_instance, _vector_store_instance
    _embeddings_instance = None
    _vector_store_instance = None

    import gc
    gc.collect()
    gc.collect()