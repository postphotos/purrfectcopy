"""Small facade for the pcopy backup tool.

This module intentionally re-exports a small set of symbols from the
`pcopy` package for compatibility with older tests and scripts that
import from ``app``. The real implementation lives in the `pcopy`
package; importing this module should not perform work other than
binding names.

"""

from pcopy.runner import main
from pcopy import (
    BackupDashboard,
    SLOGANS,
    CAT_FACTS,
    COW_PATH,
    SETTINGS,
    SOURCE_DIR,
    DEST_DIR,
)

__all__ = [
    'main',
    'BackupDashboard',
    'SLOGANS',
    'CAT_FACTS',
    'COW_PATH',
    'SETTINGS',
    'SOURCE_DIR',
    'DEST_DIR',
]


if __name__ == '__main__':
    raise SystemExit(main())

# Facade version (re-exported from package)
try:
    __version__ = getattr(__import__('pcopy'), '__version__')
    VERSION = __version__
except Exception:
    __version__ = '0.0.1'
    VERSION = __version__