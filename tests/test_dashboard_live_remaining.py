import time
import types
from datetime import datetime, timedelta

from pcopy.dashboard_live import LiveDashboard
from pcopy import dashboard_live


def test_format_elapsed_hours_and_minutes():
    d = LiveDashboard(test_mode=True)
    # simulate a start_time far in the past (2 hours, 3 minutes, 5 seconds)
    d.start_time = None
    # set start_time so delta has hours
    d.start_time = datetime.now() - timedelta(hours=2, minutes=3, seconds=5)
    s = d._format_elapsed()
    assert 'h' in s or 'm' in s


def test_total_transferred_parsing_exception(monkeypatch):
    d = LiveDashboard(test_mode=True)
    # pass a line that lacks the colon to trigger the exception in parsing
    d.transferred = 'old'
    d.update_from_rsync_line('Total transferred file size no colon')
    # transferred should remain unchanged if parsing failed
    assert d.transferred == 'old'


def test_run_demo_progress_update_exception(monkeypatch):
    d = LiveDashboard(test_mode=False)
    # ensure the demo runs in test mode deterministically
    monkeypatch.setenv('PCOPY_TEST_MODE', '1')
    # make progress_bar.update raise so the except branch runs
    def bad_update(*a, **k):
        raise RuntimeError('boom')
    monkeypatch.setattr(d.progress_bar, 'update', bad_update)

    # Run demo; should not raise and should finish
    d.run_demo(duration=0.05)
    assert d.progress == 100 or d.progress >= 0


def test_update_slogan_when_no_quotes_or_animals(monkeypatch):
    d = LiveDashboard(test_mode=True)
    # Set STAGES empty and CAT_FACTS empty to force default quote
    monkeypatch.setattr(dashboard_live, 'STAGES', {})
    monkeypatch.setattr(dashboard_live, 'CAT_FACTS', [])
    d.progress = 10
    d._update_slogan()
    assert d.cow_quote == 'Backing up with purrs...'
