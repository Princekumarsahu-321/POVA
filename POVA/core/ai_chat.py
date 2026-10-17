"""Local Ollama chat client; prompts never leave the configured loopback host."""

from __future__ import annotations

import json
import re
from typing import TypedDict
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from config.settings import Settings


class ChatMessage(TypedDict):
    role: str
    content: str


class ChatError(RuntimeError):
    """A recoverable local AI chat failure."""


_GREETINGS = {
    "good afternoon",
    "good evening",
    "good morning",
    "hello",
    "hey",
    "hi",
    "hii",
    "hiii",
}


class OllamaChatClient:
    def __init__(self, settings: Settings):
        settings.validate()
        self.endpoint = settings.ai_endpoint.rstrip("/")
        self.model = settings.ai_model.strip()

    def reply(self, messages: list[ChatMessage]) -> str:
        if not messages or any(
            not isinstance(message, dict)
            or message.get("role") not in {"user", "assistant"}
            or not isinstance(message.get("content"), str)
            for message in messages
        ):
            raise ChatError("Chat messages must contain user or assistant text.")
        latest = messages[-1]
        if latest["role"] == "user":
            greeting = re.sub(r"[.!?,]+$", "", latest["content"].strip().lower())
            if greeting in _GREETINGS:
                return "Hii Sir! How can I help you today?"

        body = json.dumps({
            "model": self.model,
            "messages": messages,
            "stream": False,
        }).encode("utf-8")
        request = Request(
            f"{self.endpoint}/api/chat",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=120) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                raise ChatError(
                    f"Ollama could not find model '{self.model}'. Pull it with `ollama pull {self.model}`."
                ) from exc
            raise ChatError(f"Ollama returned HTTP {exc.code}.") from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise ChatError(
                "Could not reach Ollama. Start Ollama and verify the local endpoint in Settings."
            ) from exc
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ChatError("Ollama returned an invalid response.") from exc

        try:
            message = payload["message"]
            content = message["content"]
        except (KeyError, TypeError) as exc:
            raise ChatError("Ollama returned an unexpected response.") from exc
        if not isinstance(content, str) or not content.strip():
            raise ChatError("Ollama returned an empty response.")
        return content.strip()
