import sys
import os

# Add project root to path so 'app' can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.rag.retriever import retrieve_with_metadata

results = retrieve_with_metadata("legume cover crops soil carbon", k=3)

print(f"Retrieved {len(results)} chunks\n")
for i, r in enumerate(results, 1):
    print(f"[{i}] {r['source']} (score: {r['relevance_score']})")
    print(f"    {r['content'][:200]}...")
    print()