import subprocess
from types import SimpleNamespace

import pytest

from pcopy import runner


def test_build_rsync_cmd_defaults():
    cmd = runner._build_rsync_cmd('a', 'b')
    assert 'rsync' in cmd[0]
    assert '--info=progress2' in cmd


def test_run_backup_rsync_missing(monkeypatch, capsys):
    # Simulate subprocess.run raising FileNotFoundError
    def fake_run(*a, **k):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, 'run', fake_run)
    rc = runner.run_backup(source='s', dest='d', dry_run=False, boring=True)
    # run_backup should return 2 when rsync not found
    assert rc == 2


def test_run_backup_nonzero_return(monkeypatch):
    class P:
        def __init__(self):
            self.returncode = 3
            self.stdout = ''

    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: P())
    rc = runner.run_backup(source='s', dest='d', dry_run=False, boring=True)
    assert rc == 3


def test_run_backup_dry_run_ignores_nonzero(monkeypatch):
    class P:
        def __init__(self):
            self.returncode = 5
            self.stdout = 'progress'

    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: P())
    rc = runner.run_backup(source='s', dest='d', dry_run=True, boring=True)
    assert rc == 0


def test_main_demo_when_run_backup_monkeypatched(monkeypatch):
    # If run_backup is monkeypatched and doesn't accept demo kwarg, main should still work
    def fake_run_backup(source=None, dest=None, dry_run=False, boring=False):
        return 0

    monkeypatch.setattr(runner, 'run_backup', fake_run_backup)
    rc = runner.main(['--demo'])
    assert rc == 0
