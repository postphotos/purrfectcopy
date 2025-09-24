"""Dashboard class and helpers for rendering the backup UI."""
from __future__ import annotations

import time
from typing import Iterable, Optional

from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn


class BackupDashboard:
    """Small, testable dashboard wrapper around rich Progress."""

    def __init__(self, console: Optional[Console] = None, boring: bool = False) -> None:
        self.console = console or Console()
        self.boring = boring
        self.start_time = time.monotonic()

    def format_elapsed(self, seconds: float) -> str:
        mins = int(seconds // 60)
        if mins < 60:
            return f"{mins}m"
        hours = mins // 60
        return f"{hours}h{mins % 60}m"

    def files_progress(self, total: int, completed: int) -> str:
        if total <= 0:
            return "0/0"
        return f"{completed}/{total}"

    def show_message(self, message: str) -> None:
        if self.boring:
            self.console.print(message)
        else:
            self.console.print(f"[bold green]{message}[/]")
