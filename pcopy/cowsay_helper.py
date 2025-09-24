"""Helpers to render cowsay art for pcopy."""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Dict, Optional

from .config import COW_PATH

_CACHE: Dict[str, str] = {}


def _system_cowsay_available() -> bool:
    return shutil.which('cowsay') is not None


def find_custom_cow(name: str) -> Optional[Path]:
    p = COW_PATH / f"{name}.cow"
    return p if p.exists() else None


def cowsay_art(text: str, cow: str = 'datakitten') -> str:
    """Return ASCII art for given text. Use cache, system cowsay if available, or built-in fallback."""
    key = f"{cow}:{text}"
    if key in _CACHE:
        return _CACHE[key]

    if _system_cowsay_available():
        cowfile = find_custom_cow(cow)
        cmd = ['cowsay']
        if cowfile:
            cmd += ['-f', str(cowfile)]
        cmd += [text]
        try:
            out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            _CACHE[key] = out
            return out
        except Exception:
            pass

    # Fallback ascii art if cowsay is not present
    art = f"<{cow}> {text}\n"
    _CACHE[key] = art
    return art
