import json
import subprocess
import time
from types import SimpleNamespace
from pathlib import Path

import pytest

import pcopy.config as config
from pcopy.dashboard_live import LiveDashboard
from pcopy import runner


def test_run_backup_demo_uses_dashboard(monkeypatch):
    called = {}

    def fake_run_demo(self, *a, **k):
        called['demo'] = True

    monkeypatch.setattr(LiveDashboard, 'run_demo', fake_run_demo)
    rc = runner.run_backup(source='s', dest='d', demo=True)
    assert rc == 0
    assert called.get('demo')


def test_run_backup_popen_fallback(monkeypatch):
    # Force subprocess.run to raise AttributeError to trigger Popen fallback
    def fake_run(*a, **k):
        raise AttributeError('simulate missing run')

    monkeypatch.setattr(subprocess, 'run', fake_run)

    class FakePopen:
        def __init__(self, *a, **k):
            self.stdout = iter([b'23% 0.1MB/s\n', b'>f+++++++++ a/file.txt\n'])
            self.returncode = 0

        def wait(self):
            return self.returncode

        def kill(self):
            self.returncode = 1

    # Popen should accept text=True so strings; make stdout yield strings
    class FakePopenText(FakePopen):
        def __init__(self, *a, **k):
            self.stdout = iter(['23% 0.1MB/s\n', '>f+++++++++ a/file.txt\n'])
            self.returncode = 0

    monkeypatch.setattr(subprocess, 'Popen', FakePopenText)

    rc = runner.run_backup(source='s', dest='d', dry_run=False)
    assert rc == 0

    # Now simulate non-zero return
    class FakePopenFail(FakePopenText):
        def __init__(self, *a, **k):
            super().__init__()
            self.returncode = 7

    monkeypatch.setattr(subprocess, 'Popen', FakePopenFail)
    rc2 = runner.run_backup(source='s', dest='d', dry_run=False)
    assert rc2 == 7


def test_dashboard_helpers_and_finish(capsys, monkeypatch):
    dash = LiveDashboard(test_mode=True, cow_hold_seconds=1)
    # monkeypatch cowsay_art so it's deterministic
    monkeypatch.setattr('pcopy.dashboard_live.cowsay_art', lambda text, cow: f'cow:{cow}:{text}')

    dash.progress = 10
    dash.cow_quote = 'hello'
    first = dash._get_cowsay_art()
    second = dash._get_cowsay_art()
    assert first == second  # cached because within hold seconds

    # files bar without total_files
    fb = dash._files_bar(width=10)
    assert 'files' in str(fb)

    # set total_files and test bar label
    dash.total_files = 5
    dash.files_moved_count = 2
    fb2 = dash._files_bar(width=10)
    assert '2/5' in str(fb2)

    # start and finish should print messages
    dash.start()
    dash.finish(0)
    dash.finish(3)


def test_reload_settings_reads_slogans(tmp_path, monkeypatch):
    # Create a temporary slogans JSON and point SLOGANS_PATH to it
    data = {'quotes': ['q1'], 'cat_facts': ['cf1']}
    p = tmp_path / 'slogans.json'
    p.write_text(json.dumps(data), encoding='utf8')
    monkeypatch.setattr(config, 'SLOGANS_PATH', p)
    # Ensure SETTINGS_PATH doesn't interfere
    monkeypatch.setattr(config, 'SETTINGS_PATH', tmp_path / 'notexist.yml')
    config.reload_settings()
    assert 'q1' in config.SLOGANS
    assert 'cf1' in config.CAT_FACTS
