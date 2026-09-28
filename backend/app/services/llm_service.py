import logging
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Interface to the local Ollama LLM."""

    @staticmethod
    def check_health() -> bool:
        """Check if Ollama is reachable and the model is available."""
        try:
            response = httpx.get(
                f"{settings.ollama_base_url}/api/tags",
                timeout=5.0,
            )
            if response.status_code == 200:
                models = response.json().get("models", [])
                target = settings.llm_model.lower()
                return any(target in m.get("name", "").lower() or m.get("name", "").lower().startswith(target.split(":")[0]) for m in models)
            return False
        except Exception:
            return False

    @staticmethod
    def get_available_models() -> list[str]:
        """List models available in Ollama."""
        try:
            response = httpx.get(
                f"{settings.ollama_base_url}/api/tags",
                timeout=5.0,
            )
            if response.status_code == 200:
                return [m["name"] for m in response.json().get("models", [])]
        except Exception:
            pass
        return []
