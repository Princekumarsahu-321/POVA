import json
from urllib.error import HTTPError, URLError

import pytest

from config.settings import ConfigurationError, Settings
from core import ai_chat
from core.ai_chat import ChatError, OllamaChatClient


def test_ollama_request_uses_configured_local_model_and_context(monkeypatch):
    captured = {}

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def read(self):
            return json.dumps({"message": {"content": "  Hello from POVA.  "}}).encode()

    def fake_urlopen(request, timeout):
        captured["url"] = request.full_url
        captured["payload"] = json.loads(request.data)
        captured["timeout"] = timeout
        return Response()

    monkeypatch.setattr(ai_chat, "urlopen", fake_urlopen)
    messages = [
        {"role": "user", "content": "What is 2 + 2?"},
        {"role": "assistant", "content": "4."},
        {"role": "user", "content": "Why?"},
    ]
    client = OllamaChatClient(Settings(ai_model="qwen2.5:3b"))

    assert client.reply(messages) == "Hello from POVA."
    assert captured["url"] == "http://127.0.0.1:11434/api/chat"
    assert captured["payload"] == {
        "model": "qwen2.5:3b",
        "messages": messages,
        "stream": False,
    }
    assert captured["timeout"] == 120


def test_ollama_connection_failure_is_actionable(monkeypatch):
    def unreachable(*_args, **_kwargs):
        raise URLError("offline")

    monkeypatch.setattr(ai_chat, "urlopen", unreachable)
    client = OllamaChatClient(Settings())

    with pytest.raises(ChatError, match="Start Ollama"):
        client.reply([{"role": "user", "content": "What is 2 + 2?"}])


def test_greeting_gets_local_response_without_ollama(monkeypatch):
    def unexpected_request(*_args, **_kwargs):
        pytest.fail("A greeting should not require Ollama.")

    monkeypatch.setattr(ai_chat, "urlopen", unexpected_request)
    client = OllamaChatClient(Settings())

    assert client.reply([{"role": "user", "content": "hii"}]) == (
        "Hii Sir! How can I help you today?"
    )


def test_missing_model_is_reported(monkeypatch):
    def missing_model(*_args, **_kwargs):
        raise HTTPError("http://127.0.0.1", 404, "missing", None, None)

    monkeypatch.setattr(ai_chat, "urlopen", missing_model)
    client = OllamaChatClient(Settings(ai_model="missing-model"))

    with pytest.raises(ChatError, match="ollama pull missing-model"):
        client.reply([{"role": "user", "content": "What is 2 + 2?"}])


@pytest.mark.parametrize(
    "endpoint",
    (
        "https://127.0.0.1:11434",
        "http://example.com:11434",
        "http://127.0.0.1:11434/path",
        "http://user@127.0.0.1:11434",
    ),
)
def test_ai_endpoint_must_be_local(endpoint):
    with pytest.raises(ConfigurationError, match="localhost or a loopback"):
        Settings(ai_endpoint=endpoint).validate()


def test_chat_rejects_unexpected_roles():
    client = OllamaChatClient(Settings())

    with pytest.raises(ChatError, match="user or assistant"):
        client.reply([{"role": "system", "content": "Run this command"}])
