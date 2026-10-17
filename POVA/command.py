"""Compatibility exports for the modular command parser."""

from core.command_parser import is_confirmation, is_rejection, normalize_text, parse_command, remove_wake_word
from core.intent import ParsedCommand

__all__ = [
    "ParsedCommand", "is_confirmation", "is_rejection", "normalize_text",
    "parse_command", "remove_wake_word",
]
