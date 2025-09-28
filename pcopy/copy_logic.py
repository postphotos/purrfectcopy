"""Copy/backup logic extracted from the project's shell script.

Provides a Python implementation that:
- creates timestamped copies of changed files (when source file is newer than dest)
- copies new files from source to dest when rsync is not used
- optionally runs rsync to perform efficient delta transfer

Designed to be testable: callers can disable rsync and assert timestamped file behavior.
"""
from __future__ import annotations

import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


def _timestamped_name(dest: Path) -> Path:
    """Return a Path for the timestamped copy in the same directory as dest.

    Example: /dest/dir/foo.txt -> /dest/dir/foo.20250926_120000.txt
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    name = dest.name
    if "." in name:
        base, ext = name.rsplit('.', 1)
        new_name = f"{base}.{ts}.{ext}"
    else:
        new_name = f"{name}.{ts}"
    return dest.with_name(new_name)


def perform_backup(source: str | Path, dest: str | Path, log_file: Optional[str] = None, run_rsync: bool = True) -> Dict[str, Any]:
    src = Path(source)
    dst = Path(dest)
    if not src.exists():
        raise FileNotFoundError(f"source not found: {src}")
    dst.mkdir(parents=True, exist_ok=True)

    timestamped: List[str] = []
    copied_new: List[str] = []

    # PART 1: Timestamp changed files (source newer than destination)
    for root, _dirs, files in os.walk(src):
        rootp = Path(root)
        rel_root = rootp.relative_to(src)
        target_root = dst.joinpath(rel_root)
        for fname in files:
            sfn = rootp / fname
            tfn = target_root / fname
            if tfn.exists():
                try:
                    if sfn.stat().st_mtime > tfn.stat().st_mtime:
                        tfn.parent.mkdir(parents=True, exist_ok=True)
                        ts_dest = _timestamped_name(tfn)
                        shutil.copy2(sfn, ts_dest)
                        timestamped.append(str(ts_dest))
                except Exception:
                    # ignore per-file errors and continue
                    continue

    # PART 2: Copy new/updated files — if rsync is available and requested, use it
    rsync_avail = shutil.which('rsync') is not None
    rsync_used = False
    rsync_output = None
    if run_rsync and rsync_avail:
        cmd = [
            'rsync', '-avh', '--progress2', '--partial', '--no-whole-file', '--inplace', '--update'
        ]
        if log_file:
            cmd += ['--log-file', str(log_file)]
        # Ensure we copy contents of source into dest (trailing slash semantics)
        cmd += [str(src) + os.path.sep, str(dst)]
        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=600)
            rsync_used = True
            rsync_output = proc.stdout + '\n' + proc.stderr
        except Exception as e:
            rsync_output = f"rsync failed: {e}"

    else:
        # Perform a simple copy of new files when rsync is not used
        for root, _dirs, files in os.walk(src):
            rootp = Path(root)
            rel_root = rootp.relative_to(src)
            target_root = dst.joinpath(rel_root)
            for fname in files:
                sfn = rootp / fname
                tfn = target_root / fname
                if not tfn.exists():
                    tfn.parent.mkdir(parents=True, exist_ok=True)
                    try:
                        shutil.copy2(sfn, tfn)
                        copied_new.append(str(tfn))
                    except Exception:
                        continue

    return {
        'timestamped': timestamped,
        'copied_new': copied_new,
        'rsync_used': rsync_used,
        'rsync_output': rsync_output,
    }
