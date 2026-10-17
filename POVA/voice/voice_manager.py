"""Lifecycle-managed voice recognition and serialized TTS worker."""

from __future__ import annotations

import logging
import queue
import threading
from typing import Callable

from config.settings import Settings
from voice.tts import WindowsSpeechSynthesizer
from voice.windows_speech import SpeechRecognitionBackend, VoiceError, WindowsSpeechBackend


LOGGER = logging.getLogger("pova")


class VoiceManager:
    def __init__(
        self,
        settings: Settings | None = None,
        status_callback: Callable[[str], None] | None = None,
    ):
        self.settings = settings or Settings()
        self.status_callback = status_callback or (lambda _status: None)
        self.backend: SpeechRecognitionBackend = WindowsSpeechBackend(self.settings)
        self.synthesizer = WindowsSpeechSynthesizer()
        self._stop_event = threading.Event()
        self._speech_queue: queue.Queue[tuple[str, int] | None] = queue.Queue()
        self._speaker = threading.Thread(target=self._speak_loop, name="pova-tts", daemon=True)
        self._speaker.start()

    @property
    def available(self) -> bool:
        return self.backend.available

    def run(self, on_text: Callable[[str], None]) -> None:
        if not self.backend.available:
            self.status_callback("ERROR:POVA voice recognition is available on Windows 10 and Windows 11.")
            return
        while not self._stop_event.is_set():
            try:
                self.status_callback("LISTENING")
                self.status_callback("RECOGNIZING")
                text = self.backend.listen_once()
                if not self._stop_event.is_set():
                    on_text(text)
            except VoiceError as exc:
                if self._stop_event.is_set():
                    break
                LOGGER.warning("Voice recognition failed: %s", exc)
                self.status_callback(f"ERROR:{exc}")
                self._stop_event.wait(1)
        self.status_callback("IDLE")

    def test_microphone(self) -> str:
        self.backend.reset()
        return self.backend.listen_once()

    def listen_once(self) -> str:
        return self.backend.listen_once()

    def start_listening(self) -> None:
        self._stop_event.clear()
        self.backend.reset()

    def speak(self, text: str) -> None:
        if self.settings.voice_response_enabled:
            self._speech_queue.put((text, self.settings.speech_rate))

    def _speak_loop(self) -> None:
        while True:
            item = self._speech_queue.get()
            if item is None:
                return
            text, rate = item
            try:
                self.status_callback("SPEAKING")
                self.synthesizer.speak(text, rate)
            except VoiceError as exc:
                LOGGER.warning("Text-to-speech unavailable: %s", exc)
                self.status_callback(f"VOICE_ERROR:{exc}")
            finally:
                self.status_callback("LISTENING" if not self._stop_event.is_set() else "IDLE")

    def stop(self) -> None:
        self.stop_listening()
        self.synthesizer.stop()
        while True:
            try:
                self._speech_queue.get_nowait()
            except queue.Empty:
                break
        self._speech_queue.put(None)
        if self._speaker.is_alive() and threading.current_thread() is not self._speaker:
            self._speaker.join(timeout=1)

    def stop_listening(self) -> None:
        self._stop_event.set()
        self.backend.stop()
