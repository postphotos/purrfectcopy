import shutil
from pathlib import Path

from pcopy import cowsay_helper as ch


def test_cowsay_fallback_and_cache(tmp_path: Path):
    # Force cache to be empty
    ch._CACHE.clear()

    # Monkeypatch shutil.which so the system cowsay path is considered absent.
    orig_which = shutil.which
    try:
        shutil.which = lambda name: None

        out = ch.cowsay_art('hello', 'nonexistentcow')
        # The fallback art includes the cow name in angle brackets
        assert '<nonexistentcow>' in out

        # Calling again should use the cache and return the same output
        out2 = ch.cowsay_art('hello', 'nonexistentcow')
        assert out2 == out
    finally:
        shutil.which = orig_which
