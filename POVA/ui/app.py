"""POVA desktop application and Tkinter-thread orchestration."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import logging
import os
from pathlib import Path
import queue
import tkinter as tk
from tkinter import messagebox

from actions import execute
from config.settings import ConfigurationError, Settings, load_settings, save_settings
from core.ai_chat import ChatError, ChatMessage, OllamaChatClient
from core.assistant import Assistant, AssistantResult
from ui.dashboard import Dashboard
from ui.chat import ChatWindow
from ui.settings import SettingsDialog
from utils.logger import configure_logging
from voice.voice_manager import VoiceManager


LOGGER = logging.getLogger("pova")


class PovaApp:
    def __init__(self, root: tk.Tk, settings: Settings | None = None):
        self.root = root
        self.settings = settings or load_settings()
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="pova-worker")
        self._closed = False
        self._listening = False
        self._chat_window: ChatWindow | None = None
        self.voice = VoiceManager(self.settings, self._voice_status)
        self.assistant = Assistant(
            lambda command: execute(
                command,
                screenshot_directory=self.settings.screenshot_directory,
                project_directory=self.settings.project_directory,
            ),
            settings=self.settings,
            state_callback=lambda state: self.events.put(("status", state)),
        )
        self.root.title("POVA - Personal Operating Voice Assistant")
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)
        icon = Path(__file__).resolve().parents[1] / "assets" / "pova_icon.ico"
        if icon.is_file():
            try:
                self.root.iconbitmap(str(icon))
            except tk.TclError:
                LOGGER.warning("Could not load the application icon.")
        self.dashboard = Dashboard(
            self.root,
            self.settings,
            {
                "toggle_listening": self.toggle_listening,
                "stop_listening": self.stop_listening,
                "test_microphone": self.test_microphone,
                "settings": self.open_settings,
                "clear_history": self.clear_history,
                "show_commands": self.show_commands,
                "ai_chat": self.open_chat,
            },
        )
        self.dashboard.response_text.set(
            "Hii Sir! Welcome to POVA. " + (
                "Windows speech recognition is available. Test your microphone before listening."
                if self.voice.available
                else "Microphone setup required. POVA voice control requires Windows 10 or 11."
            )
        )
        if os.name == "nt":
            self.voice.speak("Hii Sir. Welcome to POVA.")
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self._drain_events)
        LOGGER.info("POVA application started; voice backend: Windows System.Speech.")
        if os.name != "nt":
            self.dashboard.set_status("ERROR: POVA currently supports Windows 10 and Windows 11.")
        if self.settings.auto_start_listening:
            self.root.after(500, self.toggle_listening)

    def _voice_status(self, value: str) -> None:
        self.events.put(("voice_status", value))

    def toggle_listening(self) -> None:
        if self._listening:
            self.stop_listening()
            return
        self._listening = True
        self.voice.start_listening()
        self.dashboard.listen_button.configure(text="Listening...")
        self.events.put(("status", "LISTENING"))
        self.executor.submit(self.voice.run, lambda text: self.events.put(("command", text)))

    def stop_listening(self) -> None:
        if self._listening:
            self._listening = False
            self.voice.stop_listening()
            self.dashboard.listen_button.configure(text="Start Listening")
            self.events.put(("status", "STOPPED"))

    def test_microphone(self) -> None:
        if self._listening:
            self.dashboard.response_text.set("Stop listening before testing the microphone.")
            return
        self.events.put(("status", "RECOGNIZING"))
        self.executor.submit(self._test_microphone_worker)

    def _test_microphone_worker(self) -> None:
        try:
            recognized = self.voice.test_microphone()
            self.events.put(("microphone_test", recognized))
        except Exception as exc:
            LOGGER.warning("Microphone test failed: %s", exc)
            self.events.put(("microphone_error", str(exc)))

    def _process_command(self, text: str) -> None:
        self.events.put(("status", "PROCESSING"))
        try:
            result = self.assistant.process(text)
            self.events.put(("result", (text, result)))
        except Exception:
            LOGGER.exception("Unexpected error while processing an assistant command.")
            from core.intent import ParsedCommand

            failed = AssistantResult(ParsedCommand("UNKNOWN"), "POVA could not process that command. Please try again.", "ERROR")
            self.events.put(("result", (text, failed)))

    def _drain_events(self) -> None:
        if self._closed:
            return
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "command":
                    LOGGER.info("Recognized voice command; processing through allowlist.")
                    self.executor.submit(self._process_command, str(value))
                elif kind == "status":
                    self.dashboard.set_status(str(value))
                elif kind == "voice_status":
                    status = str(value)
                    if status.startswith("ERROR:"):
                        self.dashboard.set_status(status)
                        self.dashboard.response_text.set(status.split(":", 1)[1])
                    elif status.startswith("VOICE_ERROR:"):
                        self.dashboard.response_text.set(status.split(":", 1)[1])
                    elif status in {"LISTENING", "RECOGNIZING", "PROCESSING", "EXECUTING", "SPEAKING", "IDLE"}:
                        if self._listening or status == "IDLE":
                            self.dashboard.set_status(status)
                elif kind == "microphone_test":
                    self.dashboard.set_status("READY")
                    self.dashboard.response_text.set(f"Microphone working. Recognized: “{value}”")
                elif kind == "microphone_error":
                    self.dashboard.set_status("ERROR")
                    self.dashboard.response_text.set(str(value))
                elif kind == "result":
                    text, result = value  # type: ignore[misc]
                    self._display_result(text, result)
                elif kind == "chat_result":
                    window, response, error = value  # type: ignore[misc]
                    if self._chat_window is window:
                        window.complete(response=response, error=error)
        except queue.Empty:
            pass
        self.root.after(100, self._drain_events)

    def _display_result(self, text: str, result: AssistantResult) -> None:
        command = result.command
        action = command.intent
        if command.target:
            action += f" → {command.target.upper()}"
        self.dashboard.user_text.set(text)
        self.dashboard.action_text.set(action)
        self.dashboard.response_text.set(result.response)
        if self.settings.command_history_enabled:
            self.dashboard.history.add(text, action, result.status)
        status = "ERROR" if result.status == "ERROR" and not self._listening else (
            "LISTENING" if self._listening else "READY"
        )
        self.dashboard.set_status(status)
        if result.status == "ERROR":
            LOGGER.warning("Action failed: %s", result.response)
        else:
            LOGGER.info("Intent processed: %s (%s).", command.intent, result.status)
        self.voice.speak(result.response)

    def clear_history(self) -> None:
        self.dashboard.history.clear()

    def open_chat(self) -> None:
        if self._chat_window is not None:
            try:
                if self._chat_window.winfo_exists():
                    self._chat_window.lift()
                    return
            except tk.TclError:
                self._chat_window = None
        window: ChatWindow
        window = ChatWindow(self.root, lambda messages: self._submit_chat(window, messages))
        self._chat_window = window

    def _submit_chat(self, window: ChatWindow, messages: list[ChatMessage]) -> None:
        self.executor.submit(self._chat_worker, window, messages, self.settings)

    def _chat_worker(
        self, window: ChatWindow, messages: list[ChatMessage], settings: Settings,
    ) -> None:
        try:
            response = OllamaChatClient(settings).reply(messages)
            self.events.put(("chat_result", (window, response, None)))
        except ChatError as exc:
            self.events.put(("chat_result", (window, None, str(exc))))
        except Exception:
            LOGGER.exception("Unexpected error while requesting a local AI response.")
            self.events.put((
                "chat_result",
                (window, None, "POVA could not get a reply. Check the log and try again."),
            ))

    def show_commands(self) -> None:
        window = tk.Toplevel(self.root)
        window.title("POVA command guide")
        window.configure(bg="#0b1020")
        window.resizable(False, False)
        window.transient(self.root)
        window.grab_set()
        tk.Label(
            window, text="Commands you can say", font=("Segoe UI", 16, "bold"),
            fg="#f4f7fb", bg="#0b1020",
        ).pack(anchor="w", padx=22, pady=(20, 4))
        tk.Label(
            window, text="POVA only performs the fixed, allowlisted actions below.",
            font=("Segoe UI", 9), fg="#91a0b8", bg="#0b1020",
        ).pack(anchor="w", padx=22, pady=(0, 14))
        examples = (
            "APPS & SITES\n"
            "Open Notepad  •  Open Calculator  •  Open VS Code\n"
            "Open Chrome  •  Open YouTube  •  Open GitHub\n\n"
            "FOLDERS & WINDOWS\n"
            "Open Downloads  •  Open Documents  •  Open Desktop\n"
            "Lock Windows  •  Show desktop  •  Open Settings\n"
            "Take a screenshot\n\n"
            "MEDIA & INFORMATION\n"
            "Volume up  •  Volume down  •  Mute  •  Unmute\n"
            "Play  •  Pause  •  Next track  •  Previous track\n"
            "What time is it?  •  What is today's date?\n\n"
            "POWER (ALWAYS ASKS FOR CONFIRMATION)\n"
            "Shutdown  •  Restart  •  Sleep  •  Hibernate"
        )
        guide = tk.Text(
            window, width=64, height=18, wrap="word", relief="flat",
            bg="#151f33", fg="#dce6f2", insertbackground="#dce6f2",
            font=("Segoe UI", 10), padx=16, pady=14,
        )
        guide.insert("1.0", examples)
        guide.configure(state="disabled")
        guide.pack(fill="both", expand=True, padx=22, pady=(0, 18))
        tk.Button(
            window, text="Done", command=window.destroy, font=("Segoe UI", 9, "bold"),
            fg="#06212a", bg="#49d7e8", activebackground="#78e6ef",
            relief="flat", bd=0, padx=18, pady=8,
        ).pack(anchor="e", padx=22, pady=(0, 20))

    def open_settings(self) -> None:
        SettingsDialog(self.root, self.settings, self._save_settings)

    def _save_settings(self, settings: Settings) -> bool:
        try:
            save_settings(settings)
        except ConfigurationError as exc:
            messagebox.showerror("Settings could not be saved", str(exc), parent=self.root)
            return False
        self.stop_listening()
        self.voice.stop()
        self.settings = settings
        self.voice = VoiceManager(settings, self._voice_status)
        self.assistant = Assistant(
            lambda command: execute(
                command,
                screenshot_directory=self.settings.screenshot_directory,
                project_directory=self.settings.project_directory,
            ),
            settings=settings,
            state_callback=lambda state: self.events.put(("status", state)),
        )
        self.dashboard.update_settings(settings)
        self.dashboard.response_text.set("Settings saved.")
        if settings.auto_start_listening:
            self.root.after(500, self.toggle_listening)
        return True

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self.voice.stop()
        self.executor.shutdown(wait=False, cancel_futures=True)
        LOGGER.info("POVA application stopped.")
        self.root.destroy()


def main() -> None:
    logger = configure_logging()
    root: tk.Tk | None = None
    try:
        settings = load_settings()
    except ConfigurationError as exc:
        logger.error("Invalid configuration: %s", exc)
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "POVA Settings Error",
            f"{exc}\n\nPOVA will open with safe default settings for this session.",
            parent=root,
        )
        settings = Settings()
    try:
        if root is None:
            root = tk.Tk()
        root.deiconify()
        PovaApp(root, settings)
        root.mainloop()
    except tk.TclError as exc:
        logger.exception("Could not initialize the POVA interface.")
        raise RuntimeError(f"POVA could not open its desktop window: {exc}") from exc


if __name__ == "__main__":
    main()
