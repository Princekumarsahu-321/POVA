import json

import pytest

from config.settings import ConfigurationError, Settings, load_settings, save_settings
from config import APP_NAME, APPLICATIONS, COMMAND_ALIASES, WEBSITES


def test_original_configuration_exports_remain_available():
    assert APP_NAME == "POVA"
    assert APPLICATIONS["notepad"][0] == "Notepad"
    assert "note pad" in COMMAND_ALIASES["notepad"]
    assert WEBSITES["github"][1] == "https://github.com"


def test_settings_round_trip(tmp_path):
    destination = tmp_path / "settings.json"
    settings = Settings(recognition_timeout=12, screenshot_directory=str(tmp_path / "shots"))
    save_settings(settings, destination)
    loaded = load_settings(destination)
    assert loaded.recognition_timeout == 12
    assert loaded.screenshot_directory == str(tmp_path / "shots")


def test_invalid_settings_are_reported(tmp_path):
    destination = tmp_path / "settings.json"
    destination.write_text(json.dumps({"speech_rate": 50}), encoding="utf-8")
    with pytest.raises(ConfigurationError, match="Speech rate"):
        load_settings(destination)


def test_settings_reject_out_of_range_values():
    with pytest.raises(ConfigurationError):
        Settings(recognition_timeout=1).validate()
