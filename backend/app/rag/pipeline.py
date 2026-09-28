import logging
from dataclasses import dataclass

from llama_index.core import Settings as LlamaSettings, VectorStoreIndex, StorageContext
from llama_index.core.schema import TextNode
from llama_index.core.postprocessor import SimilarityPostprocessor
from llama_index.llms.ollama import Ollama
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore

from app.core.config import settings
from app.services.vector_store_service import VectorStoreService
from app.services.conversation_service import conversation_service, Session
from app.rag.prompts import SYSTEM_PROMPT, QUERY_PROMPT_TEMPLATE, CONVERSATION_HISTORY_PREFIX

logger = logging.getLogger(__name__)


@dataclass
class RAGResult:
    answer: str
    grounded: bool
    sources: list[dict]
    session_id: str


class RAGPipeline:
    """LlamaIndex-based RAG pipeline using ChromaDB + Ollama."""

    _instance = None
    _initialized = False

    @classmethod
    def get_instance(cls) -> "RAGPipeline":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        if not RAGPipeline._initialized:
            self._setup_llama_index()
            RAGPipeline._initialized = True

    def _setup_llama_index(self):
        """Configure LlamaIndex with Ollama LLM and HuggingFace embeddings."""
        logger.info("Initializing LlamaIndex with Ollama model '%s'", settings.llm_model)

        self._llm = Ollama(
            model=settings.llm_model,
            base_url=settings.ollama_base_url,
            temperature=settings.llm_temperature,
            request_timeout=settings.llm_request_timeout,
            context_window=settings.llm_context_window,
            additional_kwargs={"num_ctx": settings.llm_context_window},
            system_prompt=SYSTEM_PROMPT,
        )

        self._embed_model = HuggingFaceEmbedding(
            model_name=settings.embedding_model,
        )

        # Set as global LlamaIndex defaults
        LlamaSettings.llm = self._llm
        LlamaSettings.embed_model = self._embed_model

        logger.info("LlamaIndex initialized successfully")

    def _get_query_engine(self):
        """Build a query engine backed by the ChromaDB collection with top_k and similarity filtering."""
        chroma_collection = VectorStoreService.get_collection()
        vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
        storage_context = StorageContext.from_defaults(vector_store=vector_store)

        index = VectorStoreIndex.from_vector_store(
            vector_store=vector_store,
            storage_context=storage_context,
            embed_model=self._embed_model,
        )

        node_postprocessors = []
        if settings.similarity_threshold > 0:
            node_postprocessors.append(
                SimilarityPostprocessor(similarity_cutoff=settings.similarity_threshold)
            )

        return index.as_query_engine(
            similarity_top_k=settings.top_k,
            node_postprocessors=node_postprocessors,
            llm=self._llm,
        )

    def query(
        self,
        question: str,
        session_id: str | None = None,
    ) -> RAGResult:
        question = question.strip()
        if not question:
            raise ValueError("Question cannot be empty")

        # Check if ChromaDB has any documents
        doc_count = VectorStoreService.count()
        if doc_count == 0:
            return RAGResult(
                answer="No documents have been indexed yet. Please run the ingestion process first.",
                grounded=False,
                sources=[],
                session_id=session_id or "",
            )

        # Manage conversation session
        session = conversation_service.get_or_create_session(session_id)
        session.add_user_message(question)

        # Build the augmented query with conversation context
        augmented_query = self._build_augmented_query(question, session)

        try:
            query_engine = self._get_query_engine()
            response = query_engine.query(augmented_query)

            answer = str(response).strip()
            sources = self._extract_sources(response)
            grounded = len(sources) > 0 and not self._is_no_info_response(answer)

            session.add_assistant_message(answer)

            return RAGResult(
                answer=answer,
                grounded=grounded,
                sources=sources,
                session_id=session.session_id,
            )

        except Exception as e:
            logger.exception("RAG query failed")
            # Remove the user message we added since we failed
            if session.history and session.history[-1].role == "user":
                session.history.pop()
            raise RuntimeError(f"RAG pipeline error: {e}") from e

    def _build_augmented_query(self, question: str, session: Session) -> str:
        """Prepend conversation history to help resolve follow-up references."""
        history_summary = session.get_context_summary()
        if history_summary:
            return f"Previous conversation:\n{history_summary}\n\nCurrent question: {question}"
        return question

    def _extract_sources(self, response) -> list[dict]:
        """Pull source metadata from LlamaIndex response."""
        sources = []
        seen = set()

        if not hasattr(response, "source_nodes"):
            return sources

        for node in response.source_nodes:
            metadata = node.node.metadata if hasattr(node.node, "metadata") else {}
            doc_name = metadata.get("source_document", "Unknown")
            chunk_idx = metadata.get("chunk_index", 0)
            key = f"{doc_name}:{chunk_idx}"

            if key in seen:
                continue
            seen.add(key)

            content = node.node.text if hasattr(node.node, "text") else ""
            sources.append({
                "document_name": doc_name,
                "page": metadata.get("page"),
                "chunk_index": chunk_idx,
                "similarity_score": round(node.score if node.score else 0.0, 4),
                "content_preview": content[:200] + "..." if len(content) > 200 else content,
            })

        return sources

    def _is_no_info_response(self, answer: str) -> bool:
        """Detect if the LLM indicated it couldn't find the information."""
        no_info_phrases = [
            "couldn't find",
            "could not find",
            "not available in",
            "no information",
            "not mentioned",
            "does not contain",
            "not found in",
            "don't have enough information",
        ]
        answer_lower = answer.lower()
        return any(phrase in answer_lower for phrase in no_info_phrases)

    @classmethod
    def reset(cls):
        """Reset the singleton (for testing)."""
        cls._instance = None
        cls._initialized = False
