import os
import time
import yaml
from types import SimpleNamespace
from pathlib import Path

import pytest

from pcopy import runner
import pcopy.config as config


# Helper to write a temporary settings.yml for tests
def _write_tmp_settings(tmp_path):
    yaml_path = tmp_path / 'settings.yml'
    settings = {'jobA': {'source': 's', 'dest': 'd'}}
    yaml_path.write_text(yaml.safe_dump(settings), encoding='utf8')
    return yaml_path


class _FakeProc:
    def __init__(self, lines):
        # stdout should be an iterable of lines
        self.stdout = list(lines)
        self.returncode = 0

    def wait(self):
        return 0

    def communicate(self, input=None, timeout=None):
        # Return stdout as a single string and None for stderr
        return ('\n'.join(self.stdout), None)

    def kill(self):
        # emulate killing the process
        self.returncode = -9

    # make this object usable as a context manager in case code uses 'with'
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_streaming_popen_persists(tmp_path, monkeypatch):
    yaml_path = _write_tmp_settings(tmp_path)
    monkeypatch.setattr(config, 'SETTINGS_PATH', yaml_path)
    monkeypatch.setenv('PCOPY_SETTINGS_PATH', str(yaml_path))
    # Ensure streaming Popen path is used
    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising=False)
    # Provide a fake Popen that yields rsync-like lines
    lines = [
        ' 10% 0.12MB/s 0:00:01\n',
        '>f+++++++++ demo/file1.txt\n',
        'Total transferred file size: 12345 bytes\n',
    ]

    def fake_popen(cmd, stdout, stderr, text):
        return _FakeProc(lines)

    monkeypatch.setattr(runner.subprocess, 'Popen', fake_popen)
    # Set BACKUP_VERSIONS_DIR and create a file to test dupes_saved detection
    bv = tmp_path / 'versions'
    bv.mkdir()
    config.BACKUP_VERSIONS_DIR = bv
    # create a file with mtime >= now
    f = bv / 'recent.txt'
    f.write_text('x')
    os.utime(str(f), None)

    rc = runner.run_backup(source='s', dest='d', name='jobA', persist_last_run=True)
    assert rc == 0
    loaded = yaml.safe_load(yaml_path.read_text(encoding='utf8'))
    lr = loaded['jobA']['last_run']
    assert lr['status'] == 0
    assert lr['transferred_bytes'] == 12345
    assert lr['dupes_saved'] in (True, False)


def test_fallback_run_persists(tmp_path, monkeypatch):
    yaml_path = _write_tmp_settings(tmp_path)
    monkeypatch.setattr(config, 'SETTINGS_PATH', yaml_path)
    monkeypatch.setenv('PCOPY_SETTINGS_PATH', str(yaml_path))
    # Force streaming Popen to raise to trigger outer except fallback
    def bad_popen(*a, **k):
        raise RuntimeError('stream fail')
    monkeypatch.setattr(runner.subprocess, 'Popen', bad_popen)

    # Make fallback run return a non-zero code but with stdout
    def fake_run(cmd, **kwargs):
        return SimpleNamespace(returncode=0, stdout='Total transferred file size: 9999 bytes')
    monkeypatch.setattr(runner.subprocess, 'run', fake_run)

    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising=False)
    rc = runner.run_backup(source='s', dest='d', name='jobA', persist_last_run=True)
    assert rc == 0
    loaded = yaml.safe_load(yaml_path.read_text(encoding='utf8'))
    lr = loaded['jobA']['last_run']
    assert lr['status'] == 0
    assert lr['transferred_bytes'] == 9999


def test_yaml_write_failure_is_handled(tmp_path, monkeypatch):
    yaml_path = _write_tmp_settings(tmp_path)
    monkeypatch.setattr(config, 'SETTINGS_PATH', yaml_path)
    monkeypatch.setenv('PCOPY_SETTINGS_PATH', str(yaml_path))

    # Monkeypatch the writer to raise
    def broken_writer(name, entry):
        raise OSError('disk full')
    monkeypatch.setattr(runner, '_write_last_run_yaml_ml', broken_writer)

    # Ensure we don't call real rsync: stub subprocess.run
    monkeypatch.setattr(runner.subprocess, 'run', lambda *a, **k: SimpleNamespace(returncode=0, stdout=''))

    rc = runner.run_backup(source='s', dest='d', name='jobA', persist_last_run=True)
    assert rc == 0
    # file should be unchanged because writer raised
    loaded = yaml.safe_load(yaml_path.read_text(encoding='utf8'))
    assert 'last_run' not in loaded['jobA']
