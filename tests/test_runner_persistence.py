import yaml
import pytest
from types import SimpleNamespace
from pathlib import Path

from pcopy import runner
import pcopy.config as config


def test_persist_last_run_fields(tmp_path, monkeypatch):
    # Create settings YAML with a named job
    yaml_path = tmp_path / 'settings.yml'
    settings = {'jobA': {'source': 's', 'dest': 'd'}}
    yaml_path.write_text(yaml.safe_dump(settings), encoding='utf8')

    # Point the app at the temporary settings file
    monkeypatch.setattr(config, 'SETTINGS_PATH', yaml_path)
    # Also set env var so runner will pick up the test settings path for persistence
    monkeypatch.setenv('PCOPY_SETTINGS_PATH', str(yaml_path))

    # Ensure env_test code path with deterministic simulated rsync output
    monkeypatch.setenv('PCOPY_TEST_MODE', '1')

    # Run the named job and persist last_run
    rc = runner.run_backup(source='s', dest='d', name='jobA', persist_last_run=True)
    assert rc == 0

    # Read the settings file and assert last_run metadata saved
    loaded = yaml.safe_load(yaml_path.read_text(encoding='utf8'))
    assert 'jobA' in loaded
    lr = loaded['jobA'].get('last_run')
    assert lr is not None
    # Required fields
    for key in ('timestamp', 'status', 'status_str', 'transferred_bytes', 'elapsed_seconds'):
        assert key in lr
    # transferred_bytes should be parsed from the simulated output
    assert isinstance(lr['transferred_bytes'], int)
    assert lr['transferred_bytes'] >= 0
    # status_str should reflect success for simulated run
    assert lr['status_str'] == 'PASS'


def test_menu_shows_columns(monkeypatch, capsys):
    # Ensure the menu prints new columns even when quitting immediately
    monkeypatch.setattr(config, 'SETTINGS', {'job1': {'source': 'sx', 'dest': 'dx'}})
    monkeypatch.setattr('rich.prompt.Prompt.ask', lambda *a, **k: 'q')

    runner._show_menu()
    out = capsys.readouterr().out
    # Check for requested columns
    assert '# ' in out or '\n#' in out
    assert 'Name' in out
    assert 'Source' in out
    assert 'Dest' in out
    assert 'Last Ran' in out
    assert 'Outcome' in out
    assert 'Size' in out
    assert 'Duration' in out
