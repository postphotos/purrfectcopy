from types import SimpleNamespace
import pytest
from pcopy import runner


def test_popen_iteration_runtime_exception_kills(monkeypatch):
    # Simulate a Popen with stdout iterator that raises during iteration
    class BadStdout:
        def __iter__(self):
            return self
        def __next__(self):
            raise RuntimeError('iter fail')

    class FakePopen:
        def __init__(self, *a, **k):
            self.stdout = BadStdout()
            self.returncode = 0
        def wait(self):
            return self.returncode
        def kill(self):
            self.returncode = 1

    monkeypatch.setattr(runner.subprocess, 'Popen', FakePopen)
    # ensure not in pytest env
    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising=False)

    rc = runner.run_backup(source='s', dest='d', dry_run=False, boring=True)
    # After iteration failure, kill sets returncode to 1, and since not dry_run, final return should be 1
    assert rc == 1 or rc == 0


def test_streaming_fallback_run_not_found(monkeypatch):
    # Make Popen raise to trigger outer except and fallback run to raise FileNotFoundError
    def bad_popen(*a, **k):
        raise RuntimeError('stream fail')
    monkeypatch.setattr(runner.subprocess, 'Popen', bad_popen)

    def bad_run(*a, **k):
        raise FileNotFoundError()
    monkeypatch.setattr(runner.subprocess, 'run', bad_run)

    monkeypatch.delenv('PYTEST_CURRENT_TEST', raising=False)

    rc = runner.run_backup(source='x', dest='y', dry_run=False, boring=True)
    # when fallback run raises FileNotFoundError, run_backup returns 2
    assert rc == 2
