"""Safe command processing and time-limited confirmation state."""

from __future__ import annotations

from dataclasses import dataclass, replace
import time
from typing import Callable

from config.commands import CONFIRMATION_INTENTS
from core.command_parser import is_confirmation, is_rejection, parse_command
from core.intent import ParsedCommand
from config.settings import Settings
from core.security import validate_command


@dataclass(frozen=True)
class AssistantResult:
    command: ParsedCommand
    response: str
    status: str


class Assistant:
    """Parse commands and dispatch only validated intents."""

    def __init__(
        self,
        action: Callable[[ParsedCommand], str],
        confirmation_timeout: int = 30,
        settings: Settings | None = None,
        state_callback: Callable[[str], None] | None = None,
    ):
        self._action = action
        self._confirmation_timeout = confirmation_timeout
        self._settings = settings or Settings()
        self._state_callback = state_callback or (lambda _state: None)
        self._pending: tuple[ParsedCommand, float] | None = None

    def process(self, text: str) -> AssistantResult:
        if self._pending:
            pending, expires = self._pending
            self._pending = None
            if time.monotonic() > expires:
                return AssistantResult(ParsedCommand("UNKNOWN"), "That confirmation expired. Please try again.", "CANCELLED")
            if is_confirmation(text, self._settings.wake_word):
                return self._execute(text, replace(pending, confirmed=True))
            if is_rejection(text, self._settings.wake_word):
                return AssistantResult(pending, "Okay, cancelled.", "CANCELLED")
            self._pending = (pending, expires)
            return AssistantResult(pending, "Please say yes or no.", "CONFIRMATION_REQUIRED")

        command = parse_command(
            text,
            wake_word_enabled=self._settings.wake_word_enabled,
            wake_word=self._settings.wake_word,
        )
        if command.intent == "UNKNOWN":
            return AssistantResult(command, "I didn't understand that command.", "UNKNOWN")
        if command.intent == "WAKE_WORD":
            return AssistantResult(command, "Yes, how can I help?", "SUCCESS")
        if command.intent in CONFIRMATION_INTENTS:
            self._pending = (command, time.monotonic() + self._confirmation_timeout)
            messages = {
                "SHUTDOWN": "Are you sure you want to shut down the computer?",
                "RESTART": "Are you sure you want to restart the computer?",
                "SLEEP": "Are you sure you want to put the computer to sleep?",
                "HIBERNATE": "Are you sure you want to hibernate the computer?",
            }
            return AssistantResult(command, messages[command.intent], "CONFIRMATION_REQUIRED")
        return self._execute(text, command)

    def _execute(self, text: str, command: ParsedCommand) -> AssistantResult:
        self._state_callback("EXECUTING")
        try:
            validate_command(command)
            return AssistantResult(command, self._action(command), "SUCCESS")
        except Exception as exc:
            from actions import ActionError
            from core.security import CommandError

            if isinstance(exc, (ActionError, CommandError)):
                return AssistantResult(command, str(exc), "ERROR")
            raise

    def cancel_pending(self) -> None:
        self._pending = None
