# app.py

import argparse
import json
import os
import random
import re
import subprocess
import sys
import time
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.table import Table
from rich.text import Text
import yaml

# --- 🐾 Configuration 🐾 ---
try:
    with open("slogans.json", "r") as f:
        SLOGANS = json.load(f)
except FileNotFoundError:
    print("Error: slogans.json not found!")
    sys.exit(1)

USER_HOME = os.path.expanduser(f"~{os.environ.get('SUDO_USER', os.environ.get('USER', ''))}")

# Load settings from ~/.pcopy-main-backup.yml if exists
SETTINGS_FILE = os.path.join(USER_HOME, ".pcopy-main-backup.yml")
SETTINGS = {}
if os.path.exists(SETTINGS_FILE):
    try:
        with open(SETTINGS_FILE, "r") as f:
            SETTINGS = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"Warning: Could not load settings from {SETTINGS_FILE}: {e}")

SOURCE_DIR = os.path.join(USER_HOME, "Documents/Desktop/")
DEST_VOLUME = "/Volumes/nelops-node"
DEST_DIR = os.path.join(DEST_VOLUME, "postphotos-bak/Documents/Desktop/")
EXCLUDE_FILE = os.path.join(USER_HOME, ".rsync_excludes.txt")

# Override with settings if main-backup
if "main-backup" in SETTINGS:
    main_backup = SETTINGS["main-backup"]
    if "source" in main_backup:
        SOURCE_DIR = main_backup["source"]
    if "dest" in main_backup:
        DEST_DIR = main_backup["dest"]

# If the terminal is tall enough we will mix in short cat facts with the cowsay quotes.
# 33 lightweight, original cat facts to display when the console height > 45 lines.
CAT_FACTS = SLOGANS.get("cat_facts", [])
# --- End of Configuration ---

BACKUP_VERSIONS_DIR = os.path.join(DEST_DIR, "..", f"_backup_versions/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
COW_PATH = os.path.abspath("./cows")

class BackupDashboard:
    def __init__(self, dry_run=False, cow_hold_seconds: int = 7):
        self.dry_run = dry_run
        self.console = Console()

        # Dashboard state
        # File counting & timing
        self.files_moved_count = 0
        self.total_files = None  # computed on start
        self.start_time = None

        # Cowsay cache to keep same picture for N seconds
        self.cow_hold_seconds = cow_hold_seconds
        self._last_cow_change = 0.0
        self._cached_cow_art = None

        # Placeholder attributes used by update/display logic
        self.progress = 0
        self.cow_character = "default"
        self.cow_quote = ""
        self.current_file = ""
        self.last_moved_file = ""
        self.speed = ""
        self.transferred = ""
        self.errors = []

        # Rich components
        self.progress_bar = Progress(
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[bold magenta]{task.percentage:>3.0f}%"),
        )
        self.task_id = self.progress_bar.add_task("Overall Progress", total=100)
        self.layout = self._create_layout()

    def _create_layout(self) -> Layout:
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(ratio=1, name="main"),
            Layout(size=6, name="footer"),
        )
        layout["main"].split_row(Layout(name="cowsay"), Layout(name="stats"))
        return layout

    def _count_source_files(self) -> int:
        """Count files under SOURCE_DIR as an estimate for total files."""
        count = 0
        try:
            for root, dirs, files in os.walk(SOURCE_DIR):
                count += len(files)
        except Exception:
            count = 0
        return count

    def _get_cowsay_art(self) -> str:
        """Generates or returns cached cowsay art. Keep same art for cow_hold_seconds."""
        now = time.time()
        if self._cached_cow_art and (now - self._last_cow_change) < self.cow_hold_seconds:
            art = self._cached_cow_art
        else:
            try:
                if os.path.exists(os.path.join(COW_PATH, self.cow_character)):
                    cowfile_path = os.path.join(COW_PATH, self.cow_character)
                else:
                    cowfile_path = self.cow_character
                cmd = ["cowsay", "-f", cowfile_path, f"({self.progress}%) {self.cow_quote}"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                art = result.stdout
            except (subprocess.CalledProcessError, FileNotFoundError):
                art = f"({self.progress}%) {self.cow_quote}"
            self._cached_cow_art = art
            self._last_cow_change = now

        try:
            console_height = getattr(self.console, "size").height
        except Exception:
            console_height = 0

        if console_height and console_height > 45:
            fact = random.choice(CAT_FACTS)
            return art + "\n\n" + fact

        return art

    def _files_bar(self, width: int = 30) -> Text:
        """Small graphical representation of files moved vs total."""
        if not self.total_files or self.total_files == 0:
            # fallback to progress percentage
            filled = int((self.progress / 100.0) * width)
            label = f"{self.files_moved_count} files"
        else:
            ratio = min(1.0, self.files_moved_count / self.total_files)
            filled = int(ratio * width)
            label = f"{self.files_moved_count}/{self.total_files} files"
        empty = width - filled
        bar = "█" * filled + "░" * empty
        return Text(f"{bar} {label}", style="bold green")

    def _update_slogan(self):
        """Selects a new cow and quote based on the current progress.
        Actual cowsay ASCII art is cached for cow_hold_seconds to avoid rapid changes.
        """
        stage_key = "stage1"
        if 25 < self.progress <= 75:
            stage_key = "stage2"
        elif self.progress > 75:
            stage_key = "stage3"

        stage = SLOGANS["stages"][stage_key]
        # pick new animal; cowsay art generation is cached separately
        self.cow_character = random.choice(stage["animals"])

        # Prepare a pool of quotes; if the console is tall, mix in cat facts.
        quotes_pool = list(stage.get("quotes", []))
        if not quotes_pool:
            self.cow_quote = "Backing up with purrs..."
        else:
            self.cow_quote = random.choice(quotes_pool)

    def _format_elapsed(self) -> str:
        """Return a human-readable elapsed time since start_time."""
        if not self.start_time:
            return "0s"
        delta = datetime.now() - self.start_time
        total_seconds = int(delta.total_seconds())
        mins, secs = divmod(total_seconds, 60)
        hours, mins = divmod(mins, 60)
        if hours:
            return f"{hours}h {mins}m {secs}s"
        if mins:
            return f"{mins}m {secs}s"
        return f"{secs}s"

    def _update_dashboard(self):
        """Update the progress bar and all panels in the layout."""
        # update progress bar task
        try:
            self.progress_bar.update(self.task_id, completed=self.progress)
        except Exception:
            pass

        # (re)build the stats table
        stats_table = Table.grid(expand=True)
        stats_table.add_column(justify="right", ratio=1)
        stats_table.add_column(justify="left", ratio=4)

        stats_table.add_row("🔄 Current File:", Text(self.current_file, overflow="ellipsis", no_wrap=True))
        stats_table.add_row("📂 Last Moved:", Text(self.last_moved_file, overflow="ellipsis", no_wrap=True))
        stats_table.add_row("📦 Speed:", Text(self.speed))
        stats_table.add_row("📦 Transferred:", Text(self.transferred))
        stats_table.add_row("⏱️ Elapsed:", Text(self._format_elapsed()))
        stats_table.add_row("📁 Files:", self._files_bar())

        # update panels
        self.layout["header"].update(Panel(
            Text("Purrfect Backup 🐾", justify="center", style="bold magenta"),
            border_style="green"
        ))
        self.layout["cowsay"].update(Panel(
            Text(self._get_cowsay_art(), justify="center"),
            border_style="blue",
            title="Backup Mascot"
        ))
        self.layout["stats"].update(Panel(
            stats_table,
            border_style="yellow",
            title="Live Stats"
        ))
        self.layout["footer"].update(self.progress_bar)

    def run(self):
        """Build the rsync command, confirm with the user, and run the backup while updating the dashboard."""
        # estimate total files
        self.total_files = self._count_source_files()

        rsync_cmd = [
            "rsync", "-a", "-i", "--info=progress2,stats", "--human-readable",
            "--delete", "--backup", f"--backup-dir={BACKUP_VERSIONS_DIR}",
            f"--exclude-from={EXCLUDE_FILE}", SOURCE_DIR, DEST_DIR
        ]

        # Add custom rsync options from settings
        if "rsync_options" in SETTINGS:
            rsync_cmd.extend(SETTINGS["rsync_options"])

        if self.dry_run:
            rsync_cmd.append("--dry-run")

        self.console.print(Panel(
            f"[bold]Source:[/]      [cyan]{SOURCE_DIR}[/]\n"
            f"[bold]Destination:[/] [cyan]{DEST_DIR}[/]\n"
            f"[bold]Excludes:[/]    [cyan]{EXCLUDE_FILE}[/]\n"
            f"[bold]Estimated files:[/] [cyan]{self.total_files}[/]",
            title="Backup Configuration", border_style="green"
        ))

        if not self.console.input("\n[bold yellow]Proceed with backup? (y/n): ").lower().startswith('y'):
            self.console.print(f"[bold red]😿 {random.choice(SLOGANS['cancellations'])}")
            sys.exit(0)

        self.start_time = datetime.now()
        with Live(self.layout, console=self.console, screen=True, redirect_stderr=False, vertical_overflow="visible"):
            try:
                process = subprocess.Popen(
                    rsync_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1  # Line-buffered
                )
                stdout = process.stdout
                stderr = process.stderr
                # satisfy static type checkers: ensure pipes are present
                assert stdout is not None and stderr is not None

                for line in iter(stdout.readline, ''):
                    # Parse progress percentage
                    if match := re.search(r"(\d+)%", line):
                        self.progress = int(match.group(1))
                        if sp := re.search(r"([0-9.]+[A-Z]?B/s)", line):
                            self.speed = sp.group(1)
                        # choose new quote/animal based on progress but keep art cached for cow_hold_seconds
                        self._update_slogan()
                        # invalidate cached art only if the cow_hold_seconds expired
                        if (time.time() - self._last_cow_change) >= self.cow_hold_seconds:
                            # regenerate on next _get_cowsay_art call
                            self._cached_cow_art = None

                    # File transfer lines
                    elif match := re.search(r"^>f\S+\s+(.*)", line):
                        self.current_file = match.group(1).strip()
                        # Consider this a moved/transferred file for counting
                        self.files_moved_count += 1
                        self.last_moved_file = self.current_file

                    elif "Total transferred file size" in line:
                        self.transferred = line.split(":", 1)[1].strip()

                    self._update_dashboard()

                stderr_output = stderr.read()
                if stderr_output:
                    self.errors = stderr_output.strip().split('\n')

                process.wait()
                exit_code = process.returncode

            except FileNotFoundError:
                self.console.print("[bold red]Error: 'rsync' command not found. Is rsync installed and in your PATH?")
                sys.exit(1)
            except Exception as e:
                self.console.print(f"[bold red]An unexpected error occurred: {e}")
                sys.exit(1)

        # Final Report
        if exit_code == 0 and not self.errors:
            self.console.print(Panel(f"[bold green]✅ Purrfect Success! {random.choice(SLOGANS['goodbyes'])}", title="Complete"))
        else:
            self.console.print(Panel(
                f"[bold red]😿 Oh no! The kittens stumbled. Rsync finished with exit code {exit_code} and {len(self.errors)} errors.[/]\n\n"
                f"[yellow]First 5 error lines:\n" + "\n".join(self.errors[:5]),
                title="Failure"
            ))
def main(argv=None):
    parser = argparse.ArgumentParser(description="A delightful kitten-powered backup script.")
    parser.add_argument("--dry-run", action="store_true", help="Perform a trial run with no changes made.")
    parser.add_argument("--dry-run-command", action="store_true", help="Print the rsync command that would be run and exit.")
    parser.add_argument("source", nargs="?", help="Source directory to backup.")
    parser.add_argument("dest", nargs="?", help="Destination directory for backup.")
    args = parser.parse_args(argv)

    # Override paths if provided
    if args.source:
        global SOURCE_DIR
        SOURCE_DIR = args.source
    if args.dest:
        global DEST_DIR
        DEST_DIR = args.dest

    if args.dry_run_command:
        rsync_cmd_str = (f"rsync -a -i --info=progress2,stats --human-readable "
                        f"--delete --backup --backup-dir='{BACKUP_VERSIONS_DIR}' "
                        f"--exclude-from='{EXCLUDE_FILE}' '{SOURCE_DIR}' '{DEST_DIR}'")
        # print plain string (Panel objects require a Console); keep it simple
        print(rsync_cmd_str)
        sys.exit(0)

    dashboard = BackupDashboard(dry_run=args.dry_run)
    dashboard.run()


if __name__ == "__main__":
    main()