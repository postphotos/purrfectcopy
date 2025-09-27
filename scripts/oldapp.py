import argparse
import json
import os
import random
import re
import subprocess
import sys
from datetime import datetime
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn
from rich.table import Table
from rich.text import Text

# --- 🐾 Configuration 🐾 ---
# Load all our fun slogans and quotes from the JSON file
try:
    with open("slogans.json", "r") as f:
        SLOGANS = json.load(f)
except FileNotFoundError:
    print("Error: slogans.json not found!")
    sys.exit(1)

# Get the home directory of the user, even when run with sudo
USER_HOME = os.path.expanduser(f"~{os.environ.get('SUDO_USER', os.environ.get('USER', ''))}")

# --- ✨ CUSTOMIZE YOUR PATHS HERE ✨ ---
SOURCE_DIR = os.path.join(USER_HOME, "Documents/Desktop/")
DEST_VOLUME = "/Volumes/nelops-node"
DEST_DIR = os.path.join(DEST_VOLUME, "postphotos-bak/Documents/Desktop/")
EXCLUDE_FILE = os.path.join(USER_HOME, ".rsync_excludes.txt")
# --- End of Configuration ---

BACKUP_VERSIONS_DIR = os.path.join(DEST_DIR, "..", f"_backup_versions/{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}")
COW_PATH = os.path.abspath("./cows")

class BackupDashboard:
    def __init__(self, dry_run=False):
        self.dry_run = dry_run
        self.console = Console()

        # Dashboard state
        self.progress = 0
        self.current_file = "Initializing..."
        self.speed = "N/A"
        self.transferred = "0B"
        self.errors = []
        self.cow_character = "kitty"
        self.cow_quote = "Getting ready to pounce..."

        # Rich components
        self.progress_bar = Progress(
            TextColumn("[bold cyan]{task.description}"),
            BarColumn(bar_width=None),
            TextColumn("[bold magenta]{task.percentage:>3.0f}%"),
        )
        self.task_id = self.progress_bar.add_task("Overall Progress", total=100)
        self.layout = self._create_layout()

    def _create_layout(self) -> Layout:
        """Defines the TUI layout."""
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(ratio=1, name="main"),
            Layout(size=5, name="footer"),
        )
        layout["main"].split_row(Layout(name="cowsay"), Layout(name="stats"))
        return layout

    def _get_cowsay_art(self) -> str:
        """Generates the cowsay art with a random slogan."""
        try:
            # Check if it's a custom cowfile
            cowfile_path = os.path.join(COW_PATH, self.cow_character) if "/" in self.cow_character else self.cow_character
            
            cmd = ["cowsay", "-f", cowfile_path, f"({self.progress}%) {self.cow_quote}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            return result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            # Fallback if cowsay or the file is missing
            return f"({self.progress}%) {self.cow_quote}"

    def _update_dashboard(self):
        """Updates all the rich components with the current state."""
        try:
            self.progress_bar.update(self.task_id, completed=self.progress)
        except Exception:
            pass

        stats_table = Table.grid(padding=(0, 1))
        stats_table.add_column(style="bold cyan")
        stats_table.add_column(style="white")
        stats_table.add_row("🔄 Current File:", Text(self.current_file, overflow="ellipsis", no_wrap=True))
        stats_table.add_row("🚀 Speed:", Text(str(self.speed)))
        stats_table.add_row("📦 Transferred:", Text(str(self.transferred)))
        stats_table.add_row("😿 Errors:", Text(str(len(self.errors))))

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

    def _update_slogan(self):
        """Selects a new cow and quote based on the current progress."""
        stage_key = "stage1"
        if 25 < self.progress <= 75:
            stage_key = "stage2"
        elif self.progress > 75:
            stage_key = "stage3"
        
        stage = SLOGANS["stages"][stage_key]
        self.cow_character = random.choice(stage["animals"])
        self.cow_quote = random.choice(stage["quotes"])

    def _check_destination(self):
        """Checks if the destination volume exists and is mounted."""
        if not os.path.exists(DEST_VOLUME):
            self.console.print(f"[bold red]Destination volume {DEST_VOLUME} not found!")
            sys.exit(1)
        
        # Check if it's mounted
        try:
            result = subprocess.run(["mount"], capture_output=True, text=True, check=True)
            if DEST_VOLUME not in result.stdout:
                self.console.print(f"[bold red]Destination volume {DEST_VOLUME} is not mounted!")
                sys.exit(1)
        except subprocess.CalledProcessError:
            # If mount command fails, assume it's okay (e.g., on non-Unix systems)
            pass

    def run(self):
        """Constructs and runs the rsync command, updating the TUI live."""
        self._check_destination()
        
        os.makedirs(BACKUP_VERSIONS_DIR, exist_ok=True)
        
        rsync_cmd = [
            "rsync",
            "-a", "-i", "--info=progress2,stats", "--human-readable",
            "--delete", "--backup", f"--backup-dir={BACKUP_VERSIONS_DIR}",
            f"--exclude-from={EXCLUDE_FILE}",
            SOURCE_DIR, DEST_DIR
        ]
        if self.dry_run:
            rsync_cmd.append("--dry-run")
        
        self.console.print(Panel(
            f"[bold]Source:[/]      [cyan]{SOURCE_DIR}[/]\n"
            f"[bold]Destination:[/] [cyan]{DEST_DIR}[/]\n"
            f"[bold]Excludes:[/]    [cyan]{EXCLUDE_FILE}[/]",
            title="Backup Configuration", border_style="green"
        ))

        if not self.console.input("\n[bold yellow]Proceed with backup? (y/n): ").lower().startswith('y'):
            self.console.print(f"[bold red]😿 {random.choice(SLOGANS['cancellations'])}")
            sys.exit(0)

        with Live(self.layout, console=self.console, screen=True, redirect_stderr=False, vertical_overflow="visible"):
            try:
                # We use Popen for non-blocking, real-time stream reading
                process = subprocess.Popen(
                    rsync_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1  # Line-buffered
                )
                
                if process.stdout is None or process.stderr is None:
                    raise RuntimeError("Failed to capture rsync stdout/stderr")
                
                # Process stdout for progress
                for line in iter(process.stdout.readline, ''):
                    if not line:
                        break
                    
                    # --- PARSE RSYNC'S LIVE OUTPUT ---
                    if match := re.search(r"(\d+)%", line):
                        self.progress = int(match.group(1))
                        if sp := re.search(r"([0-9.]+[A-Z]?B/s)", line):
                            self.speed = sp.group(1)
                        self._update_slogan()
                    
                    elif match := re.search(r"^>f\S+\s+(.*)", line):
                        self.current_file = match.group(1).strip()
                    
                    elif "Total transferred file size" in line:
                        parts = line.split(":", 1)
                        if len(parts) > 1:
                            self.transferred = parts[1].strip()
                    
                    self._update_dashboard()
                
                # Process stderr for errors after the fact
                stderr_output = process.stderr.read()
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
        
        # --- Final Report ---
        if exit_code == 0 and not self.errors:
            self.console.print(Panel(f"[bold green]✅ Purrfect Success! {random.choice(SLOGANS['goodbyes'])}", title="Complete"))
        else:
            self.console.print(Panel(
                f"[bold red]😿 Oh no! The kittens stumbled. Rsync finished with exit code {exit_code} and {len(self.errors)} errors.[/]\n\n"
                f"[yellow]First 5 error lines:\n" + "\n".join(self.errors[:5]),
                title="Failure"
            ))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A delightful kitten-powered backup script.")
    parser.add_argument("--dry-run", action="store_true", help="Perform a trial run with no changes made.")
    parser.add_argument("--dry-run-command", action="store_true", help="Print the rsync command that would be run and exit.")
    args = parser.parse_args()
    
    # Handle --dry-run-command separately
    if args.dry_run_command:
        rsync_cmd_str = (f"rsync -a -i --info=progress2,stats --human-readable "
                         f"--delete --backup --backup-dir='{BACKUP_VERSIONS_DIR}' "
                         f"--exclude-from='{EXCLUDE_FILE}' '{SOURCE_DIR}' '{DEST_DIR}'")
        # print plain string for scripts/CI
        print(rsync_cmd_str)
        sys.exit(0)
    
    dashboard = BackupDashboard(dry_run=args.dry_run)
    dashboard.run()
