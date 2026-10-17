"""Allowlisted applications, websites, and spoken aliases."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Application:
    name: str
    commands: tuple[str, ...]
    aliases: tuple[str, ...]
    paths: tuple[str, ...] = ()


APPLICATIONS: dict[str, Application] = {
    "notepad": Application("Notepad", ("notepad.exe",), ("notepad", "note pad", "notes")),
    "calculator": Application("Calculator", ("calc.exe",), ("calculator", "calc")),
    "paint": Application("Paint", ("mspaint.exe",), ("paint", "microsoft paint")),
    "file explorer": Application("File Explorer", ("explorer.exe",), ("file explorer", "explorer", "files")),
    "command prompt": Application("Command Prompt", ("cmd.exe",), ("command prompt", "cmd")),
    "powershell": Application("PowerShell", ("powershell.exe",), ("powershell", "power shell")),
    "windows terminal": Application("Windows Terminal", ("wt.exe",), ("windows terminal", "terminal")),
    "vs code": Application(
        "VS Code",
        ("code.exe", "code"),
        ("vs code", "visual studio code", "vscode", "visual studio"),
        (
            "%LOCALAPPDATA%\\Programs\\Microsoft VS Code\\Code.exe",
            "%ProgramFiles%\\Microsoft VS Code\\Code.exe",
        ),
    ),
    "chrome": Application(
        "Chrome",
        ("chrome.exe", "chrome"),
        ("chrome", "google chrome"),
        (
            "%ProgramFiles%\\Google\\Chrome\\Application\\chrome.exe",
            "%ProgramFiles(x86)%\\Google\\Chrome\\Application\\chrome.exe",
            "%LOCALAPPDATA%\\Google\\Chrome\\Application\\chrome.exe",
        ),
    ),
    "microsoft edge": Application(
        "Microsoft Edge",
        ("msedge.exe",),
        ("microsoft edge", "edge"),
        (
            "%ProgramFiles(x86)%\\Microsoft\\Edge\\Application\\msedge.exe",
            "%ProgramFiles%\\Microsoft\\Edge\\Application\\msedge.exe",
        ),
    ),
    "firefox": Application(
        "Firefox",
        ("firefox.exe", "firefox"),
        ("firefox", "mozilla firefox"),
        ("%ProgramFiles%\\Mozilla Firefox\\firefox.exe", "%ProgramFiles(x86)%\\Mozilla Firefox\\firefox.exe"),
    ),
    "task manager": Application("Task Manager", ("taskmgr.exe",), ("task manager",)),
}

WEBSITES: dict[str, tuple[str, str, tuple[str, ...]]] = {
    "google": ("Google", "https://www.google.com", ("google",)),
    "youtube": ("YouTube", "https://www.youtube.com", ("youtube", "you tube")),
    "github": ("GitHub", "https://github.com", ("github", "git hub")),
    "gmail": ("Gmail", "https://mail.google.com", ("gmail", "g mail")),
    "chatgpt": ("ChatGPT", "https://chatgpt.com", ("chatgpt", "chat gpt")),
    "linkedin": ("LinkedIn", "https://www.linkedin.com", ("linkedin", "linked in")),
}

DIRECTORIES: dict[str, tuple[str, ...]] = {
    "downloads": ("downloads",),
    "documents": ("documents", "my documents"),
    "desktop": ("desktop",),
    "pictures": ("pictures", "photos"),
    "project folder": ("project folder", "pova folder"),
}

CONFIRMATION_INTENTS = frozenset({"SHUTDOWN", "RESTART", "SLEEP", "HIBERNATE"})

# Intent names are the only executable operations accepted by the action dispatcher.
COMMANDS = frozenset({
    "OPEN_APPLICATION", "OPEN_WEBSITE", "OPEN_DIRECTORY", "LOCK_WINDOWS",
    "SHOW_DESKTOP", "TAKE_SCREENSHOT", "VOLUME_UP", "VOLUME_DOWN",
    "MUTE_VOLUME", "UNMUTE_VOLUME", "MEDIA_PLAY_PAUSE", "MEDIA_NEXT",
    "MEDIA_PREVIOUS", "OPEN_SETTINGS", "TIME", "DATE", "SHUTDOWN",
    "RESTART", "SLEEP", "HIBERNATE", "WAKE_WORD",
})
