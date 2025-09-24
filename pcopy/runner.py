"""Runner orchestration for pcopy backup, exposes main()."""
from __future__ import annotations

import argparse
import shlex
import subprocess
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
