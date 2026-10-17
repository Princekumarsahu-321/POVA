"""Speech recognition and speech synthesis backends."""

from typing import Callable

from config.settings import Settings
from voice.voice_manager import VoiceManager
from voice.windows_speech import VoiceError


class Voice(VoiceManager):
    """Compatibility constructor for earlier POVA versions."""

    def __init__(self, status_callback: Callable[[str], None] | None = None):
        super().__init__(Settings(), status_callback)

    def run(self, on_text: Callable[[str], None]) -> None:
        self.start_listening()
        super().run(on_text)


__all__ = ["Settings", "Voice", "VoiceError", "VoiceManager"]
