"""Natural-language command normalization and safe intent detection."""

from dataclasses import dataclass
import re
from typing import Optional

from config import APPLICATIONS, COMMAND_ALIASES, WEBSITES


@dataclass(frozen=True)
class ParsedCommand:
    intent: str
    target: Optional[str] = None
    display_name: Optional[str] = None
    requires_confirmation: bool = False


def normalize_text(text: str) -> str:
    """Normalize speech-recognition output without changing its meaning."""
    normalized = text.casefold().strip()
    normalized = re.sub(r"[^\w\s]", " ", normalized)
    return re.sub(r"\s+", " ", normalized)


def remove_wake_word(text: str) -> str:
    normalized = normalize_text(text)
    return re.sub(r"^\s*(?:hey\s+)?pova\b[:,]?\s*", "", normalized).strip()


def _find_target(text: str, aliases: dict[str, tuple[str, ...]]) -> Optional[str]:
    for target, names in aliases.items():
        if any(re.search(rf"\b{re.escape(name)}\b", text) for name in names):
            return target
    return None


def parse_command(spoken_text: str) -> ParsedCommand:
    text = remove_wake_word(spoken_text)
    if not text:
        return ParsedCommand("WAKE_WORD")

    if re.search(r"\b(?:shutdown|shut down|turn off)\b", text):
        return ParsedCommand("SHUTDOWN", requires_confirmation=True)
    if re.search(r"\brestart\b|\breboot\b", text):
        return ParsedCommand("RESTART", requires_confirmation=True)
    if re.search(r"\b(?:lock|secure)\b.*\b(?:windows|computer|pc|workstation|screen)\b", text):
        return ParsedCommand("LOCK_WINDOWS")
    if re.search(r"\b(?:screenshot|screen shot|screen capture)\b", text):
        return ParsedCommand("TAKE_SCREENSHOT")
    if re.search(r"\bvolume\b.*\bup\b|\bincrease\b.*\bvolume\b", text):
        return ParsedCommand("VOLUME_UP")
    if re.search(r"\bvolume\b.*\bdown\b|\bdecrease\b.*\bvolume\b", text):
        return ParsedCommand("VOLUME_DOWN")
    if re.search(r"\b(?:mute|silence)\b.*\bvolume\b|\bmute\b", text):
        return ParsedCommand("MUTE_VOLUME")
    if re.search(r"\bshow\s+desktop\b|\bminimize\b.*\bwindows\b", text):
        return ParsedCommand("SHOW_DESKTOP")
    if re.search(r"\bwhat\b.*\btime\b|\btime\b.*\bnow\b", text):
        return ParsedCommand("TIME")
    if re.search(r"\b(?:what|which)\b.*\bdate\b|\btoday'?s\s+date\b", text):
        return ParsedCommand("DATE")

    website = _find_target(text, {key: (key,) for key in WEBSITES})
    if website and re.search(r"\b(?:open|launch|go|visit|show)\b", text):
        return ParsedCommand("OPEN_WEBSITE", website, WEBSITES[website][0])

    app = _find_target(text, COMMAND_ALIASES)
    if app and re.search(r"\b(?:open|launch|start|run)\b", text):
        return ParsedCommand("OPEN_APPLICATION", app, APPLICATIONS[app][0])

    return ParsedCommand("UNKNOWN")


def is_confirmation(text: str) -> bool:
    return normalize_text(text) in {"yes", "yeah", "yep", "sure", "confirm", "do it", "okay", "ok"}


def is_rejection(text: str) -> bool:
    return normalize_text(text) in {"no", "nope", "cancel", "stop", "dont", "do not"}
