import logging
from pathlib import Path

from app.core.config import settings
from app.services.text_extraction_service import TextExtractionService, TextExtractionError
from app.services.text_cleaning_service import clean_text
from app.services.chunking_service import ChunkingService
from app.services.embedding_service import EmbeddingService
from app.services.vector_store_service import VectorStoreService

logger = logging.getLogger(__name__)


def ingest_documents(clear_existing: bool = True) -> dict:
    """
    Process all documents in the documents directory and store them in ChromaDB.

    Returns a summary dict with processing results.
    """
    documents_dir = settings.get_documents_path()
    if not documents_dir.exists():
        raise FileNotFoundError(f"Documents directory not found: {documents_dir}")

    # Find all supported documents
    supported_extensions = {".pdf", ".docx", ".txt", ".md"}
    doc_files = [
        f for f in documents_dir.iterdir()
        if f.is_file() and f.suffix.lower() in supported_extensions
    ]

    if not doc_files:
        logger.warning("No documents found in %s", documents_dir)
        return {"documents_processed": 0, "total_chunks": 0, "details": []}

    logger.info("Found %d documents to process", len(doc_files))

    if clear_existing:
        logger.info("Clearing existing ChromaDB collection")
        VectorStoreService.clear_collection()

    chunker = ChunkingService(settings.chunk_size, settings.chunk_overlap)
    embedding_service = EmbeddingService.get_instance()

    all_ids = []
    all_documents = []
    all_embeddings = []
    all_metadatas = []
    details = []
    total_chunks = 0

    for doc_file in doc_files:
        file_type = doc_file.suffix.lstrip(".").lower()
        doc_name = doc_file.name
        logger.info("Processing: %s", doc_name)

        try:
            # Extract text with page information
            pages = TextExtractionService.extract_pages(str(doc_file), file_type)

            if not pages:
                logger.warning("No content extracted from %s", doc_name)
                details.append({"document": doc_name, "status": "empty", "chunks": 0})
                continue

            # Clean and chunk each page
            doc_chunks = []
            for page in pages:
                cleaned = clean_text(page.content)
                if not cleaned:
                    continue

                page_meta = {"source_document": doc_name}
                if page.page_number is not None:
                    page_meta["page"] = page.page_number

                chunks = chunker.chunk_text(cleaned, metadata=page_meta)
                doc_chunks.extend(chunks)

            if not doc_chunks:
                logger.warning("No chunks produced from %s", doc_name)
                details.append({"document": doc_name, "status": "no_chunks", "chunks": 0})
                continue

            # Generate embeddings
            chunk_texts = [c.content for c in doc_chunks]
            embeddings = embedding_service.embed_texts(chunk_texts)

            # Prepare for ChromaDB insertion
            for idx, chunk in enumerate(doc_chunks):
                chunk_id = f"{doc_name}::chunk_{idx}"
                metadata = {
                    "source_document": doc_name,
                    "chunk_index": idx,
                }
                if "page" in chunk.metadata:
                    metadata["page"] = chunk.metadata["page"]

                all_ids.append(chunk_id)
                all_documents.append(chunk.content)
                all_embeddings.append(embeddings[idx])
                all_metadatas.append(metadata)

            total_chunks += len(doc_chunks)
            details.append({
                "document": doc_name,
                "status": "success",
                "chunks": len(doc_chunks),
                "pages": len(pages),
            })
            logger.info("  → %d chunks from %d pages", len(doc_chunks), len(pages))

        except TextExtractionError as e:
            logger.error("Failed to extract text from %s: %s", doc_name, e)
            details.append({"document": doc_name, "status": "extraction_error", "error": str(e)})
        except Exception as e:
            logger.error("Failed to process %s: %s", doc_name, e)
            details.append({"document": doc_name, "status": "error", "error": str(e)})

    # Batch insert into ChromaDB
    if all_ids:
        logger.info("Storing %d chunks in ChromaDB", len(all_ids))
        VectorStoreService.add_chunks(all_ids, all_documents, all_embeddings, all_metadatas)
        logger.info("Ingestion complete: %d documents, %d chunks", len(doc_files), total_chunks)
    else:
        logger.warning("No chunks to store")

    return {
        "documents_processed": len([d for d in details if d["status"] == "success"]),
        "total_chunks": total_chunks,
        "details": details,
    }
