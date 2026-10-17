"""POVA configuration package and compatibility exports."""

from pathlib import Path

from config.commands import APPLICATIONS as APP_DEFINITIONS, WEBSITES as WEBSITE_DEFINITIONS
from config.commands import COMMANDS, DIRECTORIES
from config.settings import Settings, default_settings_path, load_settings, save_settings

APP_NAME = "POVA"
APP_SUBTITLE = "Personal Operating Voice Assistant"
WAKE_WORD = "hey pova"
PROJECT_DIR = Path(__file__).resolve().parents[1]
SCREENSHOTS_DIR = PROJECT_DIR / "screenshots"

# Keep the simple lookup shapes exported by the original config.py module.
APPLICATIONS = {
    key: (item.name, list(item.commands))
    for key, item in APP_DEFINITIONS.items()
}
COMMAND_ALIASES = {
    key: item.aliases
    for key, item in APP_DEFINITIONS.items()
}
WEBSITES = {
    key: (name, url)
    for key, (name, url, _aliases) in WEBSITE_DEFINITIONS.items()
}

__all__ = [
    "APP_NAME", "APP_SUBTITLE", "WAKE_WORD", "PROJECT_DIR", "SCREENSHOTS_DIR",
    "APPLICATIONS", "COMMAND_ALIASES", "WEBSITES", "COMMANDS", "DIRECTORIES",
    "Settings", "default_settings_path", "load_settings", "save_settings",
]
