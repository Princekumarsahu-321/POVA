"""Allowlisted Windows actions. No speech input is ever executed as a shell command."""

from datetime import datetime
import ctypes
import os
from pathlib import Path
import subprocess
import time
import webbrowser

from config import APPLICATIONS, SCREENSHOTS_DIR, WEBSITES


class ActionError(RuntimeError):
    """A safe, user-facing action failure."""


def _require_windows() -> None:
    if os.name != "nt":
        raise ActionError("Windows actions are only available on Windows.")


def open_application(target: str) -> str:
    _require_windows()
    try:
        subprocess.Popen(APPLICATIONS[target][1], shell=False)
    except FileNotFoundError as exc:
        raise ActionError(f"{APPLICATIONS[target][0]} is not installed or is not on PATH.") from exc
    except OSError as exc:
        raise ActionError(f"Could not open {APPLICATIONS[target][0]}.") from exc
    return f"Opening {APPLICATIONS[target][0]}."


def open_website(target: str) -> str:
    if not webbrowser.open_new_tab(WEBSITES[target][1]):
        raise ActionError(f"Could not open {WEBSITES[target][0]} in the browser.")
    return f"Opening {WEBSITES[target][0]}."


def lock_windows() -> str:
    _require_windows()
    if not ctypes.windll.user32.LockWorkStation():
        raise ActionError("Windows could not lock the workstation.")
    return "Windows is locked."


def take_screenshot() -> str:
    _require_windows()
    try:
        from PIL import ImageGrab
    except ImportError as exc:
        raise ActionError("Screenshot support requires Pillow. Install the project requirements.") from exc
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    filename = SCREENSHOTS_DIR / f"POVA_{datetime.now():%Y%m%d_%H%M%S}.png"
    try:
        ImageGrab.grab(all_screens=True).save(filename)
    except OSError as exc:
        raise ActionError("The screenshot could not be saved.") from exc
    return f"Screenshot saved to {filename}."


def adjust_volume(direction: str) -> str:
    _require_windows()
    # VK_VOLUME_* are the documented Windows multimedia virtual-key codes.
    key = {"up": 0xAF, "down": 0xAE, "mute": 0xAD}[direction]
    ctypes.windll.user32.keybd_event(key, 0, 0, 0)
    ctypes.windll.user32.keybd_event(key, 0, 2, 0)
    return {"up": "Volume increased.", "down": "Volume decreased.", "mute": "Volume muted."}[direction]


def show_desktop() -> str:
    _require_windows()
    subprocess.Popen(["explorer.exe", "shell:::{3080F90D-D7AD-11D9-BD98-0000947B0257}"], shell=False)
    return "Showing the desktop."


def current_time() -> str:
    return f"It is {datetime.now():%I:%M %p}."


def current_date() -> str:
    return f"Today is {datetime.now():%A, %B %d, %Y}."


def shutdown_windows() -> str:
    _require_windows()
    subprocess.Popen(["shutdown", "/s", "/t", "5"], shell=False)
    return "Shutting down in five seconds."


def restart_windows() -> str:
    _require_windows()
    subprocess.Popen(["shutdown", "/r", "/t", "5"], shell=False)
    return "Restarting in five seconds."


def execute(parsed) -> str:
    """Execute only a ParsedCommand produced by command.parse_command."""
    handlers = {
        "OPEN_APPLICATION": lambda: open_application(parsed.target),
        "OPEN_WEBSITE": lambda: open_website(parsed.target),
        "LOCK_WINDOWS": lock_windows,
        "TAKE_SCREENSHOT": take_screenshot,
        "VOLUME_UP": lambda: adjust_volume("up"),
        "VOLUME_DOWN": lambda: adjust_volume("down"),
        "MUTE_VOLUME": lambda: adjust_volume("mute"),
        "SHOW_DESKTOP": show_desktop,
        "TIME": current_time,
        "DATE": current_date,
        "SHUTDOWN": shutdown_windows,
        "RESTART": restart_windows,
    }
    handler = handlers.get(parsed.intent)
    if handler is None:
        raise ActionError("I did not understand that command.")
    return handler()
