"""Application configuration and allowlisted command definitions."""

from pathlib import Path

APP_NAME = "POVA"
APP_SUBTITLE = "Personal Operating Voice Assistant"
WAKE_WORD = "hey pova"
PROJECT_DIR = Path(__file__).resolve().parent
SCREENSHOTS_DIR = Path.home() / "Pictures" / "Screenshots"

APPLICATIONS = {
    "notepad": ("Notepad", ["notepad.exe"]),
    "calculator": ("Calculator", ["calc.exe"]),
    "file explorer": ("File Explorer", ["explorer.exe"]),
    "chrome": ("Chrome", ["chrome.exe"]),
    "vs code": ("VS Code", ["code.exe"]),
    "command prompt": ("Command Prompt", ["cmd.exe"]),
    "powershell": ("PowerShell", ["powershell.exe"]),
}

WEBSITES = {
    "youtube": ("YouTube", "https://www.youtube.com"),
    "google": ("Google", "https://www.google.com"),
    "github": ("GitHub", "https://github.com"),
}

COMMAND_ALIASES = {
    "notepad": ("notepad", "notes", "notebook", "note pad"),
    "calculator": ("calculator", "calc"),
    "file explorer": ("file explorer", "explorer", "files"),
    "chrome": ("chrome", "google chrome", "browser"),
    "vs code": ("vs code", "visual studio code", "vscode"),
    "command prompt": ("command prompt", "cmd"),
    "powershell": ("powershell",),
}
