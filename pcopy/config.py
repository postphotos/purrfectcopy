"""Configuration and constants for pcopy backup app."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

HERE = Path(__file__).resolve().parent
# Prefer package-local slogans.json (installed with package data); fallback to repo-level slogans.json
SLOGANS_PATH = HERE / 'slogans.json'
if not SLOGANS_PATH.exists():
    SLOGANS_PATH = HERE.parent / 'slogans.json'


def _load_slogans() -> Dict[str, Any]:
    try:
        with SLOGANS_PATH.open('r', encoding='utf8') as fh:
            return json.load(fh)
    except Exception:
        return {
            'slogans': ['Backup running...'],
            'cat_facts': ['Cats sleep a lot.']
        }


_S = _load_slogans()
SLOGANS: List[str] = _S.get('slogans', [])
CAT_FACTS: List[str] = _S.get('cat_facts', [])

# Optional YAML settings file for named backup configs
SETTINGS_PATH = Path.home() / '.pcopy-main-backup.yml'


def _load_settings() -> Dict[str, Any]:
    try:
        import yaml

        if SETTINGS_PATH.exists():
            with SETTINGS_PATH.open('r', encoding='utf8') as fh:
                return yaml.safe_load(fh) or {}
    except Exception:
        return {}
    return {}


SETTINGS = _load_settings()

# Paths
COW_PATH = HERE.parent / 'cows'
SOURCE_DIR = Path(SETTINGS.get('source', '.')).resolve()
DEST_DIR = Path(SETTINGS.get('dest', './backup')).resolve()
EXCLUDE_FILE = Path(SETTINGS.get('exclude', '.pcopy-exclude'))
BACKUP_VERSIONS_DIR = Path(SETTINGS.get('backup_versions_dir', str(DEST_DIR / 'versions')))
