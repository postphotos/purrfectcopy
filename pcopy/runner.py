"""Runner orchestration for pcopy backup, exposes main()."""
from __future__ import annotations

import argparse
import shlex
import subprocess
import sys
from typing import List

from .config import SOURCE_DIR, DEST_DIR
from .cowsay_helper import cowsay_art
from .dashboard import BackupDashboard


def _build_rsync_cmd(source: str, dest: str, dry_run: bool = False, extra: List[str] | None = None) -> List[str]:
    cmd = ['rsync', '-a', '--info=progress2']
    if dry_run:
        cmd.append('--dry-run')
    if extra:
        cmd += extra
    cmd += [str(source), str(dest)]
    return cmd


def run_backup(source: str | None = None, dest: str | None = None, dry_run: bool = False, boring: bool = False, extra: List[str] | None = None) -> int:
    src = source or str(SOURCE_DIR)
    dst = dest or str(DEST_DIR)
    dash = BackupDashboard(boring=boring)
    dash.show_message('Starting backup')

    cmd = _build_rsync_cmd(src, dst, dry_run=dry_run, extra=extra)
    dash.show_message('Running: ' + shlex.join(cmd))

    try:
        proc = subprocess.run(cmd, check=False, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        out = proc.stdout or ''
        if proc.returncode != 0 and not dry_run:
            dash.show_message('rsync failed')
            dash.show_message(cowsay_art('Backup failed', 'backupcat'))
            return proc.returncode
        dash.show_message('Backup completed')
        dash.show_message(cowsay_art('Backup complete', 'datakitten'))
        return 0
    except FileNotFoundError:
        dash.show_message('rsync not found')
        dash.show_message(cowsay_art('rsync missing', 'rsyncat'))
        return 2


def main(argv: List[str] | None = None) -> int:
    # If invoked with no argv (interactive CLI) and running in a TTY, show a
    # simple step menu to guide users. Tests call main([...]) with an explicit
    # argv so this branch won't interfere with automated tests.
    if argv is None and sys.stdin.isatty() and len(sys.argv) <= 1:
        return _show_menu()

    p = argparse.ArgumentParser(prog='pcopy')
    p.add_argument('--dry-run', action='store_true', dest='dry_run')
    p.add_argument('--quiet', action='store_true', dest='quiet')
    p.add_argument('--boring', action='store_true', dest='boring', help='Alias for --quiet')
    p.add_argument('--source', help='Source dir')
    p.add_argument('--dest', help='Dest dir')
    args = p.parse_args(argv)

    # boring is alias for quiet
    boring = args.boring or args.quiet
    return run_backup(source=args.source, dest=args.dest, dry_run=args.dry_run, boring=boring)


def _show_menu() -> int:
    """Simple interactive menu shown when running `pcopy` with no args.

    It's intentionally minimal — it prints numbered choices and maps them to
    common actions (dry-run, real run, custom source/dest). It returns 0 on
    normal completion. This helper is skipped during tests (they call main
    with an explicit argv).
    """
    from .config import SETTINGS, SLOGANS, CAT_FACTS
    from rich.prompt import Prompt
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    import random

    console = Console()

    def header_text() -> str:
        # Prefer slogans, then cat facts for a charming header
        if SLOGANS:
            return random.choice(SLOGANS)
        if CAT_FACTS:
            return random.choice(CAT_FACTS)
        return "Purrfect Backup"

    try:
        while True:
            console.clear()
            console.print(Panel(header_text(), title="🐾 Purrfect Backup", subtitle="Interactive"))

            # Build named backups table
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("#", style="dim", width=3)
            table.add_column("Name")
            table.add_column("Source")
            table.add_column("Dest")

            named = []
            if isinstance(SETTINGS, dict):
                named = [k for k in SETTINGS.keys() if k != 'rsync_options']

            for i, name in enumerate(named, start=1):
                cfg = SETTINGS.get(name, {}) if isinstance(SETTINGS, dict) else {}
                table.add_row(str(i), name, str(cfg.get('source', '')), str(cfg.get('dest', '')))

            console.print(table)

            console.print("\nOptions: [bold]N[/]umber to run, [bold]d[/]ry-run + number, [bold]c[/]ustom, [bold]h[/]elp, [bold]q[/]uit")

            choice = Prompt.ask("Choice (e.g. '1', 'd2', 'c')", default="q")
            if not choice:
                continue
            choice = choice.strip().lower()

            if choice == 'q' or choice == 'quit':
                console.print("Goodbye")
                return 0

            if choice == 'h' or choice == 'help':
                console.print(Panel("pcopy --help\nRun 'pcopy --source <src> --dest <dst>' or use the menu."))
                Prompt.ask("Press Enter to continue", default="")
                continue

            if choice.startswith('d') and len(choice) > 1 and choice[1:].isdigit():
                idx = int(choice[1:]) - 1
                if 0 <= idx < len(named):
                    name = named[idx]
                    cfg = SETTINGS.get(name, {})
                    console.print(f"Dry-run: {name}")
                    return run_backup(source=cfg.get('source'), dest=cfg.get('dest'), dry_run=True)
                else:
                    console.print("Invalid selection")
                    continue

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(named):
                    name = named[idx]
                    cfg = SETTINGS.get(name, {})
                    console.print(f"Running: {name}")
                    return run_backup(source=cfg.get('source'), dest=cfg.get('dest'), dry_run=False)
                else:
                    console.print("Invalid selection")
                    continue

            if choice.startswith('c'):
                # custom run
                try:
                    src = Prompt.ask("Source path")
                    dst = Prompt.ask("Destination path")
                except (EOFError, KeyboardInterrupt):
                    console.print()
                    return 1
                return run_backup(source=src, dest=dst, dry_run=False)

            console.print("Unknown command")
    except (KeyboardInterrupt, EOFError):
        console.print()
        return 1
