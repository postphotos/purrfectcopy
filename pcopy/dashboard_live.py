"""Live dashboard implementation for pcopy (port of oldapp BackupDashboard).

Provides a Live-driven multi-panel UI with demo and test modes for safe
rendering during tests/CI.
"""
from __future__ import annotations

import os
import random
import re
import subprocess
import time
from datetime import datetime
import sys
from pathlib import Path
from typing import Iterable, List, Optional
import logging

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.table import Table
from rich.text import Text

from .config import SLOGANS_DATA, SLOGANS, CAT_FACTS, STAGES
from .cowsay_helper import cowsay_art


class LiveDashboard:
    def __init__(self, dry_run: bool = False, boring: bool = False, test_mode: bool = False, demo_mode: bool = False, cow_hold_seconds: int = 7, logger: Optional[logging.Logger] = None):
        self.dry_run = dry_run
        self.boring = boring
        self.test_mode = test_mode
        self.demo_mode = demo_mode
        self.console = Console()
        self.logger = logger

        # State
        self.files_moved_count = 0
        self.total_files: Optional[int] = None
        self.start_time: Optional[datetime] = None
        self.progress = 0
        self.cow_character = "datakitten"
        self.cow_quote = ""
        self.current_file = ""
        self.last_moved_file = ""
        self.speed = ""
        self.transferred = ""
        self.errors: List[str] = []
        # duplicate detection
        self._seen_files: set[str] = set()
        self.duplicates: int = 0

        # cowsay caching
        self.cow_hold_seconds = cow_hold_seconds
        self._last_cow_change = 0.0
        self._cached_cow_art: Optional[str] = None

        # rich components
        self.progress_bar = Progress(
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[bold magenta]{task.percentage:>3.0f}%"),
        )
        self.task_id = self.progress_bar.add_task("Overall Progress", total=100)
        self.layout = self._create_layout()

        # For test/demo mode we may not create Live screen
        self._live: Optional[Live] = None

    def _create_layout(self) -> Layout:
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(ratio=1, name="main"),
            Layout(size=6, name="footer"),
        )
        layout["main"].split_row(Layout(name="cowsay"), Layout(name="stats"))
        return layout

    def _get_cowsay_art(self) -> str:
        now = time.time()
        if self._cached_cow_art and (now - self._last_cow_change) < self.cow_hold_seconds:
            return self._cached_cow_art

        try:
            out = cowsay_art(f"({self.progress}%) {self.cow_quote}", self.cow_character)
        except Exception:
            out = f"({self.progress}%) {self.cow_quote}"

        self._cached_cow_art = out
        self._last_cow_change = now
        return out

    def _files_bar(self, width: int = 30) -> Text:
        if not self.total_files or self.total_files == 0:
            filled = int((self.progress / 100.0) * width)
            label = f"{self.files_moved_count} files"
        else:
            ratio = min(1.0, self.files_moved_count / self.total_files)
            filled = int(ratio * width)
            label = f"{self.files_moved_count}/{self.total_files} files"
        empty = width - filled
        bar = "█" * filled + "░" * empty
        return Text(f"{bar} {label}", style="bold green")

    def _update_layout_panels(self) -> None:
        # header
        self.layout["header"].update(Panel(Text("Purrfect Backup 🐾", justify="center", style="bold magenta"), border_style="green"))

        # cowsay
        self.layout["cowsay"].update(Panel(Text(self._get_cowsay_art(), justify="center"), border_style="blue", title="Backup Mascot"))

        # stats table
        stats_table = Table.grid(expand=True)
        stats_table.add_column(justify="right", ratio=1)
        stats_table.add_column(justify="left", ratio=4)

        stats_table.add_row("🔄 Current File:", Text(self.current_file, overflow="ellipsis", no_wrap=True))
        stats_table.add_row("📂 Last Moved:", Text(self.last_moved_file, overflow="ellipsis", no_wrap=True))
        stats_table.add_row("📦 Speed:", Text(str(self.speed)))
        stats_table.add_row("📦 Transferred:", Text(str(self.transferred)))
        stats_table.add_row("⏱️ Elapsed:", Text(self._format_elapsed()))
        stats_table.add_row("📁 Files:", self._files_bar())

        self.layout["stats"].update(Panel(stats_table, border_style="yellow", title="Live Stats"))
        self.layout["footer"].update(self.progress_bar)

    def _format_elapsed(self) -> str:
        if not self.start_time:
            return "0s"
        delta = datetime.now() - self.start_time
        total_seconds = int(delta.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        if hours:
            return f"{hours}h {minutes}m {seconds}s"
        if minutes:
            return f"{minutes}m {seconds}s"
        return f"{seconds}s"

    def start(self) -> None:
        self.start_time = datetime.now()
        if not self.test_mode and not self.demo_mode:
            try:
                self._live = Live(self.layout, console=self.console, screen=True, redirect_stderr=False, vertical_overflow="visible")
                self._live.__enter__()
            except Exception:
                self._live = None
        else:
            # In test/demo mode we just update layout without entering Live
            self._update_layout_panels()

    def finish(self, exit_code: int = 0) -> None:
        # Print completion status
        if exit_code == 0 and not self.errors:
            status_panel = Panel(f"[bold green]✅ Purrfect Success! {random.choice(SLOGANS_DATA.get('goodbyes', ['Goodbye']))}", title="Complete")
        else:
            status_panel = Panel(
                f"[bold red]😿 Oh no! Rsync finished with exit code {exit_code} and {len(self.errors)} errors.\nFirst 5 errors:\n" + "\n".join(self.errors[:5]),
                title="Failure",
            )

        # Teardown Live if we entered it (close the live render)
        if self._live:
            try:
                self._live.__exit__(None, None, None)
            except Exception:
                pass

        # Always print a final summary panel so the user sees stats in the normal
        # terminal buffer (this avoids the UI vanishing silently).
        summary = Table.grid(expand=True)
        summary.add_column(ratio=1)
        summary.add_column(ratio=2)
        summary.add_row("Files moved:", str(self.files_moved_count))
        summary.add_row("Total files:", str(self.total_files or "unknown"))
        summary.add_row("Elapsed:", self._format_elapsed())
        summary.add_row("Transferred:", str(self.transferred))
        if self.errors:
            summary.add_row("Errors:", "\n".join(self.errors[:5]))
        summary.add_row("Duplicate transfers:", str(self.duplicates))

        # Print the main status and the summary table
        self.console.print(status_panel)
        self.console.print(Panel(summary, title="Summary"))

        # Log the end of the run if logger configured
        if self.logger:
            try:
                self.logger.info("Run complete: exit_code=%s files_moved=%s total=%s duplicates=%s errors=%s", exit_code, self.files_moved_count, self.total_files or 'unknown', self.duplicates, len(self.errors))
                if self.errors:
                    for e in self.errors[:20]:
                        self.logger.error("Error: %s", e)
            except Exception:
                pass

        # For dry-run mode in a real interactive session, hold the UI visible
        # for a short period so the user can inspect results. Skip this pause
        # during tests or demo mode to avoid slowing automated runs.
        if self.dry_run and not self.test_mode and not self.demo_mode:
            # Only pause for interactive real runs. Skip the pause during tests,
            # CI, or when stdin is not a TTY so automated runs are not slowed.
            under_pytest = 'pytest' in sys.modules or os.environ.get('PYTEST_CURRENT_TEST')
            if sys.stdin and sys.stdin.isatty() and not under_pytest:
                try:
                    self.console.print("[bold yellow]Dry-run complete — showing summary for 30 seconds. Press Ctrl-C to dismiss early.[/]")
                    time.sleep(30)
                except KeyboardInterrupt:
                    # Allow interactive users to dismiss the pause early
                    pass
            else:
                # Non-interactive or test environment: do not pause
                pass

    def update_from_rsync_line(self, line: str) -> None:
        # percent
        if m := re.search(r"(\d+)%", line):
            try:
                self.progress = int(m.group(1))
            except Exception:
                pass
            # detect speed
            if sp := re.search(r"([0-9.]+[A-Z]?B/s)", line):
                self.speed = sp.group(1)

        # file transfer line (rsync style)
        elif m := re.search(r"^>f\S+\s+(.*)", line):
            self.current_file = m.group(1).strip()
            self.files_moved_count += 1
            self.last_moved_file = self.current_file
            # Duplicate detection: if we've seen this file before, record it
            if self.current_file in self._seen_files:
                self.duplicates += 1
                if self.logger:
                    try:
                        self.logger.warning("Duplicate transfer detected: %s", self.current_file)
                    except Exception:
                        pass
            else:
                self._seen_files.add(self.current_file)

        elif "Total transferred file size" in line:
            try:
                self.transferred = line.split(":", 1)[1].strip()
            except Exception:
                pass

        # update slogan/animal selection heuristics
        self._update_slogan()

        # update the progress bar
        try:
            self.progress_bar.update(self.task_id, completed=self.progress)
        except Exception:
            pass

        # refresh panels
        self._update_layout_panels()

    def _update_slogan(self) -> None:
        # Determine stage from progress
        stage_key = "stage1"
        if 25 < self.progress <= 75:
            stage_key = "stage2"
        elif self.progress > 75:
            stage_key = "stage3"

        stage = STAGES.get(stage_key, {}) if isinstance(STAGES, dict) else {}
        animals = stage.get("animals", [])
        quotes = stage.get("quotes", [])

        if animals:
            self.cow_character = random.choice(animals)

        quotes_pool = list(quotes)
        try:
            console_height = getattr(self.console, "size").height
        except Exception:
            console_height = 0

        if console_height and console_height > 45:
            quotes_pool.extend(CAT_FACTS)

        if quotes_pool:
            self.cow_quote = random.choice(quotes_pool)
        else:
            self.cow_quote = "Backing up with purrs..."

    # Demo helpers
    def run_demo(self, duration: float = 20.0, steps: int | None = None) -> None:
        """Simulate a staged progression over `duration` seconds.

        If `test_mode` is enabled or environment variable `PCOPY_TEST_MODE` is
        set, the run is seeded for determinism and shortened for speed.
        """
        # In demo we avoid entering full Live; allow deterministic demos in test mode
        self.test_mode = True  # do not enter Live

        # Deterministic behavior in test/CI
        env_test = os.environ.get('PCOPY_TEST_MODE') == '1'
        if self.test_mode or env_test:
            random.seed(0)
            # shorten demo for tests
            if steps is None:
                steps = 10
            duration = float(max(0.05, min(duration, 0.2)))
        else:
            if steps is None:
                steps = 50

        self.start()
        for i in range(steps + 1):
            pct = int((i / steps) * 100)
            # simulate occasional file lines
            if i % max(1, steps // 10) == 0:
                self.update_from_rsync_line(f">f+++++++++ demo-file-{i}.txt")
            self.progress = pct
            self._update_slogan()
            try:
                self.progress_bar.update(self.task_id, completed=self.progress)
            except Exception:
                pass
            self._update_layout_panels()
            time.sleep(max(0.001, duration / max(1, steps)))
        self.finish(0)
