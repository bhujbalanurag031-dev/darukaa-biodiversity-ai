"""
Retriever for the RAG pipeline.
Uses ChromaDB vector similarity search with citation metadata.
"""
from typing import List, Dict, Any
from app.rag.vector_store import get_vector_store
from app.config import settings


def retrieve_with_metadata(query: str, k: int = None) -> List[Dict[str, Any]]:
    """
    Retrieve relevant document chunks for a query.
    Returns a list of dicts with content, source, page, and relevance score.
    """
    if k is None:
        k = settings.TOP_K_RETRIEVAL

    vector_store = get_vector_store()
    results = vector_store.similarity_search_with_score(query, k=k)

    retrieved = []
    for doc, score in results:
        retrieved.append({
            "content": doc.page_content,
            "source": doc.metadata.get("source_file", "unknown"),
            "page": doc.metadata.get("page", None),
            "relevance_score": round(float(score), 4),
        })

    return retrieved


def format_context(retrieved: List[Dict[str, Any]]) -> str:
    """
    Format retrieved chunks into a context string for the LLM.
    Includes source citations so the LLM can cite them.
    """
    if not retrieved:
        return "No relevant context found in the knowledge base."

    parts = []
    for i, r in enumerate(retrieved, 1):
        source_info = f"{r['source']}"
        if r.get("page") is not None:
            source_info += f", page {r['page']}"

        parts.append(
            f"[Document {i}: {source_info}]\n{r['content']}"
        )

    return "\n\n---\n\n".join(parts)


# ---------- Self-test ----------
if __name__ == "__main__":
    test_queries = [
        "How do legume cover crops affect soil organic carbon?",
        "What is the relationship between biodiversity and soil health?",
        "How does land use change impact habitat fragmentation?",
    ]

    for q in test_queries:
        print(f"\n{'=' * 60}")
        print(f"Query: {q}")
        print('=' * 60)

        results = retrieve_with_metadata(q, k=3)
        if not results:
            print("  No results (did you run ingestion?)")
            continue

        for i, r in enumerate(results, 1):
            preview = r["content"][:200].replace("\n", " ")
            print(f"\n  [{i}] {r['source']} (score: {r['relevance_score']})")
            print(f"      {preview}...")