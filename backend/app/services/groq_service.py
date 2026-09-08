from collections.abc import Sequence

from app.core.config import settings


class GroqService:
    def __init__(self, client=None):
        self._client = client

    def _get_client(self):
        if self._client is None:
            if not settings.groq_api_key:
                raise RuntimeError("GROQ_API_KEY is not configured")
            try:
                from groq import Groq
            except ImportError as exc:
                raise RuntimeError("groq is required for answer generation") from exc
            self._client = Groq(api_key=settings.groq_api_key)
        return self._client

    def generate_answer(self, question: str, context: Sequence[str]) -> str:
        if not context:
            raise ValueError("context cannot be empty")
        response = self._get_client().chat.completions.create(
            model=settings.groq_model,
            temperature=settings.groq_temperature,
            max_tokens=settings.groq_max_tokens,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a customer support assistant. Answer only from the provided "
                        "context. If the context does not contain the answer, say that you "
                        "do not have enough information and recommend human support. Do not "
                        "invent policies, steps, prices, or capabilities."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Context:\n\n{chr(10).join(context)}\n\nQuestion: {question}",
                },
            ],
        )
        answer = response.choices[0].message.content
        if not answer or not answer.strip():
            raise RuntimeError("Groq returned an empty answer")
        return answer.strip()