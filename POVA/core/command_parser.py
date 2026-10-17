"""Deterministic parser for safe, explicitly supported spoken commands."""

from __future__ import annotations

import re

from config.commands import APPLICATIONS, DIRECTORIES, WEBSITES
from core.intent import ParsedCommand


def normalize_text(text: str) -> str:
    """Normalize recognized text without interpreting it as executable input."""
    text = text.casefold().replace("’", "'")
    text = re.sub(r"[^\w\s']", " ", text, flags=re.UNICODE)
    return re.sub(r"\s+", " ", text).strip()


def remove_wake_word(text: str, wake_word: str = "pova") -> str:
    """Remove an optional leading POVA wake word."""
    normalized = normalize_text(text)
    wake_word = normalize_text(wake_word)
    if not wake_word:
        return normalized
    return re.sub(rf"^(?:hey\s+)?{re.escape(wake_word)}(?:\s+|$)", "", normalized).strip()


def _exact_target(text: str, aliases: dict[str, tuple[str, ...]]) -> str | None:
    for key, names in aliases.items():
        if text == key or text in names:
            return key
    return None


def _strip_polite_prefix(text: str) -> str:
    return re.sub(r"^(?:please\s+)?(?:could you\s+|would you\s+)?", "", text).strip()


def parse_command(
    spoken_text: str, *, wake_word_enabled: bool = True, wake_word: str = "pova"
) -> ParsedCommand:
    """Convert speech into one known intent; extra or unsupported words fail closed."""
    text = _strip_polite_prefix(
        remove_wake_word(spoken_text, wake_word) if wake_word_enabled else normalize_text(spoken_text)
    )
    if not text:
        return ParsedCommand("WAKE_WORD")

    power_patterns = (
        (r"(?:please\s+)?(?:shut down|shutdown|turn off)(?:\s+(?:my\s+)?(?:pc|computer|windows))?", "SHUTDOWN"),
        (r"(?:please\s+)?(?:restart|reboot)(?:\s+(?:my\s+)?(?:pc|computer|windows))?", "RESTART"),
        (r"(?:please\s+)?(?:put (?:my )?(?:pc|computer) to sleep|sleep)", "SLEEP"),
        (r"(?:please\s+)?hibernate(?:\s+(?:my\s+)?(?:pc|computer))?", "HIBERNATE"),
    )
    for pattern, intent in power_patterns:
        if re.fullmatch(pattern, text):
            return ParsedCommand(intent, requires_confirmation=True)

    phrases: tuple[tuple[str, tuple[str, ...]], ...] = (
        ("LOCK_WINDOWS", ("lock windows", "lock my computer", "lock computer", "lock my pc",
                          "lock pc", "secure computer", "lock workstation")),
        ("SHOW_DESKTOP", ("show desktop", "minimize all windows")),
        ("TAKE_SCREENSHOT", ("take screenshot", "take a screenshot", "capture screen",
                             "screen capture", "capture the screen")),
        ("VOLUME_UP", ("volume up", "increase volume", "turn volume up", "raise volume")),
        ("VOLUME_DOWN", ("volume down", "decrease volume", "turn volume down", "lower volume")),
        ("MUTE_VOLUME", ("mute", "mute volume", "silence volume")),
        ("UNMUTE_VOLUME", ("unmute", "unmute volume", "volume unmute")),
        ("MEDIA_PLAY_PAUSE", ("play", "pause", "play pause", "toggle playback")),
        ("MEDIA_NEXT", ("next track", "skip track", "next song")),
        ("MEDIA_PREVIOUS", ("previous track", "previous song", "last track")),
        ("OPEN_SETTINGS", ("open settings", "open windows settings", "settings")),
        ("TIME", ("what time is it", "tell me the time", "tell me time", "what is the time", "time")),
        ("DATE", ("what is today's date", "what is today s date", "tell me today's date",
                  "tell me today s date", "what is the date", "what s today s date",
                  "today's date", "todays date")),
    )
    for intent, aliases in phrases:
        if text in aliases:
            return ParsedCommand(intent)

    for prefix in ("open ", "launch ", "start ", "visit ", "go to "):
        if text.startswith(prefix):
            target_text = text[len(prefix):].strip()
            website = _exact_target(target_text, {key: data[2] for key, data in WEBSITES.items()})
            if website:
                return ParsedCommand("OPEN_WEBSITE", website, WEBSITES[website][0])
            app = _exact_target(target_text, {key: item.aliases for key, item in APPLICATIONS.items()})
            if app:
                return ParsedCommand("OPEN_APPLICATION", app, APPLICATIONS[app].name)
            directory = _exact_target(target_text, DIRECTORIES)
            if directory:
                return ParsedCommand("OPEN_DIRECTORY", directory, directory.title())

    return ParsedCommand("UNKNOWN")


def is_confirmation(text: str, wake_word: str = "pova") -> bool:
    normalized = remove_wake_word(text, wake_word)
    return normalized in {"yes", "yeah", "yep", "confirm", "okay", "ok", "do it"}


def is_rejection(text: str, wake_word: str = "pova") -> bool:
    normalized = remove_wake_word(text, wake_word)
    return normalized in {
        "no", "nope", "cancel", "stop", "dont", "don't", "do not", "don't do it",
    }
