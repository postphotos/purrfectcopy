import importlib
import subprocess
from types import SimpleNamespace

import pcopy.runner as runner


def test_run_backup_file_not_found(monkeypatch):
    # Simulate rsync binary missing
    def fake_run(*args, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, 'run', fake_run)

    rc = runner.run_backup(source='a', dest='b', dry_run=False, boring=True)
    assert rc == 2


def test_run_backup_rsync_failure(monkeypatch):
    # Simulate rsync returning non-zero when not a dry-run
    def fake_run(cmd, **kwargs):
        return SimpleNamespace(returncode=3, stdout='error')

    monkeypatch.setattr(subprocess, 'run', fake_run)

    rc = runner.run_backup(source='a', dest='b', dry_run=False, boring=True)
    assert rc == 3


def test_run_backup_dry_run_ignores_error(monkeypatch):
    # Even if rsync returns non-zero, dry-run should still return 0
    def fake_run(cmd, **kwargs):
        return SimpleNamespace(returncode=5, stdout='progress')

    monkeypatch.setattr(subprocess, 'run', fake_run)

    rc = runner.run_backup(source='a', dest='b', dry_run=True, boring=True)
    assert rc == 0
import subprocess
from pcopy.runner import run_backup, _build_rsync_cmd


def test_build_rsync_cmd_extra():
    cmd = _build_rsync_cmd('a', 'b', dry_run=True, extra=['--verbose'])
    assert '--dry-run' in cmd
    assert '--verbose' in cmd


def test_run_backup_rsync_missing(monkeypatch):
    # simulate FileNotFoundError from subprocess.run
    def fake_run(*a, **k):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, 'run', fake_run)
    rc = run_backup(source='s', dest='d', dry_run=False, boring=True)
    assert rc == 2


def test_run_backup_rsync_nonzero_return(monkeypatch):
    class P:
        def __init__(self):
            self.returncode = 2
            self.stdout = ''

    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: P())
    rc = run_backup(source='s', dest='d', dry_run=False, boring=True)
    assert rc == 2
