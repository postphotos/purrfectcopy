import yaml
from datetime import datetime, timedelta
from pathlib import Path
import os

import pytest

from pcopy import runner


class DummyDash:
    def __init__(self):
        self.start_time = datetime.now() - timedelta(seconds=2)
        self.transferred = 'Total transferred file size: 999 bytes'
        self.errors = ['err1', 'err2']
        self.duplicates = 3


def test_parse_and_format_helpers():
    assert runner._parse_transferred_bytes_ml('Total transferred file size: 123 bytes') == 123
    assert runner._parse_transferred_bytes_ml('1.5 MB') == int(1.5 * 1024 * 1024)
    assert runner._format_bytes_ml(512) == '512 bytes'
    assert 'KB' in runner._format_bytes_ml(2048)
    assert runner._format_duration_ml(5) == '5s'
    assert runner._format_duration_ml(75) == '1m 15s'


def test_write_and_persist_last_run(tmp_path, monkeypatch):
    sfile = tmp_path / 'settings.yml'
    # create base settings
    base = {'jobX': {'source': '/s', 'dest': '/d'}}
    sfile.write_text(yaml.safe_dump(base), encoding='utf8')

    monkeypatch.setenv('PCOPY_SETTINGS_PATH', str(sfile))

    # create a backup versions dir and add a file newer than dash start_time
    bv = tmp_path / 'bv'
    bv.mkdir()
    f = bv / 'vfile'
    f.write_text('x')
    # ensure mtime is now
    os.utime(str(f), None)

    # patch runner.BACKUP_VERSIONS_DIR to point to bv
    monkeypatch.setattr(runner, 'BACKUP_VERSIONS_DIR', bv)

    dash = DummyDash()
    runner._persist_last_run_entry_ml('jobX', 0, False, dash)

    data = yaml.safe_load(sfile.read_text(encoding='utf8'))
    assert 'jobX' in data
    lr = data['jobX'].get('last_run')
    assert lr is not None
    assert lr['status_str'] == 'PASS'
    assert lr['transferred_bytes'] == 999
    assert lr['errors_count'] == 2
    assert lr['dupes_saved'] is True


def test_write_last_run_handles_yaml_error(tmp_path, monkeypatch):
    sfile = tmp_path / 'settings.yml'
    sfile.write_text('{}', encoding='utf8')
    monkeypatch.setenv('PCOPY_SETTINGS_PATH', str(sfile))

    # force yaml.safe_dump to raise
    def bad_dump(*a, **k):
        raise RuntimeError('yaml fail')

    monkeypatch.setattr('yaml.safe_dump', bad_dump)
    # Should not raise
    runner._write_last_run_yaml_ml('nope', {'a': 1})
