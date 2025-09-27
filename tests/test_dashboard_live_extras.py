import time
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest

from pcopy.dashboard_live import LiveDashboard
from pcopy import runner
import pcopy.dashboard_live as dl


def test_format_elapsed_variations():
    dash = LiveDashboard(test_mode=True)
    # seconds
    dash.start_time = datetime.now() - timedelta(seconds=5)
    assert 's' in dash._format_elapsed()

    # minutes
    dash.start_time = datetime.now() - timedelta(minutes=3, seconds=5)
    assert 'm' in dash._format_elapsed()

    # hours
    dash.start_time = datetime.now() - timedelta(hours=2, minutes=5, seconds=3)
    assert 'h' in dash._format_elapsed()


def test_get_cowsay_cache_rotation(monkeypatch):
    calls = {'n': 0}

    def fake_cowsay(text, cow):
        calls['n'] += 1
        return f"{cow}:{text}:{calls['n']}"

    monkeypatch.setattr('pcopy.dashboard_live.cowsay_art', fake_cowsay)
    dash = LiveDashboard(test_mode=True, cow_hold_seconds=1)
    dash.progress = 10
    dash.cow_quote = 'q'
    a = dash._get_cowsay_art()
    b = dash._get_cowsay_art()
    assert a == b  # cached
    time.sleep(1.1)
    c = dash._get_cowsay_art()
    assert c != b


def test_start_handles_live_exception(monkeypatch):
    class FaultyLive:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            raise RuntimeError('no live')

    monkeypatch.setattr(dl, 'Live', FaultyLive)
    dash = LiveDashboard(test_mode=False)
    dash.start()
    assert dash._live is None


def test_progress_bar_update_exception(monkeypatch):
    dash = LiveDashboard(test_mode=True)
    # make progress_bar.update raise
    def bad_update(*a, **k):
        raise RuntimeError('bad')

    monkeypatch.setattr(dash, 'progress_bar', SimpleNamespace(update=bad_update))
    # should not raise
    dash.update_from_rsync_line('50%')


def test_runner_main_interactive_calls_show_menu(monkeypatch):
    # Simulate TTY and short argv to trigger _show_menu
    monkeypatch.setattr('sys.stdin.isatty', lambda: True)
    monkeypatch.setattr('sys.argv', ['pcopy'])
    called = {}

    def fake_menu():
        called['ok'] = True
        return 77

    monkeypatch.setattr(runner, '_show_menu', fake_menu)
    rc = runner.main(None)
    assert rc == 77
    assert called.get('ok')


def test_build_rsync_cmd_with_extra():
    cmd = runner._build_rsync_cmd('s', 'd', dry_run=True, extra=['--exclude=.git'])
    assert '--dry-run' in cmd
    assert '--exclude=.git' in cmd
