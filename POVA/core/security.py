"""Validation boundary between parsed speech and executable actions."""

from config.commands import APPLICATIONS, COMMANDS, CONFIRMATION_INTENTS, DIRECTORIES, WEBSITES
from core.intent import ParsedCommand


class CommandError(RuntimeError):
    """Raised when an intent is not valid for the action allowlist."""


def validate_command(command: ParsedCommand) -> ParsedCommand:
    if command.intent not in COMMANDS:
        raise CommandError("This command is not supported.")
    if command.intent == "OPEN_APPLICATION" and command.target not in APPLICATIONS:
        raise CommandError("That application is not on the allowlist.")
    if command.intent == "OPEN_WEBSITE" and command.target not in WEBSITES:
        raise CommandError("That website is not on the allowlist.")
    if command.intent == "OPEN_DIRECTORY" and command.target not in DIRECTORIES:
        raise CommandError("That folder is not on the allowlist.")
    if command.intent in CONFIRMATION_INTENTS and (
        not command.requires_confirmation or not command.confirmed
    ):
        raise CommandError("This action must be confirmed before it can run.")
    if command.intent not in {"OPEN_APPLICATION", "OPEN_WEBSITE", "OPEN_DIRECTORY"} and command.target:
        raise CommandError("This command contains an unexpected target.")
    return command
