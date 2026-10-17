"""Session-only chat window for the optional local Ollama assistant."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Callable

from core.ai_chat import ChatMessage


class ChatWindow(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Misc,
        on_send: Callable[[list[ChatMessage]], None],
    ):
        super().__init__(parent)
        self.on_send = on_send
        self.messages: list[ChatMessage] = []
        self.title("POVA AI Chat")
        self.geometry("720x620")
        self.minsize(560, 440)
        self.configure(bg="#0b1020")
        self.transient(parent)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        tk.Label(
            self, text="Chat with POVA", font=("Segoe UI", 19, "bold"),
            fg="#f4f7fb", bg="#0b1020",
        ).grid(row=0, column=0, sticky="w", padx=22, pady=(20, 3))
        tk.Label(
            self,
            text="Powered by local Ollama. Messages stay on this PC and are cleared when this window closes.",
            font=("Segoe UI", 9), fg="#91a0b8", bg="#0b1020",
        ).grid(row=1, column=0, sticky="w", padx=22, pady=(0, 14))

        transcript_frame = tk.Frame(self, bg="#151f33")
        transcript_frame.grid(row=2, column=0, sticky="nsew", padx=22)
        transcript_frame.rowconfigure(0, weight=1)
        transcript_frame.columnconfigure(0, weight=1)
        self.transcript = tk.Text(
            transcript_frame, wrap="word", state="disabled", relief="flat",
            bg="#151f33", fg="#dce6f2", insertbackground="#dce6f2",
            font=("Segoe UI", 10), padx=16, pady=14, spacing3=5,
        )
        self.transcript.grid(row=0, column=0, sticky="nsew")
        scrollbar = ttk.Scrollbar(
            transcript_frame, orient="vertical", command=self.transcript.yview,
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.transcript.configure(yscrollcommand=scrollbar.set)
        self.transcript.tag_configure("user", foreground="#49d7e8", font=("Segoe UI", 10, "bold"))
        self.transcript.tag_configure("assistant", foreground="#67e8b2", font=("Segoe UI", 10, "bold"))
        self.transcript.tag_configure("error", foreground="#fca5a5")
        self._append("POVA", "Ask me a question. I can help with general questions and follow-ups.")

        controls = tk.Frame(self, bg="#0b1020")
        controls.grid(row=3, column=0, sticky="ew", padx=22, pady=16)
        controls.columnconfigure(0, weight=1)
        self.input = ttk.Entry(controls, font=("Segoe UI", 10))
        self.input.grid(row=0, column=0, sticky="ew", padx=(0, 9), ipady=8)
        self.input.bind("<Return>", self._submit_event)
        self.send_button = tk.Button(
            controls, text="Send", command=self._submit,
            font=("Segoe UI", 9, "bold"), fg="#06212a", bg="#49d7e8",
            activebackground="#78e6ef", relief="flat", bd=0, padx=18, pady=9,
        )
        self.send_button.grid(row=0, column=1, padx=(0, 8))
        self.new_chat_button = tk.Button(
            controls, text="New chat", command=self.clear,
            font=("Segoe UI", 9), fg="#dce6f2", bg="#1b2940",
            activebackground="#2a3b55", relief="flat", bd=0, padx=12, pady=9,
        )
        self.new_chat_button.grid(row=0, column=2)
        self.input.focus_set()

    def _submit_event(self, _event: tk.Event) -> str:
        self._submit()
        return "break"

    def _submit(self) -> None:
        text = self.input.get().strip()
        if not text:
            return
        self.input.delete(0, "end")
        self.messages.append({"role": "user", "content": text})
        self._append("You", text)
        self.input.configure(state="disabled")
        self.send_button.configure(state="disabled", text="Thinking...")
        self.new_chat_button.configure(state="disabled")
        self.on_send(list(self.messages[-20:]))

    def complete(self, response: str | None = None, error: str | None = None) -> None:
        if not self.winfo_exists():
            return
        if error:
            self._append("POVA", error, "error")
        elif response:
            self.messages.append({"role": "assistant", "content": response})
            self._append("POVA", response, "assistant")
        self.input.configure(state="normal")
        self.send_button.configure(state="normal", text="Send")
        self.new_chat_button.configure(state="normal")
        self.input.focus_set()

    def clear(self) -> None:
        self.messages.clear()
        self.transcript.configure(state="normal")
        self.transcript.delete("1.0", "end")
        self.transcript.configure(state="disabled")
        self._append("POVA", "New chat started. What would you like to know?")

    def _append(self, speaker: str, text: str, tag: str | None = None) -> None:
        self.transcript.configure(state="normal")
        self.transcript.insert("end", f"{speaker}\n", tag or ("user" if speaker == "You" else "assistant"))
        if tag:
            self.transcript.insert("end", f"{text}\n\n", tag)
        else:
            self.transcript.insert("end", f"{text}\n\n")
        self.transcript.configure(state="disabled")
        self.transcript.see("end")
