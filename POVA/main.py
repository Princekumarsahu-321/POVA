"""POVA desktop application entry point."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from actions import ActionError, execute
from command import ParsedCommand, is_confirmation, is_rejection, parse_command
from config import APP_NAME, APP_SUBTITLE
from voice import Voice, VoiceError


@dataclass
class HistoryItem:
    time: str
    user: str
    action: str
    status: str


class PovaApp:
    BG = "#111827"
    PANEL = "#1f2937"
    TEXT = "#f9fafb"
    MUTED = "#9ca3af"
    ACCENT = "#38bdf8"

    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"{APP_NAME} - {APP_SUBTITLE}")
        self.root.geometry("820x760")
        self.root.minsize(650, 560)
        self.root.configure(bg=self.BG)
        icon = Path(__file__).resolve().parent / "assets" / "pova_icon.ico"
        if icon.exists():
            self.root.iconbitmap(str(icon))
        self.events: queue.Queue = queue.Queue()
        self.voice = Voice(lambda message: self.events.put(("status", message)))
        self.listener_thread = None
        self.pending_confirmation: ParsedCommand | None = None
        self.history: list[HistoryItem] = []
        self._build_ui()
        self.root.after(100, self._drain_events)
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def _build_ui(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TButton", padding=8, font=("Segoe UI", 10))
        style.configure("Treeview", background=self.PANEL, fieldbackground=self.PANEL, foreground=self.TEXT, rowheight=28)
        header = tk.Frame(self.root, bg=self.BG)
        header.pack(fill="x", padx=28, pady=(24, 10))
        tk.Label(header, text="P O V A", font=("Segoe UI", 30, "bold"), fg=self.ACCENT, bg=self.BG).pack()
        tk.Label(header, text=APP_SUBTITLE, font=("Segoe UI", 11), fg=self.MUTED, bg=self.BG).pack()

        self.status = tk.Label(self.root, text="● Ready", font=("Segoe UI", 12, "bold"), fg=self.ACCENT, bg=self.BG)
        self.status.pack(pady=8)
        panel = tk.Frame(self.root, bg=self.PANEL, padx=22, pady=18)
        panel.pack(fill="x", padx=28, pady=10)
        self.you_value = self._value_row(panel, "You")
        self.action_value = self._value_row(panel, "Detected Action")
        self.response_value = self._value_row(panel, "POVA")

        # Keep controls above the expanding history table so the buttons remain visible.
        controls = tk.Frame(self.root, bg=self.BG)
        controls.pack(fill="x", padx=28, pady=(14, 10))
        self.listen_button = ttk.Button(controls, text="Start Listening", command=self.toggle_listening)
        self.listen_button.pack(side="left")
        ttk.Button(controls, text="Clear History", command=self.clear_history).pack(side="right")

        tk.Label(self.root, text="Command History", font=("Segoe UI", 13, "bold"), fg=self.TEXT, bg=self.BG).pack(anchor="w", padx=28, pady=(8, 6))
        self.history_view = ttk.Treeview(self.root, columns=("time", "user", "action", "status"), show="headings")
        for key, title, width in (("time", "Time", 80), ("user", "Command", 260), ("action", "Action", 180), ("status", "Status", 120)):
            self.history_view.heading(key, text=title)
            self.history_view.column(key, width=width, anchor="w")
        self.history_view.pack(fill="both", expand=True, padx=28, pady=(0, 18))

    def _value_row(self, parent, label):
        row = tk.Frame(parent, bg=self.PANEL)
        row.pack(fill="x", pady=5)
        tk.Label(row, text=f"{label}:", width=16, anchor="w", fg=self.MUTED, bg=self.PANEL, font=("Segoe UI", 10, "bold")).pack(side="left")
        value = tk.Label(row, text="—", anchor="w", justify="left", wraplength=570, fg=self.TEXT, bg=self.PANEL, font=("Segoe UI", 11))
        value.pack(side="left", fill="x", expand=True)
        return value

    def toggle_listening(self):
        if self.listener_thread and self.listener_thread.is_alive():
            self.voice.stop()
            self.listen_button.configure(text="Start Listening")
            self.status.configure(text="● Stopped", fg=self.MUTED)
            return
        self.listener_thread = threading.Thread(target=self.voice.run, args=(self._received_text,), daemon=True)
        self.listener_thread.start()
        self.listen_button.configure(text="Stop Listening")

    def _received_text(self, text):
        self.events.put(("command", text))

    def _drain_events(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == "status":
                    self.status.configure(text=f"● {value}")
                elif kind == "command":
                    self.process_text(value)
        except queue.Empty:
            pass
        self.root.after(100, self._drain_events)

    def process_text(self, text: str):
        if self.pending_confirmation:
            if is_confirmation(text):
                parsed = self.pending_confirmation
                self.pending_confirmation = None
                self._execute(text, parsed)
            elif is_rejection(text):
                self.pending_confirmation = None
                self._show_result(text, "CANCELLED", "Okay, cancelled.")
            else:
                self._show_result(text, "CONFIRMATION_REQUIRED", "Please say yes or no.")
            return
        parsed = parse_command(text)
        if parsed.intent == "WAKE_WORD":
            self._show_result(text, "WAKE_WORD", "Yes, how can I help?")
            self._speak("Yes, how can I help?")
        elif parsed.intent == "UNKNOWN":
            self._show_result(text, "UNKNOWN", "I didn't understand that command.")
            self._speak("I didn't understand that command.")
        elif parsed.requires_confirmation:
            self.pending_confirmation = parsed
            response = "Are you sure you want to do that?"
            self._show_result(text, parsed.intent, response)
            self._speak(response)
        else:
            self._execute(text, parsed)

    def _execute(self, text, parsed):
        try:
            response = execute(parsed)
            self._show_result(text, parsed.intent + (f" → {parsed.target.upper()}" if parsed.target else ""), response)
            self._speak(response)
        except ActionError as exc:
            self._show_result(text, parsed.intent, str(exc), "ERROR")
            self._speak(str(exc))

    def _show_result(self, text, action, response, status="SUCCESS"):
        self.you_value.configure(text=text)
        self.action_value.configure(text=action)
        self.response_value.configure(text=response)
        item = HistoryItem(datetime.now().strftime("%H:%M:%S"), text, action, status)
        self.history.append(item)
        self.history_view.insert("", "end", values=(item.time, item.user, item.action, item.status))

    def _speak(self, text):
        threading.Thread(target=self.voice.speak, args=(text,), daemon=True).start()

    def clear_history(self):
        self.history.clear()
        for item in self.history_view.get_children():
            self.history_view.delete(item)

    def close(self):
        self.voice.stop()
        self.root.destroy()


def main():
    root = tk.Tk()
    PovaApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
