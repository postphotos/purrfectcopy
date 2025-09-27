import time
import types
import pytest

from pcopy import dashboard_live
from pcopy.dashboard_live import LiveDashboard


def test_get_cowsay_art_uses_cache(monkeypatch):
    d = LiveDashboard(test_mode=True)
    d._cached_cow_art = 'CACHED'
    d._last_cow_change = time.time()
    # make cowsay_art raise if called — cached path should avoid calling it
    def bad_cowsay(*a, **k):
        raise RuntimeError('should not be called')
    monkeypatch.setattr(dashboard_live, 'cowsay_art', bad_cowsay)
    assert d._get_cowsay_art() == 'CACHED'


def test_update_slogan_stage2_and_stage3(monkeypatch):
    d = LiveDashboard(test_mode=True)
    # Provide stages for stage2 and stage3
    monkeypatch.setattr(dashboard_live, 'STAGES', {
        'stage2': {'animals': ['guardkitten'], 'quotes': ['s2']},
        'stage3': {'animals': ['rsyncat'], 'quotes': ['s3']}
    })
    d.progress = 50
    d._update_slogan()
    assert d.cow_character in ('guardkitten',)
    assert d.cow_quote in ('s2',) or d.cow_quote in dashboard_live.CAT_FACTS

    d.progress = 80
    d._update_slogan()
    assert d.cow_character in ('rsyncat',)
    assert d.cow_quote in ('s3',) or d.cow_quote in dashboard_live.CAT_FACTS


def test_update_slogan_no_stages_or_quotes(monkeypatch):
    d = LiveDashboard(test_mode=True)
    # remove STAGES and ensure fallback quote used when no quotes
    monkeypatch.setattr(dashboard_live, 'STAGES', None)
    monkeypatch.setattr(dashboard_live, 'CAT_FACTS', [])
    d.progress = 10
    d._update_slogan()
    assert d.cow_quote == 'Backing up with purrs...'


def test_start_live_enter_exception(monkeypatch):
    # Simulate Live.__enter__ raising to exercise start() exception handling
    called = {}
    class FakeLive:
        def __init__(self, *a, **k):
            pass
        def __enter__(self):
            raise RuntimeError('enter fail')
    monkeypatch.setattr(dashboard_live, 'Live', FakeLive)
    d = LiveDashboard(test_mode=False)
    d.start()
    # start should not raise and _live should be None when enter fails
    assert d._live is None


def test_finish_exit_exception_does_not_propagate(monkeypatch, capsys):
    d = LiveDashboard(test_mode=True)
    # craft a fake _live with __exit__ raising
    class BadLive:
        def __exit__(self, *a):
            raise RuntimeError('exit bad')
    d._live = BadLive()
    # ensure finish handles __exit__ exception gracefully
    d.finish(0)
    out = capsys.readouterr().out
    assert 'Purrfect Success' in out or 'Complete' in out
