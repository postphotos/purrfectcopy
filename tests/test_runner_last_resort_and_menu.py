import builtins
from types import SimpleNamespace
import pytest

from pcopy import runner


def test_streaming_outer_exception_falls_back_to_run(monkeypatch):
    # Force streaming Popen to raise to trigger outer except fallback
    def bad_popen(*a, **k):
        raise RuntimeError('stream fail')
    monkeypatch.setattr(runner.subprocess, 'Popen', bad_popen)

    # Make fallback run return a non-zero code
    def fake_run(*a, **k):
        return SimpleNamespace(returncode=7, stdout='err')
    monkeypatch.setattr(runner.subprocess, 'run', fake_run)

    # Ensure not under pytest env so streaming is attempted
    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising=False)

    rc = runner.run_backup(source='x', dest='y', dry_run=False, boring=True)
    assert rc == 7


def test_show_menu_quit(monkeypatch):
    # Simulate prompt.ask returning 'q' once
    responses = ['q']
    def fake_ask(prompt, default=None):
        return responses.pop(0)
    # Monkeypatch the underlying Prompt.ask used inside _show_menu
    monkeypatch.setattr('rich.prompt.Prompt.ask', fake_ask)
    rc = runner._show_menu()
    assert rc == 0


def test_show_menu_custom(monkeypatch):
    # Simulate choosing custom path: first ask returns 'c', then source/dest
    seq = ['c', 'my-src', 'my-dest']
    def fake_ask(prompt, default=None):
        return seq.pop(0)
    monkeypatch.setattr('rich.prompt.Prompt.ask', fake_ask)

    # Monkeypatch run_backup so we don't actually run rsync
    called = {}
    def fake_run_backup(source=None, dest=None, dry_run=False, boring=False):
        called['src'] = source
        called['dst'] = dest
        return 0
    monkeypatch.setattr(runner, 'run_backup', fake_run_backup)

    rc = runner._show_menu()
    assert rc == 0
    assert called['src'] == 'my-src'
    assert called['dst'] == 'my-dest'
