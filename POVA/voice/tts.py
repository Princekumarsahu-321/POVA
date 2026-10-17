"""Local Windows SAPI speech synthesis."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import threading

from voice.windows_speech import VoiceError


_SPEECH_SCRIPT = r"""
Add-Type -AssemblyName System.Speech
$encoded = [Console]::In.ReadToEnd()
$payload = [System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String($encoded)) | ConvertFrom-Json
$speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $femaleVoice = $speaker.GetInstalledVoices() |
        Where-Object { $_.VoiceInfo.Gender -eq [System.Speech.Synthesis.VoiceGender]::Female } |
        Select-Object -First 1
    if ($null -eq $femaleVoice) {
        throw "No installed female speech voice is available."
    }
    $speaker.SelectVoice($femaleVoice.VoiceInfo.Name)
    $speaker.Rate = [int]$payload.rate
    $speaker.Speak([string]$payload.text)
}
finally { $speaker.Dispose() }
"""


class WindowsSpeechSynthesizer:
    """Speak response text using a static SAPI script (never as PowerShell code)."""

    def __init__(self) -> None:
        self._process: subprocess.Popen[str] | None = None
        self._lock = threading.Lock()

    def speak(self, text: str, rate: int = 0) -> None:
        if os.name != "nt":
            raise VoiceError("Voice responses are available on Windows.")
        payload = base64.b64encode(
            json.dumps(
                {"text": text, "rate": max(-10, min(10, rate))},
                ensure_ascii=False,
            ).encode("utf-8")
        ).decode("ascii")
        try:
            process = subprocess.Popen(
                ["powershell.exe", "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", _SPEECH_SCRIPT],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                shell=False,
            )
            with self._lock:
                self._process = process
            _stdout, _stderr = process.communicate(input=payload, timeout=30)
        except (OSError, subprocess.TimeoutExpired) as exc:
            if isinstance(exc, subprocess.TimeoutExpired) and "process" in locals():
                process.kill()
                process.communicate()
            raise VoiceError("Voice response is unavailable.") from exc
        finally:
            with self._lock:
                self._process = None
        if process.returncode:
            raise VoiceError("Voice response is unavailable.")

    def stop(self) -> None:
        with self._lock:
            process = self._process
        if process and process.poll() is None:
            process.terminate()
