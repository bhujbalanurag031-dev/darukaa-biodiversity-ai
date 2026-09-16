"""
RAG ingestion pipeline.
Loads PDFs -> splits into chunks -> embeds -> stores in ChromaDB.
"""
import os
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from app.rag.vector_store import get_vector_store
from app.config import settings


DOCS_DIR = "data/raw"


def load_documents(directory: str = DOCS_DIR):
    """Load all PDF and text files from a directory."""
    if not os.path.exists(directory):
        raise FileNotFoundError(f"Directory not found: {directory}")

    documents = []
    files = [f for f in os.listdir(directory) if f.endswith((".pdf", ".txt", ".md"))]

    if not files:
        raise ValueError(f"No PDF/txt/md files found in {directory}")

    for filename in files:
        filepath = os.path.join(directory, filename)
        print(f"  Loading: {filename}")

        try:
            if filename.endswith(".pdf"):
                loader = PyPDFLoader(filepath)
            else:
                loader = TextLoader(filepath, encoding="utf-8")

            docs = loader.load()

            for doc in docs:
                doc.metadata["source_file"] = filename
                doc.metadata["source_type"] = "pdf" if filename.endswith(".pdf") else "text"

            documents.extend(docs)
            print(f"    → {len(docs)} pages loaded")

        except Exception as e:
            print(f"    ✗ Failed to load {filename}: {e}")
            continue

    print(f"\nTotal pages loaded: {len(documents)}")
    return documents


def chunk_documents(documents):
    """Split documents into overlapping chunks."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )
    chunks = splitter.split_documents(documents)
    print(f"Total chunks created: {len(chunks)}")
    return chunks


def ingest_to_vector_store(chunks, batch_size: int = 100):
    """Embed and store chunks in ChromaDB in batches."""
    vector_store = get_vector_store()
    total = len(chunks)

    for i in range(0, total, batch_size):
        batch = chunks[i : i + batch_size]
        vector_store.add_documents(batch)
        print(f"  Ingested batch {i + len(batch)}/{total}")

    vector_store.persist()
    print(f"\n✓ Ingested {total} chunks into vector store")
    print(f"  Location: {settings.CHROMA_PERSIST_DIR}")


def run_ingestion():
    print("=" * 60)
    print("RAG Ingestion Pipeline")
    print("=" * 60)

    print("\n[1/3] Loading documents...")
    documents = load_documents()

    print("\n[2/3] Chunking documents...")
    chunks = chunk_documents(documents)

    print("\n[3/3] Embedding and storing in vector DB...")
    ingest_to_vector_store(chunks)

    print("\n" + "=" * 60)
    print("Ingestion complete.")
    print("=" * 60)


if __name__ == "__main__":
    run_ingestion()