"""Windows-native microphone speech recognition and text-to-speech for POVA."""

import subprocess
import threading
from typing import Callable, Optional


class VoiceError(RuntimeError):
    """A recoverable voice subsystem error."""


class Voice:
    def __init__(self, status_callback: Optional[Callable[[str], None]] = None):
        self.status_callback = status_callback or (lambda _message: None)
        self._stop_event = threading.Event()

    def speak(self, text: str) -> None:
        """Use Windows SAPI through PowerShell. No audio Python package is required."""
        command = (
            "Add-Type -AssemblyName System.Speech; "
            "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
            "$s.Speak([Console]::In.ReadToEnd())"
        )
        try:
            result = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                input=text,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
            if result.returncode != 0:
                self.status_callback("Voice response unavailable.")
        except (OSError, subprocess.TimeoutExpired):
            self.status_callback("Voice response unavailable.")

    def listen_once(self, timeout: float = 10) -> str:
        """Capture speech using Windows System.Speech, avoiding sounddevice/PyAudio."""
        script = r'''
Add-Type -AssemblyName System.Speech
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$recognizer.SetInputToDefaultAudioDevice()
$recognizer.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
$result = $recognizer.Recognize([TimeSpan]::FromSeconds(10))
if ($null -ne $result) { Write-Output $result.Text }
'''
        try:
            self.status_callback("Listening...")
            completed = subprocess.run(
                ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=timeout + 3,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise VoiceError("No speech detected.") from exc
        except OSError as exc:
            raise VoiceError("Windows PowerShell could not be started.") from exc

        if completed.returncode != 0:
            error = completed.stderr.strip()
            if error:
                raise VoiceError("Windows speech recognition failed.")
            raise VoiceError("No speech detected.")

        text = completed.stdout.strip()
        if not text:
            raise VoiceError("No speech detected.")

        self.status_callback("Recognized.")
        return text

    def run(self, on_text: Callable[[str], None]) -> None:
        self._stop_event.clear()
        while not self._stop_event.is_set():
            try:
                text = self.listen_once()
                if text and not self._stop_event.is_set():
                    on_text(text)
            except VoiceError as exc:
                self.status_callback(str(exc))
                # Do not spin at 100% CPU after a timeout/error.
                self._stop_event.wait(0.5)

    def stop(self) -> None:
        self._stop_event.set()
