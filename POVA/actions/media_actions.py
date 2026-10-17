"""Safe multimedia-key and volume controls."""

import ctypes

from actions.system_actions import require_windows
from actions import ActionError


VOLUME_KEYS = {"up": 0xAF, "down": 0xAE, "mute": 0xAD}
MEDIA_KEYS = {"play_pause": 0xB3, "next": 0xB0, "previous": 0xB1}


def _tap_virtual_key(key: int) -> None:
    require_windows()
    try:
        ctypes.windll.user32.keybd_event(key, 0, 0, 0)
        ctypes.windll.user32.keybd_event(key, 0, 2, 0)
    except (AttributeError, OSError) as exc:
        raise ActionError("Windows could not send the media key.") from exc


def set_volume(direction: str) -> str:
    if direction not in VOLUME_KEYS:
        raise ActionError("Unsupported volume action.")
    _tap_virtual_key(VOLUME_KEYS[direction])
    return {"up": "Volume increased.", "down": "Volume decreased.", "mute": "Volume mute toggled."}[direction]


def send_media_key(action: str) -> str:
    if action not in MEDIA_KEYS:
        raise ActionError("Unsupported media action.")
    _tap_virtual_key(MEDIA_KEYS[action])
    return {"play_pause": "Toggling playback.", "next": "Skipping to the next track.",
            "previous": "Returning to the previous track."}[action]
