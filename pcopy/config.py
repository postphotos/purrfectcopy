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

# Allow overriding the slogans file via environment variable for customization
import os
env_slogans = os.environ.get('PCOPY_SLOGANS')
if env_slogans:
    env_path = Path(env_slogans)
    if env_path.exists():
        SLOGANS_PATH = env_path


def _load_slogans() -> Dict[str, Any]:
    # Priority: user SETTINGS 'slogans' key > PCOPY_SLOGANS file > packaged slogans.json > defaults
    data: Dict[str, Any] = {}
    try:
        # If user settings file contains slogans, prefer that
        import yaml

        if SETTINGS_PATH.exists():
            with SETTINGS_PATH.open('r', encoding='utf8') as fh:
                user = yaml.safe_load(fh) or {}
                s = user.get('slogans')
                cf = user.get('cat_facts')
                if s or cf:
                    data['slogans'] = s or []
                    data['cat_facts'] = cf or []
                    return data
    except Exception:
        # ignore; fallback to file-based slogans
        pass

    try:
        with SLOGANS_PATH.open('r', encoding='utf8') as fh:
            data = json.load(fh) or {}
    except Exception:
        data = {}

    if 'slogans' not in data:
        # Keep legacy 'slogans' key for backwards compatibility with tests/code
        data['slogans'] = ['Backup running...']
    if 'cat_facts' not in data:
        data['cat_facts'] = ['Cats sleep a lot.']
    if 'quotes' not in data:
        # Primary modern key used by richer UI
        data['quotes'] = data.get('slogans', ['Backup running...'])
    return data


_S = _load_slogans()
# Preserve the raw slogans data (dict) for stage-based UI and backwards compat.
SLOGANS_DATA: Dict[str, Any] = _S
# Top-level quotes list (used for short header lines), and cat facts list.
SLOGANS: List[str] = list(_S.get('quotes') or [])
CAT_FACTS: List[str] = list(_S.get('cat_facts') or [])
# Stage mapping used by richer dashboards
STAGES: Dict[str, Any] = _S.get('stages', {})


def reload_settings() -> None:
    """Reload SETTINGS and slogans data. Useful for tests that modify files.

    Callers should re-import symbols or call this to refresh module-level values.
    """
    global SETTINGS, SLOGANS_DATA, SLOGANS, CAT_FACTS, STAGES
    SETTINGS = _load_settings()
    SLOGANS_DATA = _load_slogans()
    SLOGANS = list(SLOGANS_DATA.get('quotes') or [])
    CAT_FACTS = list(SLOGANS_DATA.get('cat_facts') or [])
    STAGES = SLOGANS_DATA.get('stages', {})

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
