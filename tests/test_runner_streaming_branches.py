import os
import types
import time
from types import SimpleNamespace

import pytest
from pcopy import runner


def test_pcopy_test_mode_simulated_stream(monkeypatch, capsys):
    monkeypatch.setenv('PCOPY_TEST_MODE', '1')
    rc = runner.run_backup(source='a', dest='b', dry_run=False, boring=True)
    assert rc == 0
    out = capsys.readouterr().out
    assert 'Backup complete' in out or 'Purrfect Success' in out


def test_pytest_run_path_file_not_found(monkeypatch, capsys):
    # simulate running under pytest env
    monkeypatch.setenv('PYTEST_CURRENT_TEST', '1')

    def fake_run(*a, **k):
        raise FileNotFoundError()

    monkeypatch.setattr(runner.subprocess, 'run', fake_run)

    rc = runner.run_backup(source='s', dest='d', dry_run=False, boring=True)
    # when run raises FileNotFoundError we expect rc == 2
    assert rc == 2


def test_popen_file_not_found(monkeypatch, capsys):
    # ensure not in pytest path
    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising=False)

    def fake_popen(*a, **k):
        raise FileNotFoundError()

    monkeypatch.setattr(runner.subprocess, 'Popen', fake_popen)

    rc = runner.run_backup(source='x', dest='y', dry_run=False, boring=True)
    assert rc == 2


def test_popen_nonzero_return(monkeypatch, capsys):
    # Not under pytest env; simulate a Popen that yields lines and returns non-zero
    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising=False)

    class FakePopen:
        def __init__(self, *a, **k):
            self.stdout = iter(['10% 0.1MB/s\n', '>f+++++++++ a/file.txt\n'])
            self.returncode = 2

        def wait(self):
            return self.returncode

        def kill(self):
            self.returncode = 1

    monkeypatch.setattr(runner.subprocess, 'Popen', FakePopen)

    rc = runner.run_backup(source='s', dest='d', dry_run=False, boring=True)
    # when Popen returns non-zero and not dry_run, run_backup returns that code
    assert rc == 2
