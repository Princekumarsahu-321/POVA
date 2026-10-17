"""POVA's dark desktop dashboard."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from config.settings import Settings
from ui.history import HistoryView


BG = "#071016"
PANEL = "#0a151d"
PANEL_LIGHT = "#10232d"
TEXT = "#e7fbff"
MUTED = "#82a5b1"
ACCENT = "#45e6f5"
PURPLE = "#c66cff"
GREEN = "#55e7c1"


class Dashboard:
    def __init__(
        self,
        root: tk.Tk,
        settings: Settings,
        callbacks: dict[str, Callable[[], None]],
    ):
        self.root = root
        self.root.configure(bg=BG)
        self._callbacks = callbacks
        self._pulse = 0
        self._active = False
        self.status = tk.StringVar(value="READY")
        self.user_text = tk.StringVar(value="Waiting for your first command")
        self.action_text = tk.StringVar(value="No action yet")
        self.response_text = tk.StringVar(value="Hello! I’m POVA. Press the microphone button when you’re ready.")
        self.visualizer_title = tk.StringVar(value="VOICE VISUALIZER · STANDBY")
        self._configure_style()
        self._build()
        self.update_settings(settings)
        self._animate_orb()

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(
            "POVA.Treeview", background=PANEL, fieldbackground=PANEL,
            foreground=TEXT, rowheight=32, borderwidth=0, font=("Segoe UI", 9),
        )
        style.configure(
            "POVA.Treeview.Heading", background=PANEL_LIGHT, foreground=TEXT,
            font=("Segoe UI", 9, "bold"), relief="flat",
        )
        style.map("POVA.Treeview", background=[("selected", "#164e63")])
        style.configure(
            "POVA.Vertical.TScrollbar", background=PANEL_LIGHT,
            troughcolor=PANEL, bordercolor=PANEL,
        )

    def _build(self) -> None:
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=0)
        self.root.rowconfigure(1, weight=4)
        self.root.rowconfigure(2, weight=2)

        header = tk.Frame(self.root, bg=BG)
        header.grid(row=0, column=0, sticky="ew", padx=30, pady=(20, 10))
        header.columnconfigure(0, weight=1)
        tk.Label(
            header, text="P O V A", font=("Segoe UI", 24, "bold"),
            fg=ACCENT, bg=BG,
        ).grid(row=0, column=0, sticky="n")
        tk.Label(
            header, text="PERSONAL OPERATING VOICE ASSISTANT",
            font=("Segoe UI", 8, "bold"), fg=MUTED, bg=BG,
        ).grid(row=1, column=0, sticky="n", pady=(1, 0))
        self.status_label = tk.Label(
            header, textvariable=self.status, font=("Segoe UI", 9, "bold"),
            fg=GREEN, bg="#102c2c", padx=12, pady=7,
        )
        self.status_label.grid(row=0, column=1, rowspan=2, sticky="e")

        frame = tk.Frame(self.root, bg="#12404a", padx=2, pady=2)
        frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 14))
        frame.columnconfigure(0, weight=3)
        frame.columnconfigure(1, weight=2)
        frame.rowconfigure(0, weight=1)
        screen = tk.Frame(frame, bg="#03090e", padx=22, pady=18)
        screen.grid(row=0, column=0, columnspan=2, sticky="nsew")
        screen.columnconfigure(0, weight=3)
        screen.columnconfigure(1, weight=2)
        screen.rowconfigure(0, weight=1)

        assistant_panel = tk.Frame(screen, bg="#03090e")
        assistant_panel.grid(row=0, column=0, sticky="nsew", padx=(4, 18))
        assistant_panel.columnconfigure(0, weight=1)
        assistant_panel.rowconfigure(1, weight=1)
        tk.Label(
            assistant_panel, text="◆  POVA VOICE ASSISTANT",
            font=("Segoe UI", 9, "bold"), fg=ACCENT, bg="#03090e",
        ).grid(row=0, column=0, sticky="w", pady=(4, 2))
        self.orb = tk.Canvas(
            assistant_panel, width=290, height=255, bg="#03090e",
            highlightthickness=0,
        )
        self.orb.grid(row=1, column=0, sticky="nsew", pady=(3, 0))
        tk.Label(
            assistant_panel, text="POVA", font=("Segoe UI", 16, "bold"),
            fg=ACCENT, bg="#03090e",
        ).grid(row=2, column=0, sticky="n")
        tk.Label(
            assistant_panel, text="Hi! How can I help you today?",
            font=("Segoe UI", 9), fg="#a8d9e1", bg="#03090e",
        ).grid(row=3, column=0, sticky="new", pady=(2, 0))

        widgets = tk.Frame(screen, bg="#03090e")
        widgets.grid(row=0, column=1, sticky="nsew")
        widgets.columnconfigure(0, weight=1)
        widgets.rowconfigure(0, weight=1)
        widgets.rowconfigure(1, weight=2)
        widgets.rowconfigure(2, weight=1)

        audio_card = self._card(widgets, 0, self.visualizer_title)
        self.waveform = tk.Canvas(
            audio_card, height=62, bg=PANEL, highlightthickness=0,
        )
        self.waveform.pack(fill="x", padx=10, pady=(2, 7))
        self.waveform.bind("<Configure>", lambda _event: self._draw_waveform())

        command_card = self._card(widgets, 1, "LATEST COMMAND")
        self._detail(command_card, "HEARD", self.user_text)
        self._detail(command_card, "ACTION", self.action_text)
        response_label = tk.Label(
            command_card, textvariable=self.response_text, font=("Segoe UI", 9),
            fg=TEXT, bg=PANEL, anchor="nw", justify="left", wraplength=400,
        )
        response_label.pack(fill="both", expand=True, padx=11, pady=(6, 10))

        voice_card = self._card(widgets, 2, "VOICE STATUS")
        state = tk.Frame(voice_card, bg=PANEL)
        state.pack(fill="x", padx=11, pady=(1, 9))
        self.status_dot = tk.Label(
            state, text="●", font=("Segoe UI", 14), fg=GREEN, bg=PANEL,
        )
        self.status_dot.pack(side="left", padx=(0, 8))
        tk.Label(
            state, textvariable=self.status, font=("Segoe UI", 10, "bold"),
            fg=GREEN, bg=PANEL,
        ).pack(side="left")

        toolbar = tk.Frame(self.root, bg=BG)
        toolbar.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 16))
        toolbar.columnconfigure(0, weight=1)
        toolbar.rowconfigure(1, weight=1)
        controls = tk.Frame(toolbar, bg=BG)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.listen_button = tk.Button(
            controls, text="Start listening", command=self._callbacks["toggle_listening"],
            font=("Segoe UI", 9, "bold"), fg="#031115", bg=ACCENT,
            activebackground="#82f4fb", activeforeground="#031115",
            relief="flat", bd=0, padx=15, pady=8, cursor="hand2",
        )
        self.listen_button.pack(side="left", padx=(0, 7))
        self._secondary_button(
            controls, "Test microphone", self._callbacks["test_microphone"],
        ).pack(side="left", padx=(0, 7))
        for label, callback in (
            ("Settings", self._callbacks["settings"]),
            ("AI Chat", self._callbacks["ai_chat"]),
            ("Commands", self._callbacks["show_commands"]),
        ):
            self._secondary_button(controls, label, callback).pack(side="right", padx=(7, 0))

        activity = tk.Frame(toolbar, bg=BG)
        activity.grid(row=1, column=0, sticky="nsew")
        activity.columnconfigure(0, weight=1)
        activity.rowconfigure(1, weight=1)
        history_header = tk.Frame(activity, bg=BG)
        history_header.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        history_header.columnconfigure(0, weight=1)
        tk.Label(
            history_header, text="COMMAND HISTORY", font=("Segoe UI", 9, "bold"),
            fg="#a8d9e1", bg=BG,
        ).grid(row=0, column=0, sticky="w")
        clear_button = tk.Label(
            history_header, text="Clear", font=("Segoe UI", 9),
            fg=ACCENT, bg=BG, cursor="hand2",
        )
        clear_button.grid(row=0, column=1, sticky="e")
        clear_button.bind("<Button-1>", lambda _event: self._callbacks["clear_history"]())
        self.history = HistoryView(activity)
        self.history.table.configure(style="POVA.Treeview", height=4)
        self.history.table.grid(row=1, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            activity, orient="vertical", command=self.history.table.yview,
            style="POVA.Vertical.TScrollbar",
        )
        scrollbar.grid(row=1, column=1, sticky="ns")
        self.history.table.configure(yscrollcommand=scrollbar.set)

    def _card(self, parent: tk.Frame, row: int, title: str | tk.StringVar) -> tk.Frame:
        shell = tk.Frame(parent, bg="#174753", padx=1, pady=1)
        shell.grid(row=row, column=0, sticky="nsew", pady=(0, 9))
        shell.columnconfigure(0, weight=1)
        card = tk.Frame(shell, bg=PANEL, padx=10, pady=7)
        card.pack(fill="both", expand=True)
        heading = {"textvariable": title} if isinstance(title, tk.StringVar) else {"text": title}
        tk.Label(card, **heading, font=("Segoe UI", 8, "bold"), fg="#8ecbd4", bg=PANEL).pack(
            anchor="w", pady=(0, 4),
        )
        return card

    @staticmethod
    def _detail(parent: tk.Frame, label: str, value: tk.StringVar) -> None:
        row = tk.Frame(parent, bg=PANEL)
        row.pack(fill="x", padx=11, pady=3)
        tk.Label(
            row, text=label, width=8, anchor="w", font=("Segoe UI", 8, "bold"),
            fg=MUTED, bg=PANEL,
        ).pack(side="left", anchor="n")
        tk.Label(
            row, textvariable=value, font=("Segoe UI", 9), fg=TEXT, bg=PANEL,
            anchor="w", justify="left", wraplength=300,
        ).pack(side="left", fill="x", expand=True)

    @staticmethod
    def _secondary_button(
        parent: tk.Frame, text: str, command: Callable[[], None],
    ) -> tk.Button:
        return tk.Button(
            parent, text=text, command=command, font=("Segoe UI", 9, "bold"),
            fg=TEXT, bg=PANEL_LIGHT, activebackground="#1b3b48",
            activeforeground=TEXT, relief="flat", bd=0, padx=13, pady=10,
            cursor="hand2",
        )

    def _animate_orb(self) -> None:
        if not self.root.winfo_exists():
            return
        self._pulse = (self._pulse + 1) % 32
        width = max(self.orb.winfo_width(), 180)
        height = max(self.orb.winfo_height(), 180)
        center_x = width / 2
        center_y = height / 2
        radius_x = min(width * 0.31, height * 0.36)
        radius_y = min(width * 0.31, height * 0.38)
        active = self._active
        pulse = self._pulse % 5 if active else 0
        self.orb.delete("all")
        for offset in (0, 9, 18):
            self.orb.create_oval(
                center_x - radius_x - offset - pulse,
                center_y - radius_y - offset - pulse,
                center_x + radius_x + offset + pulse,
                center_y + radius_y + offset + pulse,
                outline=("#123b48" if offset else "#247b88") if active else (
                    "#102a35" if offset else "#194753"
                ),
                width=2 if offset == 0 else 1,
            )
        head = [
            center_x - radius_x, center_y - radius_y * 0.70,
            center_x - radius_x * 0.68, center_y - radius_y,
            center_x + radius_x * 0.68, center_y - radius_y,
            center_x + radius_x, center_y - radius_y * 0.70,
            center_x + radius_x, center_y + radius_y * 0.60,
            center_x + radius_x * 0.70, center_y + radius_y,
            center_x - radius_x * 0.70, center_y + radius_y,
            center_x - radius_x, center_y + radius_y * 0.60,
        ]
        self.orb.create_polygon(
            head, smooth=True, splinesteps=24, fill="#14203a",
            outline=PURPLE, width=4,
        )
        face = [
            center_x - radius_x * 0.84, center_y - radius_y * 0.57,
            center_x - radius_x * 0.58, center_y - radius_y * 0.78,
            center_x + radius_x * 0.58, center_y - radius_y * 0.78,
            center_x + radius_x * 0.84, center_y - radius_y * 0.57,
            center_x + radius_x * 0.84, center_y + radius_y * 0.47,
            center_x + radius_x * 0.55, center_y + radius_y * 0.76,
            center_x - radius_x * 0.55, center_y + radius_y * 0.76,
            center_x - radius_x * 0.84, center_y + radius_y * 0.47,
        ]
        self.orb.create_polygon(
            face, smooth=True, splinesteps=24, fill="#080d24",
            outline="#41deef", width=2,
        )
        pad_width = max(7, radius_x * 0.14)
        for side in (-1, 1):
            x = center_x + side * radius_x * 0.98
            self.orb.create_rectangle(
                x - pad_width / 2, center_y - radius_y * 0.25,
                x + pad_width / 2, center_y + radius_y * 0.31,
                fill="#38d7ed", outline="#9d7aff", width=2,
            )
        eye_y = center_y - radius_y * 0.12
        for side in (-1, 1):
            x = center_x + side * radius_x * 0.36
            self.orb.create_arc(
                x - radius_x * 0.18, eye_y - radius_y * 0.17,
                x + radius_x * 0.18, eye_y + radius_y * 0.20,
                start=20, extent=140, style="arc",
                outline="#59f3fa", width=4,
            )
        mouth_y = center_y + radius_y * 0.31
        points = []
        for index, height_factor in enumerate((0, -0.08, 0.07, -0.30, 0.30, -0.10, 0.08, 0)):
            x = center_x - radius_x * 0.43 + index * radius_x * 0.12
            points.extend((x, mouth_y + height_factor * radius_y))
        self.orb.create_text(
            center_x, center_y + radius_y * 0.87, text=f"●  {self.status.get()}",
            fill=ACCENT if active else MUTED, font=("Segoe UI", 8, "bold"),
        )
        self.orb.create_line(
            points, fill=PURPLE if active else "#b967f7", width=2, smooth=True,
        )
        self._draw_waveform()
        self.root.after(90 if active else 180, self._animate_orb)

    def _draw_waveform(self) -> None:
        if not hasattr(self, "waveform") or not self.waveform.winfo_exists():
            return
        self.waveform.delete("all")
        width = max(self.waveform.winfo_width(), 120)
        height = max(self.waveform.winfo_height(), 42)
        bars = 36
        gap = 3
        bar_width = max(2, (width - (bars - 1) * gap - 8) / bars)
        total_width = bars * bar_width + (bars - 1) * gap
        start_x = (width - total_width) / 2
        middle = height / 2
        for index in range(bars):
            envelope = 0.28 + 0.72 * (1 - abs(index - (bars - 1) / 2) / (bars / 2))
            variation = (index * 13 + self._pulse * 2 if self._active else index * 13) % 17
            bar_height = max(5, height * envelope * (0.18 + variation / 25))
            x = start_x + index * (bar_width + gap)
            color = PURPLE if index % 7 in (0, 1) else ACCENT
            self.waveform.create_line(
                x, middle - bar_height / 2, x, middle + bar_height / 2,
                fill=color, width=max(2, int(bar_width)),
            )

    def set_status(self, value: str) -> None:
        normalized = value.split(":", 1)[0].upper()
        self._active = normalized in {"LISTENING", "RECOGNIZING", "PROCESSING", "EXECUTING", "SPEAKING"}
        colors = {
            "ERROR": ("#fecaca", "#4a222d"),
            "STOPPED": (MUTED, "#252d3d"),
            "IDLE": (ACCENT, "#173243"),
        }
        foreground, background = colors.get(normalized, (GREEN, "#12352f"))
        self.status.set(normalized.replace("_", " "))
        self.visualizer_title.set(
            f"VOICE VISUALIZER · {normalized}" if self._active
            else "VOICE VISUALIZER · STANDBY"
        )
        self.status_label.configure(fg=foreground, bg=background)
        self.status_dot.configure(fg=foreground)
        if normalized in {"LISTENING", "RECOGNIZING"}:
            self.listen_button.configure(text="  ■  Stop listening", fg=TEXT, bg="#7f3041")
        else:
            self.listen_button.configure(text="  🎙  Start listening", fg="#06212a", bg=ACCENT)

    def update_settings(self, settings: Settings) -> None:
        self.listen_button.configure(
            text="  🎙  Start listening" if not settings.auto_start_listening else "  ■  Stop listening"
        )
