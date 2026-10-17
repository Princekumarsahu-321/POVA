"""Structured representation of a recognized, allowlisted command."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ParsedCommand:
    intent: str
    target: str | None = None
    display_name: str | None = None
    requires_confirmation: bool = False
    confirmed: bool = False
