"""Small, local Settings dialog."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Callable

from config.settings import ConfigurationError, Settings


class SettingsDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        settings: Settings,
        on_save: Callable[[Settings], bool],
    ):
        super().__init__(parent)
        self.title("POVA Settings")
        self.geometry("620x700")
        self.minsize(560, 640)
        self.transient(parent)
        self.grab_set()
        self.settings = settings
        self.on_save = on_save
        self.configure(bg="#111827")
        self.columnconfigure(1, weight=1)
        self.vars: dict[str, tk.Variable] = {}
        self._build()

    def _build(self) -> None:
        style = ttk.Style(self)
        style.configure("Settings.TLabel", background="#111827", foreground="#f9fafb", font=("Segoe UI", 10))
        style.configure("Settings.TCheckbutton", background="#111827", foreground="#f9fafb")

        def entry(row: int, label: str, key: str, value: str, browse: bool = False) -> None:
            ttk.Label(self, text=label, style="Settings.TLabel").grid(row=row, column=0, sticky="w", padx=20, pady=8)
            variable = tk.StringVar(value=value)
            self.vars[key] = variable
            field = ttk.Entry(self, textvariable=variable)
            field.grid(row=row, column=1, sticky="ew", padx=(8, 10), pady=8)
            if browse:
                ttk.Button(self, text="Browse...", command=lambda: self._browse(variable)).grid(
                    row=row, column=2, padx=(0, 16), pady=8
                )

        ttk.Label(self, text="Voice backend", style="Settings.TLabel").grid(
            row=0, column=0, sticky="w", padx=20, pady=8
        )
        self.vars["voice_backend"] = tk.StringVar(value="Windows System.Speech")
        ttk.Combobox(
            self, textvariable=self.vars["voice_backend"],
            values=("Windows System.Speech",), state="readonly",
        ).grid(row=0, column=1, sticky="ew", padx=(8, 10), pady=8)
        ttk.Label(self, text="Microphone device (Windows default)", style="Settings.TLabel").grid(
            row=1, column=0, sticky="w", padx=20, pady=8
        )
        self.vars["microphone_device"] = tk.StringVar(value="Default")
        ttk.Combobox(
            self, textvariable=self.vars["microphone_device"],
            values=("Default",), state="readonly",
        ).grid(row=1, column=1, sticky="ew", padx=(8, 10), pady=8)
        entry(2, "Recognition timeout (2-30 sec)", "recognition_timeout", str(self.settings.recognition_timeout))
        entry(3, "Phrase duration (1-15 sec)", "phrase_duration", str(self.settings.phrase_duration))
        entry(4, "Wake word", "wake_word", self.settings.wake_word)
        entry(5, "Speech rate (-10 to 10)", "speech_rate", str(self.settings.speech_rate))
        entry(6, "Screenshot directory", "screenshot_directory", self.settings.screenshot_directory, True)
        entry(7, "Local Ollama endpoint", "ai_endpoint", self.settings.ai_endpoint)
        entry(8, "Ollama model", "ai_model", self.settings.ai_model)

        for row, label, key, initial in (
            (9, "Enable wake word", "wake_word_enabled", self.settings.wake_word_enabled),
            (10, "Speak responses", "voice_response_enabled", self.settings.voice_response_enabled),
            (11, "Keep command history for this session", "command_history_enabled", self.settings.command_history_enabled),
            (12, "Start listening automatically", "auto_start_listening", self.settings.auto_start_listening),
        ):
            variable = tk.BooleanVar(value=initial)
            self.vars[key] = variable
            ttk.Checkbutton(self, text=label, variable=variable, style="Settings.TCheckbutton").grid(
                row=row, column=0, columnspan=3, sticky="w", padx=20, pady=7
            )

        controls = ttk.Frame(self)
        controls.grid(row=13, column=0, columnspan=3, sticky="e", padx=20, pady=18)
        ttk.Button(controls, text="Cancel", command=self.destroy).pack(side="right", padx=(8, 0))
        ttk.Button(controls, text="Save Settings", command=self._save).pack(side="right")

    @staticmethod
    def _browse(variable: tk.StringVar) -> None:
        directory = filedialog.askdirectory(initialdir=variable.get() or None)
        if directory:
            variable.set(directory)

    def _save(self) -> None:
        try:
            updated = Settings(
                voice_backend=(
                    "windows"
                    if self.vars["voice_backend"].get() == "Windows System.Speech"
                    else ""
                ),
                microphone_device=str(self.vars["microphone_device"].get()).strip() or "Default",
                recognition_timeout=int(str(self.vars["recognition_timeout"].get())),
                phrase_duration=int(str(self.vars["phrase_duration"].get())),
                wake_word_enabled=bool(self.vars["wake_word_enabled"].get()),
                wake_word=str(self.vars["wake_word"].get()).strip(),
                voice_response_enabled=bool(self.vars["voice_response_enabled"].get()),
                speech_rate=int(str(self.vars["speech_rate"].get())),
                command_history_enabled=bool(self.vars["command_history_enabled"].get()),
                auto_start_listening=bool(self.vars["auto_start_listening"].get()),
                ai_endpoint=str(self.vars["ai_endpoint"].get()).strip(),
                ai_model=str(self.vars["ai_model"].get()).strip(),
                screenshot_directory=str(self.vars["screenshot_directory"].get()).strip(),
                project_directory=self.settings.project_directory,
            )
        except (ValueError, ConfigurationError) as exc:
            messagebox.showerror("Invalid settings", str(exc), parent=self)
            return
        if self.on_save(updated):
            self.destroy()
