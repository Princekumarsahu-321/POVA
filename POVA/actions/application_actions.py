"""Safe allowlisted application and known-folder launching."""

from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess

from config.commands import APPLICATIONS
from actions.system_actions import require_windows
from actions import ActionError


def _resolve_application(key: str) -> str:
    if key not in APPLICATIONS:
        raise ActionError("That application is not on the allowlist.")
    app = APPLICATIONS[key]
    for candidate in app.commands:
        found = shutil.which(candidate)
        if found:
            return found
    for candidate in app.paths:
        expanded = os.path.expandvars(candidate)
        if "%" in expanded:
            continue
        if Path(expanded).is_file():
            return expanded
    raise ActionError(f"{app.name} is not installed or could not be found.")


def open_application(key: str) -> str:
    require_windows()
    app = APPLICATIONS.get(key)
    if app is None:
        raise ActionError("That application is not on the allowlist.")
    try:
        subprocess.Popen([_resolve_application(key)], shell=False)
    except OSError as exc:
        raise ActionError(f"Could not open {app.name}.") from exc
    return f"Opening {app.name}."


def open_directory(key: str, project_directory: str | None = None) -> str:
    require_windows()
    folders = {
        "downloads": Path.home() / "Downloads",
        "documents": Path.home() / "Documents",
        "desktop": Path.home() / "Desktop",
        "pictures": Path.home() / "Pictures",
        "project folder": Path(project_directory) if project_directory else Path(__file__).resolve().parents[1],
    }
    target = folders.get(key)
    if target is None:
        raise ActionError("That folder is not on the allowlist.")
    if not target.is_dir():
        raise ActionError(f"{target.name} could not be found.")
    try:
        os.startfile(str(target))
    except OSError as exc:
        raise ActionError(f"Could not open {target.name}.") from exc
    return f"Opening {target.name}."
