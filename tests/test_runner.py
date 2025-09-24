import subprocess
from pcopy.runner import _build_rsync_cmd, run_backup


def test_build_rsync_cmd_default():
    cmd = _build_rsync_cmd('s', 'd')
    assert 'rsync' in cmd[0]


def test_run_backup_dry_run(monkeypatch):
    # simulate subprocess.run during dry-run
    class P:
        def __init__(self):
            self.returncode = 0
            self.stdout = ''
    monkeypatch.setattr(subprocess, 'run', lambda *a, **k: P())
    rc = run_backup(source='s', dest='d', dry_run=True, boring=True)
    assert rc == 0
