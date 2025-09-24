import importlib
from pathlib import Path

import pcopy


def test_slogans_path_fallback(tmp_path: Path):
    """Temporarily move the package-local slogans.json, reload pcopy.config to
    exercise the branch that falls back to the repo-level slogans.json or
    default values, then restore the file and reload again.
    """

    pkg_dir = Path(pcopy.__file__).resolve().parent
    pkg_slogans = pkg_dir / "slogans.json"
    backup = pkg_slogans.with_suffix('.json.bak')

    moved = False
    try:
        if pkg_slogans.exists():
            pkg_slogans.rename(backup)
            moved = True

        # Reload the config module so it picks up the missing package slogans
        cfg = importlib.import_module("pcopy.config")
        importlib.reload(cfg)

        # SLOGANS should be a list even when fallback/default path is used
        assert isinstance(cfg.SLOGANS, list)
        assert len(cfg.SLOGANS) >= 0

    finally:
        # restore file
        if moved:
            backup.rename(pkg_slogans)
            cfg = importlib.reload(importlib.import_module("pcopy.config"))
