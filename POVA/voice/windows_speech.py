"""Windows System.Speech command-grammar recognition through PowerShell."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import threading
from typing import Protocol

from config.commands import APPLICATIONS, DIRECTORIES, WEBSITES
from config.settings import Settings


class VoiceError(RuntimeError):
    """A recoverable microphone or speech recognition failure."""


class SpeechRecognitionBackend(Protocol):
    @property
    def available(self) -> bool: ...

    def listen_once(self) -> str: ...

    def stop(self) -> None: ...

    def reset(self) -> None: ...


def _command_phrases(wake_word: str) -> list[str]:
    phrases = {
        "lock windows", "lock my computer", "lock computer", "lock my pc", "secure computer",
        "show desktop", "minimize all windows", "take screenshot", "take a screenshot",
        "capture screen", "screen capture", "volume up", "increase volume", "volume down",
        "decrease volume", "mute", "mute volume", "unmute volume", "play", "pause",
        "next track", "previous track", "open settings", "open windows settings",
        "what time is it", "tell me the time", "what is the time", "what is today's date",
        "tell me today's date", "tell me time", "today's date", "what's today's date",
        "what is the date", "shutdown", "shut down", "shutdown my pc", "shutdown my computer",
        "shut down my computer", "turn off", "turn off my pc", "turn off my computer",
        "restart", "restart my pc", "restart my computer", "reboot", "sleep",
        "put my pc to sleep", "put my computer to sleep", "hibernate", "hibernate my computer",
        "yes", "yeah", "yep", "confirm", "okay", "do it", "no", "nope", "cancel", "stop",
        "don't", "dont", "do not", "don't do it", "volume unmute", "hey pova", "pova",
        "testing microphone",
    }
    for app in APPLICATIONS.values():
        phrases.update(f"{verb} {alias}" for verb in ("open", "launch", "start", "run") for alias in app.aliases)
    for _key, (_name, _url, aliases) in WEBSITES.items():
        phrases.update(f"{verb} {alias}" for verb in ("open", "visit", "go to") for alias in aliases)
    for aliases in DIRECTORIES.values():
        phrases.update(f"{verb} {alias}" for verb in ("open", "launch") for alias in aliases)
    phrases.update(
        f"{prefix} {phrase}"
        for phrase in tuple(phrases)
        for prefix in (wake_word, f"hey {wake_word}")
    )
    return sorted(phrases)


_RECOGNITION_SCRIPT = r"""
Add-Type -AssemblyName System.Speech
$inputBase64 = [Console]::In.ReadToEnd()
$inputJson = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($inputBase64))
$phrases = ConvertFrom-Json -InputObject $inputJson
$choices = New-Object System.Speech.Recognition.Choices
foreach ($phrase in $phrases) { [void]$choices.Add([string]$phrase) }
$builder = New-Object System.Speech.Recognition.GrammarBuilder
$builder.Append($choices)
$grammar = New-Object System.Speech.Recognition.Grammar($builder)
$recognizer = New-Object System.Speech.Recognition.SpeechRecognitionEngine
try {
    $recognizer.SetInputToDefaultAudioDevice()
    $recognizer.LoadGrammar($grammar)
    $result = $recognizer.Recognize([TimeSpan]::FromSeconds(__PHRASE_DURATION__))
    if ($null -ne $result) { [Console]::Out.WriteLine($result.Text) }
}
finally {
    $recognizer.Dispose()
}
"""


class WindowsSpeechBackend:
    """Recognize a finite POVA command grammar without Python audio DLLs."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or Settings()
        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()
        self._cancelled = False

    @property
    def available(self) -> bool:
        return os.name == "nt" and bool(subprocess_which("powershell.exe"))

    def listen_once(self) -> str:
        with self._lock:
            if self._cancelled:
                raise VoiceError("Listening stopped.")
        if not self.available:
            raise VoiceError("POVA voice recognition is available on Windows 10 and Windows 11.")
        try:
            process = subprocess.Popen(
                [
                    "powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive",
                    "-Command",
                    _RECOGNITION_SCRIPT.replace(
                        "__PHRASE_DURATION__", str(self.settings.phrase_duration)
                    ),
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                shell=False,
            )
            with self._lock:
                self._process = process
                cancelled = self._cancelled
            if cancelled:
                process.terminate()
            try:
                stdout, stderr = process.communicate(
                    base64.b64encode(
                        json.dumps(
                            _command_phrases(self.settings.wake_word),
                            ensure_ascii=False,
                        ).encode("utf-8")
                    ).decode("ascii"),
                    timeout=self.settings.recognition_timeout + 5,
                )
            except subprocess.TimeoutExpired as exc:
                process.kill()
                process.communicate()
                raise VoiceError("Recognition timed out. Please try again.") from exc
            if process.returncode:
                details = stderr.strip().lower()
                if "audio" in details or "microphone" in details or "input" in details:
                    raise VoiceError("Microphone unavailable. Check Windows microphone permissions and your default device.")
                raise VoiceError("Windows speech recognition is unavailable. Check that a speech language is installed.")
            recognized = stdout.strip()
            if not recognized:
                if any(word in stderr.lower() for word in ("audio", "microphone", "input device")):
                    raise VoiceError("Microphone unavailable. Check Windows microphone permissions and your default device.")
                raise VoiceError("No clear command was recognized. Please try again.")
            return recognized
        except VoiceError:
            raise
        except (OSError, subprocess.SubprocessError) as exc:
            raise VoiceError("Microphone unavailable. Please check Windows microphone permissions.") from exc
        finally:
            with self._lock:
                self._process = None

    def stop(self) -> None:
        with self._lock:
            self._cancelled = True
            process = self._process
        if process and process.poll() is None:
            process.terminate()

    def reset(self) -> None:
        with self._lock:
            self._cancelled = False


def subprocess_which(executable: str) -> str | None:
    from shutil import which

    return which(executable)
