import os
import yaml
from datetime import datetime, timedelta
from types import SimpleNamespace
from pathlib import Path

import pytest

from pcopy import runner
import pcopy.config as config


def _write_tmp_settings(tmp_path, name='jobX'):
    yaml_path = tmp_path / 'settings.yml'
    settings = {name: {'source': 's', 'dest': 'd'}}
    yaml_path.write_text(yaml.safe_dump(settings), encoding='utf8')
    return yaml_path


def test_mark_run_running_creates_entry(tmp_path):
    yaml_path = _write_tmp_settings(tmp_path, name='job_running')
    os.environ['PCOPY_SETTINGS_PATH'] = str(yaml_path)

    # should not raise
    runner._mark_run_running_ml('job_running')

    loaded = yaml.safe_load(yaml_path.read_text(encoding='utf8'))
    assert 'job_running' in loaded
    lr = loaded['job_running']['last_run']
    assert lr['status'] is None
    assert lr['status_str'] == 'RUNNING'


def test_write_last_run_triggers_reload_settings(tmp_path, monkeypatch):
    yaml_path = _write_tmp_settings(tmp_path, name='job_write')
    os.environ['PCOPY_SETTINGS_PATH'] = str(yaml_path)

    called = {'flag': False}

    def fake_reload_settings():
        called['flag'] = True

    monkeypatch.setattr(config, 'reload_settings', fake_reload_settings)

    entry = {'timestamp': datetime.now().isoformat(), 'status': 0}
    runner._write_last_run_yaml_ml('job_write', entry)
    assert called['flag'] is True

    loaded = yaml.safe_load(yaml_path.read_text(encoding='utf8'))
    assert 'last_run' in loaded['job_write']


def test_persist_last_run_dupes_saved_detection_false(tmp_path, monkeypatch):
    yaml_path = _write_tmp_settings(tmp_path, name='job_no_dupes')
    os.environ['PCOPY_SETTINGS_PATH'] = str(yaml_path)
    # ensure BACKUP_VERSIONS_DIR does not exist
    monkeypatch.setattr(config, 'BACKUP_VERSIONS_DIR', Path(tmp_path / 'missing_versions'))

    dash = SimpleNamespace()
    dash.start_time = datetime.now()
    dash.transferred = 'Total transferred file size: 321 bytes'
    dash.errors = []
    dash.duplicates = 0

    runner._persist_last_run_entry_ml('job_no_dupes', 0, False, dash)
    loaded = yaml.safe_load(yaml_path.read_text(encoding='utf8'))
    assert loaded['job_no_dupes']['last_run']['dupes_saved'] is False


def test_persist_last_run_dupes_saved_detection_true(tmp_path, monkeypatch):
    yaml_path = _write_tmp_settings(tmp_path, name='job_dupes')
    os.environ['PCOPY_SETTINGS_PATH'] = str(yaml_path)
    versions = tmp_path / 'versions'
    versions.mkdir()
    monkeypatch.setattr(config, 'BACKUP_VERSIONS_DIR', versions)
    monkeypatch.setattr(runner, 'BACKUP_VERSIONS_DIR', versions)

    dash = SimpleNamespace()
    # set start_time sufficiently in the past so newly created file has mtime >= start_time
    dash.start_time = datetime.now() - timedelta(seconds=10)
    dash.transferred = 'Total transferred file size: 777 bytes'
    dash.errors = []
    dash.duplicates = 1

    # create a recent file in versions
    p = versions / 'recent.dat'
    p.write_text('x')
    os.utime(str(p), None)

    runner._persist_last_run_entry_ml('job_dupes', 0, False, dash)
    loaded = yaml.safe_load(yaml_path.read_text(encoding='utf8'))
    assert loaded['job_dupes']['last_run']['dupes_saved'] is True


def test_mark_run_handles_writer_error_logs(tmp_path, monkeypatch, caplog):
    yaml_path = _write_tmp_settings(tmp_path, name='job_err')
    os.environ['PCOPY_SETTINGS_PATH'] = str(yaml_path)

    def broken_write(name, entry):
        raise OSError('disk full')

    monkeypatch.setattr(runner, '_write_last_run_yaml_ml', broken_write)

    caplog.clear()
    caplog.set_level('ERROR')
    # Should not raise
    runner._mark_run_running_ml('job_err')
    assert any('Failed to mark running for job_err' in rec.getMessage() for rec in caplog.records)
