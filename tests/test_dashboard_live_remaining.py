import time
import types
import sys
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


def test_files_bar_with_total_files():
    d = LiveDashboard(test_mode=True)
    d.total_files = 10
    d.files_moved_count = 4
    tb = d._files_bar(width=20)
    assert '4/10' in tb.plain


def test_get_cowsay_art_exception_path(monkeypatch):
    # Simulate cowsay_art raising so _get_cowsay_art uses fallback string
    def bad_cowsay(msg, animal):
        raise RuntimeError('boom')
    monkeypatch.setattr(dashboard_live, 'cowsay_art', bad_cowsay)
    d = LiveDashboard(test_mode=True)
    d.progress = 55
    s = d._get_cowsay_art()
    assert '(55%)' in s


def test_update_from_rsync_line_duplicate_and_speed(monkeypatch, caplog):
    d = LiveDashboard(test_mode=True)
    caplog.set_level('WARNING')
    # capture warnings through logger
    d.logger = types.SimpleNamespace(warning=lambda *a, **k: caplog.warning(' '.join(map(str, a))))
    d.update_from_rsync_line('>f+++++++++ demo/x.txt')
    assert d.files_moved_count == 1
    # duplicate
    d.update_from_rsync_line('>f+++++++++ demo/x.txt')
    assert d.duplicates == 1
    # speed parsing
    d.update_from_rsync_line(' 75% 1.23MB/s 0:00:02')
    assert 'MB/s' in d.speed


def test_finish_dry_run_pauses_when_not_under_pytest(monkeypatch):
    d = LiveDashboard(test_mode=False, demo_mode=False, dry_run=True)
    d.files_moved_count = 1
    d.transferred = '1 byte'
    d.errors = []
    # make stdin appear as TTY
    class FakeStdin:
        def isatty(self):
            return True
    monkeypatch.setattr('sys.stdin', FakeStdin())
    # remove pytest from sys.modules temporarily
    monkeypatch.delitem(sys.modules, 'pytest', raising=False)
    # monkeypatch sleep to no-op
    monkeypatch.setattr('time.sleep', lambda s: None)
    # should not raise
    d.finish(0)


def test_finish_handles_logger_exceptions(monkeypatch):
    d = LiveDashboard(test_mode=False, demo_mode=False, dry_run=False)
    d.files_moved_count = 1
    d.transferred = '0 bytes'
    d.errors = ['e1', 'e2']
    # logger whose methods raise to hit the except: pass branch
    class BadLogger:
        def info(self, *a, **k):
            raise RuntimeError('boom')
        def error(self, *a, **k):
            raise RuntimeError('boom')
    d.logger = BadLogger()
    # should not raise
    d.finish(1)


def test_finish_pause_handles_keyboardinterrupt(monkeypatch):
    d = LiveDashboard(test_mode=False, demo_mode=False, dry_run=True)
    d.files_moved_count = 0
    d.transferred = ''
    d.errors = []
    # TTY
    class FakeStdin:
        def isatty(self):
            return True
    monkeypatch.setattr('sys.stdin', FakeStdin())
    # remove pytest key
    monkeypatch.delitem(sys.modules, 'pytest', raising=False)
    # make sleep raise KeyboardInterrupt
    def raise_kb(s):
        raise KeyboardInterrupt()
    monkeypatch.setattr('time.sleep', raise_kb)
    # should not raise
    d.finish(0)


def test_update_from_rsync_line_logger_warning_raises(monkeypatch):
    d = LiveDashboard(test_mode=True)
    # logger with warning method that raises
    class BadLogger:
        def warning(self, *a, **k):
            raise RuntimeError('boom')
    d.logger = BadLogger()
    # first time add
    d.update_from_rsync_line('>f+++++++++ some/file.txt')
    # second time should attempt to call logger.warning and hit exception handler
    d.update_from_rsync_line('>f+++++++++ some/file.txt')


def test_update_slogan_handles_console_size_exception(monkeypatch):
    d = LiveDashboard(test_mode=True)
    # console.size access raises
    class BadConsole:
        @property
        def size(self):
            raise RuntimeError('boom')
    d.console = BadConsole()
    # should not raise
    d._update_slogan()
