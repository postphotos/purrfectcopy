import os
import shlex
from types import SimpleNamespace

import pytest

from pcopy import runner
import pcopy.config as config


def test_build_rsync_cmd_variants():
    assert 'rsync' in runner._build_rsync_cmd('a', 'b')
    cmd = runner._build_rsync_cmd('src', 'dst', dry_run=True, extra=['--delete'])
    assert '--dry-run' in cmd
    assert '--delete' in cmd
    assert cmd[-2:] == ['src', 'dst']


def test_run_backup_demo_invokes_run_demo(monkeypatch):
    called = {}

    def fake_run_demo(self, *a, **k):
        called['demo'] = True

    monkeypatch.setattr(runner.LiveDashboard, 'run_demo', fake_run_demo)
    # Should return 0 and call run_demo
    rc = runner.run_backup(source='s', dest='d', demo=True, name=None, persist_last_run=False)
    assert rc == 0
    assert called.get('demo') is True


def test_run_backup_rsync_missing_streaming(monkeypatch):
    # Ensure we take the streaming path (remove PYTEST_CURRENT_TEST)
    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising=False)
    # make Popen raise FileNotFoundError
    def bad_popen(*a, **k):
        raise FileNotFoundError()
    monkeypatch.setattr(runner.subprocess, 'Popen', bad_popen)
    rc = runner.run_backup(source='s', dest='d', name=None, persist_last_run=False)
    assert rc == 2


def test_run_backup_rsync_missing_synchronous(monkeypatch):
    monkeypatch.setenv('PYTEST_CURRENT_TEST', '1')
    def bad_run(*a, **k):
        raise FileNotFoundError()
    monkeypatch.setattr(runner.subprocess, 'run', bad_run)
    rc = runner.run_backup(source='s', dest='d', name=None, persist_last_run=False)
    assert rc == 2


def test_main_do_missing_name_returns_2(monkeypatch, tmp_path):
    # Ensure settings do not contain the named backup
    monkeypatch.setattr(config, 'SETTINGS', {})
    rc = runner.main(['do', 'no-such-name'])
    assert rc == 2


def test_main_run_compat_calls_run_backup(monkeypatch):
    recorded = {}

    def fake_run_backup(source=None, dest=None, **kwargs):
        recorded.update({'source': source, 'dest': dest})
        return 0

    monkeypatch.setattr(runner, 'run_backup', fake_run_backup)
    # Simulate CLI-supplied kwargs (includes an extra unknown 'demo' param)
    import inspect
    cli_kwargs = {'source': 's', 'dest': 'd', 'demo': True}
    call_kwargs = {k: v for k, v in cli_kwargs.items() if k in inspect.signature(runner.run_backup).parameters}
    runner.run_backup(**call_kwargs)
    assert recorded.get('source') == 's'
    assert recorded.get('dest') == 'd'
