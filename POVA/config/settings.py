"""Validated, user-local settings persistence."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
import ipaddress
import json
import os
from pathlib import Path
import tempfile
from urllib.parse import urlsplit


class ConfigurationError(RuntimeError):
    """Raised when POVA settings cannot safely be loaded or saved."""


def default_settings_path() -> Path:
    base = Path(os.environ.get("APPDATA", Path.home() / ".config"))
    return base / "POVA" / "settings.json"


@dataclass
class Settings:
    voice_backend: str = "windows"
    microphone_device: str = "Default"
    recognition_timeout: int = 8
    phrase_duration: int = 5
    wake_word_enabled: bool = True
    wake_word: str = "pova"
    voice_response_enabled: bool = True
    speech_rate: int = 0
    command_history_enabled: bool = True
    auto_start_listening: bool = False
    ai_endpoint: str = "http://127.0.0.1:11434"
    ai_model: str = "llama3.2"
    screenshot_directory: str = str(Path(__file__).resolve().parents[1] / "screenshots")
    project_directory: str = str(Path(__file__).resolve().parents[1])

    def validate(self) -> None:
        if self.voice_backend != "windows":
            raise ConfigurationError("The selected voice backend is not available.")
        if self.microphone_device != "Default":
            raise ConfigurationError("POVA currently uses the Windows default microphone.")
        integer_values = {
            "recognition timeout": self.recognition_timeout,
            "phrase duration": self.phrase_duration,
            "speech rate": self.speech_rate,
        }
        if any(type(value) is not int for value in integer_values.values()):
            raise ConfigurationError("Timeouts and speech rate must be whole numbers.")
        boolean_values = (
            self.wake_word_enabled, self.voice_response_enabled,
            self.command_history_enabled, self.auto_start_listening,
        )
        if any(type(value) is not bool for value in boolean_values):
            raise ConfigurationError("Boolean settings must be true or false.")
        string_values = (
            self.microphone_device, self.wake_word, self.screenshot_directory,
            self.project_directory, self.ai_endpoint, self.ai_model,
        )
        if any(not isinstance(value, str) for value in string_values):
            raise ConfigurationError("Text settings must contain strings.")
        if not 2 <= self.recognition_timeout <= 30:
            raise ConfigurationError("Recognition timeout must be between 2 and 30 seconds.")
        if not 1 <= self.phrase_duration <= 15:
            raise ConfigurationError("Phrase duration must be between 1 and 15 seconds.")
        if not -10 <= self.speech_rate <= 10:
            raise ConfigurationError("Speech rate must be between -10 and 10.")
        if not self.wake_word.strip():
            raise ConfigurationError("Wake word cannot be empty.")
        if not self.screenshot_directory.strip() or not self.project_directory.strip():
            raise ConfigurationError("Configured directories cannot be empty.")
        if not self.ai_model.strip() or len(self.ai_model) > 128:
            raise ConfigurationError("AI model must contain between 1 and 128 characters.")
        try:
            endpoint = urlsplit(self.ai_endpoint)
            hostname = endpoint.hostname
            endpoint.port
        except ValueError as exc:
            raise ConfigurationError("AI endpoint must be a valid local Ollama URL.") from exc
        try:
            is_loopback = hostname == "localhost" or (
                hostname is not None and ipaddress.ip_address(hostname).is_loopback
            )
        except ValueError:
            is_loopback = False
        if (
            endpoint.scheme != "http"
            or not is_loopback
            or endpoint.username
            or endpoint.password
            or endpoint.query
            or endpoint.fragment
            or endpoint.path not in ("", "/")
        ):
            raise ConfigurationError(
                "AI endpoint must use HTTP and point to localhost or a loopback address."
            )


def load_settings(path: Path | None = None) -> Settings:
    settings_path = path or default_settings_path()
    settings = Settings()
    if not settings_path.exists():
        return settings
    try:
        raw = json.loads(settings_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            raise ValueError("Settings must be a JSON object.")
        allowed = {item.name for item in fields(Settings)}
        settings = Settings(**{key: value for key, value in raw.items() if key in allowed})
        settings.validate()
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise ConfigurationError(f"Could not load POVA settings: {exc}") from exc
    return settings


def save_settings(settings: Settings, path: Path | None = None) -> None:
    settings.validate()
    settings_path = path or default_settings_path()
    try:
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            "w", encoding="utf-8", dir=settings_path.parent, delete=False
        ) as temporary:
            json.dump(asdict(settings), temporary, indent=2)
            temporary.write("\n")
            temporary_path = Path(temporary.name)
        temporary_path.replace(settings_path)
    except OSError as exc:
        raise ConfigurationError(f"Could not save POVA settings: {exc}") from exc
