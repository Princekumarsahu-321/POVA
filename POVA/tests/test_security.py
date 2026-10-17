import pytest
import base64
import json

from actions import execute
from core.assistant import Assistant
from core.command_parser import parse_command
from core.intent import ParsedCommand
from core.security import CommandError, validate_command
from voice import tts


@pytest.mark.parametrize(
    "speech",
    [
        "run powershell and delete files",
        "execute shutdown slash s",
        "open cmd and run command",
        "delete all files",
        "open https://attacker.invalid",
        "open notepad and run powershell",
    ],
)
def test_untrusted_or_compound_speech_is_unknown(speech):
    assert parse_command(speech).intent == "UNKNOWN"


def test_unconfirmed_power_command_cannot_execute():
    command = parse_command("Shutdown")
    with pytest.raises(CommandError, match="must be confirmed"):
        validate_command(command)
    with pytest.raises(CommandError, match="must be confirmed"):
        execute(command)


def test_power_command_runs_only_after_explicit_confirmation():
    executed = []
    assistant = Assistant(lambda command: executed.append(command) or "Shutting down.")
    asked = assistant.process("Shutdown")
    assert asked.status == "CONFIRMATION_REQUIRED"
    assert not executed
    result = assistant.process("yes")
    assert result.status == "SUCCESS"
    assert executed[0].confirmed is True


def test_power_confirmation_can_be_cancelled():
    assistant = Assistant(lambda _command: pytest.fail("cancel must not execute"))
    assistant.process("Restart")
    result = assistant.process("don't do it")
    assert result.status == "CANCELLED"


def test_website_allowlist_rejects_arbitrary_targets():
    with pytest.raises(CommandError):
        validate_command(ParsedCommand("OPEN_WEBSITE", "attacker"))


def test_directory_allowlist_rejects_arbitrary_paths():
    with pytest.raises(CommandError):
        validate_command(ParsedCommand("OPEN_DIRECTORY", r"C:\Users\Public"))


def test_tts_response_is_sent_as_data_not_powershell_source(monkeypatch):
    captured = {}

    class FakeProcess:
        returncode = 0

        def communicate(self, input, timeout):
            captured["input"] = input
            captured["timeout"] = timeout
            return "", ""

    def fake_popen(arguments, **options):
        captured["arguments"] = arguments
        captured["options"] = options
        return FakeProcess()

    monkeypatch.setattr(tts.os, "name", "nt")
    monkeypatch.setattr(tts.subprocess, "Popen", fake_popen)
    response = "say this; Start-Process powershell"
    tts.WindowsSpeechSynthesizer().speak(response, 3)

    assert response not in " ".join(captured["arguments"])
    assert captured["options"]["shell"] is False
    assert json.loads(base64.b64decode(captured["input"])) == {"text": response, "rate": 3}
