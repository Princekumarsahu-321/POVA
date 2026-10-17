"""Confirmed Windows power operations."""

import ctypes
import subprocess

from actions.system_actions import require_windows
from actions import ActionError


def power_action(intent: str) -> str:
    require_windows()
    if intent == "SHUTDOWN":
        command = ["shutdown.exe", "/s", "/t", "5"]
        message = "Shutting down in five seconds."
    elif intent == "RESTART":
        command = ["shutdown.exe", "/r", "/t", "5"]
        message = "Restarting in five seconds."
    elif intent in {"SLEEP", "HIBERNATE"}:
        hibernate = intent == "HIBERNATE"
        try:
            result = ctypes.windll.powrprof.SetSuspendState(hibernate, False, False)
        except (AttributeError, OSError) as exc:
            raise ActionError("Windows could not enter the requested power state.") from exc
        if result == 0:
            raise ActionError("Windows could not enter the requested power state.")
        return "Hibernating Windows." if hibernate else "Putting Windows to sleep."
    else:
        raise ActionError("That power action is not supported.")
    try:
        subprocess.Popen(command, shell=False)
    except OSError as exc:
        raise ActionError("Windows could not start the requested power action.") from exc
    return message
