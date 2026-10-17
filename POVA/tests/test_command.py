from core.command_parser import (
    is_confirmation, is_rejection, normalize_text, parse_command, remove_wake_word,
)


def test_normalize_and_remove_wake_word():
    assert normalize_text("  Hey POVA,  OPEN   Notepad! ") == "hey pova open notepad"
    assert remove_wake_word("Hey POVA, open notepad.") == "open notepad"


def test_supported_command_intents():
    cases = {
        "Open Notepad": ("OPEN_APPLICATION", "notepad"),
        "Launch Calculator": ("OPEN_APPLICATION", "calculator"),
        "Open Chrome": ("OPEN_APPLICATION", "chrome"),
        "Open YouTube": ("OPEN_WEBSITE", "youtube"),
        "Lock Windows": ("LOCK_WINDOWS", None),
        "Take a screenshot": ("TAKE_SCREENSHOT", None),
        "Volume Up": ("VOLUME_UP", None),
        "Volume Down": ("VOLUME_DOWN", None),
        "Mute": ("MUTE_VOLUME", None),
        "What time is it?": ("TIME", None),
        "Tell me today's date": ("DATE", None),
        "Shutdown my PC": ("SHUTDOWN", None),
        "Restart": ("RESTART", None),
        "Open Downloads": ("OPEN_DIRECTORY", "downloads"),
        "Play": ("MEDIA_PLAY_PAUSE", None),
        "Open Windows Settings": ("OPEN_SETTINGS", None),
    }
    for phrase, (intent, target) in cases.items():
        result = parse_command(phrase)
        assert (result.intent, result.target) == (intent, target), phrase


def test_wake_word_and_manual_listening():
    assert parse_command("Hey POVA, open Notepad").target == "notepad"
    assert parse_command("open notepad", wake_word_enabled=False).target == "notepad"
    assert parse_command("POVA", wake_word_enabled=False).intent == "UNKNOWN"


def test_confirmation_words():
    assert is_confirmation("Yes")
    assert is_confirmation("do it")
    assert is_rejection("don't do it")
    assert is_rejection("Cancel")


def test_power_commands_are_marked_for_confirmation():
    assert parse_command("Shutdown").requires_confirmation
    assert parse_command("Restart").requires_confirmation
    assert parse_command("Sleep").requires_confirmation
    assert parse_command("Hibernate").requires_confirmation
