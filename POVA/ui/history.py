"""In-memory command history view."""

from dataclasses import dataclass
from datetime import datetime
from tkinter import ttk


@dataclass(frozen=True)
class HistoryItem:
    time: str
    command: str
    action: str
    status: str


class HistoryView:
    def __init__(self, parent):
        self.items: list[HistoryItem] = []
        self.table = ttk.Treeview(
            parent, columns=("time", "command", "action", "status"), show="headings", height=8
        )
        for key, title, width in (
            ("time", "Time", 95), ("command", "Command", 330),
            ("action", "Action", 250), ("status", "Status", 150),
        ):
            self.table.heading(key, text=title)
            self.table.column(key, width=width, anchor="w")
        self.table.column("time", stretch=False)
        self.table.column("status", stretch=False)

    def add(self, command: str, action: str, status: str) -> None:
        item = HistoryItem(datetime.now().strftime("%H:%M:%S"), command, action, status)
        self.items.append(item)
        self.table.insert("", "end", values=(item.time, item.command, item.action, item.status))
        children = self.table.get_children()
        if children:
            self.table.see(children[-1])

    def clear(self) -> None:
        self.items.clear()
        for item in self.table.get_children():
            self.table.delete(item)
