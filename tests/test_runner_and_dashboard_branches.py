import subprocess
from types import SimpleNamespace
import builtins

import pytest

from pcopy import runner
from pcopy.dashboard_live import LiveDashboard
import pcopy.dashboard_live as dl
import pcopy.config as config


def test_popen_file_not_found_when_run_missing(monkeypatch):
    # Make subprocess.run raise AttributeError to trigger Popen fallback
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: (_ for _ in ()).throw(AttributeError('no run')))

    # Popen raises FileNotFoundError
    def fake_popen(*a, **k):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, 'Popen', fake_popen)
    rc = runner.run_backup(source='s', dest='d', dry_run=False)
    assert rc == 2


def test_popen_iteration_exception_kills_process(monkeypatch):
    # Force subprocess.run to raise AttributeError to get to Popen fallback
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: (_ for _ in ()).throw(AttributeError('no run')))

    class BadStdout:
        def __iter__(self):
            return self

        def __next__(self):
            raise RuntimeError('iteration error')

    class FakePopen:
        def __init__(self, *a, **k):
            self.stdout = BadStdout()
            self.returncode = 0

        def wait(self):
            return self.returncode

        def kill(self):
            self.returncode = 1

    monkeypatch.setattr(subprocess, 'Popen', FakePopen)
    rc = runner.run_backup(source='s', dest='d', dry_run=False)
    assert rc == 1


def test_get_cowsay_art_handles_exception(monkeypatch):
    dash = LiveDashboard(test_mode=True)
    dash.progress = 42
    dash.cow_quote = 'z'
    # cowsay_art raises
    monkeypatch.setattr('pcopy.dashboard_live.cowsay_art', lambda t, c: (_ for _ in ()).throw(RuntimeError('boom')))
    out = dash._get_cowsay_art()
    assert '(' in out and '42' in out


def test_update_slogan_picks_stage_and_cat_facts(monkeypatch):
    dash = LiveDashboard(test_mode=True)
    # Provide STAGES mapping with animals and quotes
    monkeypatch.setattr(dl, 'STAGES', {
        'stage1': {'animals': ['a1'], 'quotes': ['q1']},
        'stage2': {'animals': ['a2'], 'quotes': ['q2']},
        'stage3': {'animals': ['a3'], 'quotes': ['q3']},
    }, raising=False)
    # make console appear large so CAT_FACTS are considered
    from collections import namedtuple
    ConsoleSize = namedtuple('ConsoleSize', ['width', 'height'])
    monkeypatch.setattr(dash.console, 'size', ConsoleSize(120, 100))
    dash.progress = 90
    dash._update_slogan()
    assert dash.cow_character in ['a3']
    # cow_quote may come from stage quotes or the global cat facts; ensure it's non-empty
    assert isinstance(dash.cow_quote, str) and dash.cow_quote


def test_start_enters_live_on_success(monkeypatch):
    # Replace Live with a dummy context manager that succeeds
    class DummyLive:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    monkeypatch.setattr(dl, 'Live', DummyLive)
    dash = LiveDashboard(test_mode=False, demo_mode=False)
    dash.start()
    assert dash._live is not None
    # teardown should not raise
    dash.finish(0)


def test_finish_failure_shows_errors(capsys):
    dash = LiveDashboard(test_mode=True)
    dash.errors = ['err1', 'err2']
    dash.finish(3)
    captured = capsys.readouterr()
    assert 'Oh no' in captured.out or '😿' in captured.out
