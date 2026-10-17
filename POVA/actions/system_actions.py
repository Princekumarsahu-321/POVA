"""Windows-specific desktop actions isolated from portable application code."""

from datetime import datetime
import ctypes
import os
from pathlib import Path
import subprocess

from actions import ActionError


def require_windows() -> None:
    if os.name != "nt":
        raise ActionError("POVA currently supports Windows 10 and Windows 11.")


def lock_windows() -> str:
    require_windows()
    if not ctypes.windll.user32.LockWorkStation():
        raise ActionError("Windows could not lock the workstation.")
    return "Locking Windows."


def show_desktop() -> str:
    require_windows()
    try:
        subprocess.Popen(
            ["explorer.exe", "shell:::{3080F90D-D7AD-11D9-BD98-0000947B0257}"],
            shell=False,
        )
    except OSError as exc:
        raise ActionError("Could not show the desktop.") from exc
    return "Showing the desktop."


def open_settings() -> str:
    require_windows()
    try:
        os.startfile("ms-settings:")
    except OSError as exc:
        raise ActionError("Could not open Windows Settings.") from exc
    return "Opening Windows Settings."


def take_screenshot(directory: str | None = None) -> str:
    require_windows()
    try:
        from PIL import ImageGrab
    except ImportError as exc:
        raise ActionError("Screenshot support requires Pillow. Install the project requirements.") from exc
    destination = Path(directory) if directory else Path(__file__).resolve().parents[1] / "screenshots"
    filename = destination / f"POVA_{datetime.now():%Y%m%d_%H%M%S}.png"
    try:
        destination.mkdir(parents=True, exist_ok=True)
        ImageGrab.grab(all_screens=True).save(filename)
    except (OSError, RuntimeError) as exc:
        raise ActionError("The screenshot could not be captured or saved.") from exc
    return f"Screenshot saved to {filename}."


def current_time() -> str:
    formatted = datetime.now().strftime("%I:%M %p").lstrip("0")
    return f"It is {formatted}."


def current_date() -> str:
    return f"Today is {datetime.now():%A, %B %d, %Y}."
