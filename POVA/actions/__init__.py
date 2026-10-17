"""Allowlisted action registry and dispatch."""

from core.intent import ParsedCommand
from core.security import validate_command


class ActionError(RuntimeError):
    """A user-safe action failure."""


from actions.application_actions import open_application, open_directory
from actions.browser_actions import open_website
from actions.media_actions import send_media_key, set_volume
from actions.system_actions import (
    current_date, current_time, lock_windows, open_settings, show_desktop,
    take_screenshot,
)
from actions.windows_actions import power_action


def execute(
    command: ParsedCommand,
    screenshot_directory: str | None = None,
    project_directory: str | None = None,
) -> str:
    """Execute only structured commands that pass the central allowlist."""
    validate_command(command)
    intent = command.intent
    if intent == "OPEN_APPLICATION":
        return open_application(command.target or "")
    if intent == "OPEN_WEBSITE":
        return open_website(command.target or "")
    if intent == "OPEN_DIRECTORY":
        return open_directory(command.target or "", project_directory)
    if intent == "LOCK_WINDOWS":
        return lock_windows()
    if intent == "SHOW_DESKTOP":
        return show_desktop()
    if intent == "TAKE_SCREENSHOT":
        return take_screenshot(screenshot_directory)
    if intent == "VOLUME_UP":
        return set_volume("up")
    if intent == "VOLUME_DOWN":
        return set_volume("down")
    if intent in {"MUTE_VOLUME", "UNMUTE_VOLUME"}:
        return set_volume("mute")
    if intent == "MEDIA_PLAY_PAUSE":
        return send_media_key("play_pause")
    if intent == "MEDIA_NEXT":
        return send_media_key("next")
    if intent == "MEDIA_PREVIOUS":
        return send_media_key("previous")
    if intent == "OPEN_SETTINGS":
        return open_settings()
    if intent == "TIME":
        return current_time()
    if intent == "DATE":
        return current_date()
    if intent in {"SHUTDOWN", "RESTART", "SLEEP", "HIBERNATE"}:
        return power_action(intent)
    raise ActionError("I didn't understand that command.")


__all__ = ["ActionError", "execute"]
