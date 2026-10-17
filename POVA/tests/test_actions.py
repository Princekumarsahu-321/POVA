import subprocess

import pytest

from actions import ActionError, execute
from actions import application_actions
from core.intent import ParsedCommand
from core.security import CommandError


def test_application_launch_uses_resolved_executable_and_no_shell(monkeypatch):
    calls = []
    monkeypatch.setattr(application_actions, "require_windows", lambda: None)
    monkeypatch.setattr(application_actions.shutil, "which", lambda _name: r"C:\Windows\notepad.exe")
    monkeypatch.setattr(application_actions.subprocess, "Popen", lambda args, **kwargs: calls.append((args, kwargs)))

    response = application_actions.open_application("notepad")

    assert response == "Opening Notepad."
    assert calls[0][0] == [r"C:\Windows\notepad.exe"]
    assert calls[0][1]["shell"] is False


def test_missing_application_is_reported(monkeypatch):
    monkeypatch.setattr(application_actions, "require_windows", lambda: None)
    monkeypatch.setattr(application_actions.shutil, "which", lambda _name: None)
    monkeypatch.setattr(application_actions.Path, "is_file", lambda _path: False)

    with pytest.raises(ActionError, match="Chrome is not installed"):
        application_actions.open_application("chrome")


def test_unlisted_application_is_rejected():
    with pytest.raises(CommandError):
        execute(ParsedCommand("OPEN_APPLICATION", "arbitrary program"))


def test_non_windows_operations_fail_clearly(monkeypatch):
    from actions import system_actions

    monkeypatch.setattr(system_actions.os, "name", "posix")
    with pytest.raises(ActionError, match="Windows 10 and Windows 11"):
        system_actions.lock_windows()


def test_power_action_uses_fixed_arguments(monkeypatch):
    from actions import windows_actions

    calls = []
    monkeypatch.setattr(windows_actions, "require_windows", lambda: None)
    monkeypatch.setattr(windows_actions.subprocess, "Popen", lambda args, **kwargs: calls.append((args, kwargs)))
    assert windows_actions.power_action("SHUTDOWN") == "Shutting down in five seconds."
    assert calls[0][0] == ["shutdown.exe", "/s", "/t", "5"]
    assert calls[0][1]["shell"] is False
