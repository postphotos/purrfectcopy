"""pcopy package - small helpers and re-exports for the pcopy app."""
from .config import SLOGANS, SETTINGS, CAT_FACTS, COW_PATH, SOURCE_DIR, DEST_DIR, EXCLUDE_FILE, BACKUP_VERSIONS_DIR
from .dashboard import BackupDashboard
from .runner import main

__all__ = [
    'SLOGANS','SETTINGS','CAT_FACTS','COW_PATH','SOURCE_DIR','DEST_DIR','EXCLUDE_FILE','BACKUP_VERSIONS_DIR',
    'BackupDashboard','main'
]

# Package version (PEP440)
__version__ = "0.0.1"
VERSION = __version__
# Package metadata
__author__ = "(your name)"
