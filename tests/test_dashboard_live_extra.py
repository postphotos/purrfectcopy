import os
import time
from types import SimpleNamespace

import pytest

from pcopy.dashboard_live import LiveDashboard


def test_get_cowsay_art_caching():
    ld = LiveDashboard(test_mode=True)
    # prime cache
    a1 = ld
    # set the cached art and last change to recent
    ld._cached_cow_art = a1
    ld._last_cow_change = time.time()
    a2 = ld._get_cowsay_art()
    assert a1 == a2


def test_run_demo_in_test_mode_quick(monkeypatch):
    # Use test_mode so run_demo short-circuits and is deterministic
    ld = LiveDashboard(test_mode=True)
    # shorten sleep and steps to be fast
    monkeypatch.setenv('PCOPY_TEST_MODE', '1')
    ld.run_demo(duration=0.01, steps=2)
    # After demo, files_moved_count should be set
    assert ld.files_moved_count >= 0
    assert isinstance(ld.transferred, str)


def test_finish_logs_and_handles_pause(monkeypatch, caplog):
    # test finish prints summary and logs info; simulate dry-run interactive pause bypass
    ld = LiveDashboard(test_mode=False, demo_mode=False, dry_run=True)
    ld.files_moved_count = 2
    ld.transferred = '123 bytes'
    ld.errors = ['err1']
    ld.duplicates = 1

    # Make stdin appear as a TTY and ensure not under pytest
    class _FakeStdin:
        def isatty(self):
            return True

    monkeypatch.setattr('sys.stdin', _FakeStdin())
    # ensure pytest module not in modules to attempt pause; monkeypatch environment so under_pytest check fails
    monkeypatch.setitem(os.environ, 'PYTEST_CURRENT_TEST', '')
    caplog.clear()
    caplog.set_level('INFO')
    # set a real logger that caplog will capture
    import logging
    test_logger = logging.getLogger('pcopy_test')
    test_logger.setLevel(logging.INFO)
    ld.logger = test_logger
    # monkeypatch time.sleep to avoid long pauses
    monkeypatch.setattr('time.sleep', lambda s: None)
    ld.finish(1)
    assert 'Run complete' in caplog.text
