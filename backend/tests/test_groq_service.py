from types import SimpleNamespace

import pytest

from app.services.groq_service import GroqService


class FakeCompletions:
    def __init__(self, content):
        self.content = content
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=self.content))]
        )


class FakeClient:
    def __init__(self, content="Answer from context"):
        self.chat = SimpleNamespace(completions=FakeCompletions(content))


def test_groq_service_sends_grounded_prompt_and_model_settings():
    client = FakeClient()
    service = GroqService(client)

    answer = service.generate_answer("Where is the reset link?", ["Source 1: Use Settings."])

    call = client.chat.completions.calls[0]
    assert answer == "Answer from context"
    assert call["model"] == "openai/gpt-oss-20b"
    assert call["temperature"] == 0.0
    assert "Use Settings" in call["messages"][1]["content"]


def test_groq_service_rejects_empty_context():
    with pytest.raises(ValueError, match="context cannot be empty"):
        GroqService(FakeClient()).generate_answer("Question", [])


def test_groq_service_rejects_empty_response():
    with pytest.raises(RuntimeError, match="empty answer"):
        GroqService(FakeClient(content=" ")).generate_answer("Question", ["Context"])