import os
import types
import time
import random

import pytest

from pcopy.dashboard_live import LiveDashboard
from pcopy import dashboard_live


def test_get_cowsay_art_fallback(monkeypatch):
    # Make cowsay_art raise to exercise fallback
    def fake_cowsay(*a, **k):
        raise RuntimeError('boom')

    monkeypatch.setattr(dashboard_live, 'cowsay_art', fake_cowsay)
    d = LiveDashboard(test_mode=True)
    d.cow_quote = 'hello'
    d.progress = 42
    art = d._get_cowsay_art()
    assert '(42%)' in art


def test_update_slogan_console_height_and_animals(monkeypatch):
    d = LiveDashboard(test_mode=True)
    # set STAGES to force animals/quotes for stage1
    monkeypatch.setattr(dashboard_live, 'STAGES', {'stage1': {'animals': ['guardkitten'], 'quotes': ['q1']}})
    # replace console with a lightweight fake that has a .size.height attribute
    d.console = types.SimpleNamespace(size=types.SimpleNamespace(width=80, height=100))
    d.progress = 10
    d._update_slogan()
    assert d.cow_character in ('guardkitten',)
    assert d.cow_quote in ('q1',) or d.cow_quote in dashboard_live.CAT_FACTS


def test_progress_bar_update_exception(monkeypatch):
    d = LiveDashboard(test_mode=True)
    # monkeypatch the progress_bar.update to raise
    def bad_update(*a, **k):
        raise RuntimeError('update fail')

    monkeypatch.setattr(d.progress_bar, 'update', bad_update)
    # call update_from_rsync_line to trigger progress update
    d.update_from_rsync_line('23% 0.1MB/s 0:00:01')
    # should not raise
    assert d.progress == 23


def test_run_demo_shortened_and_deterministic(monkeypatch):
    # With PCOPY_TEST_MODE=1 demo should be fast and deterministic
    monkeypatch.setenv('PCOPY_TEST_MODE', '1')
    d = LiveDashboard(test_mode=False)
    # Ensure run_demo runs quickly
    start = time.time()
    d.run_demo(duration=0.5)
    elapsed = time.time() - start
    assert elapsed < 2.0
    # deterministic seed should produce same quote on repeated runs
    q1 = d.cow_quote
    d2 = LiveDashboard(test_mode=False)
    monkeypatch.setenv('PCOPY_TEST_MODE', '1')
    d2.run_demo(duration=0.5)
    assert q1 == d2.cow_quote
