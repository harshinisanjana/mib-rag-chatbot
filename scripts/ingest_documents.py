"""
Standalone ingestion script.

Usage:
    cd backend
    python -m scripts.ingest_documents

Or from project root:
    python scripts/ingest_documents.py
"""
import sys
import os
import logging

# Add backend to path so imports work
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from app.ingestion.ingest import ingest_documents


def main():
    print("=" * 60)
    print("MIB RAG Chatbot — Document Ingestion")
    print("=" * 60)

    try:
        result = ingest_documents(clear_existing=True)
    except Exception as e:
        print(f"\n❌ Ingestion failed: {e}")
        sys.exit(1)

    print(f"\n{'=' * 60}")
    print(f"Documents processed: {result['documents_processed']}")
    print(f"Total chunks created: {result['total_chunks']}")
    print()

    for detail in result["details"]:
        status_icon = "[OK]" if detail["status"] == "success" else "[FAIL]"
        print(f"  {status_icon} {detail['document']}: {detail['status']}", end="")
        if "chunks" in detail:
            print(f" ({detail['chunks']} chunks)", end="")
        if "error" in detail:
            print(f" — {detail['error']}", end="")
        print()

    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
