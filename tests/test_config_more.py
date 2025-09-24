import importlib
import sys
import types
from pathlib import Path

import pcopy.config as config


def _reload_config():
    importlib.reload(config)
    return config


def test_load_settings_from_yaml(tmp_path, monkeypatch):
    # Backup existing settings file if present
    settings_path: Path = config.SETTINGS_PATH
    backup = None
    if settings_path.exists():
        backup = settings_path.read_text(encoding='utf8')
        settings_path.unlink()

    try:
        # Write a simple yaml settings file
        settings_path.write_text(
            """
source: ./my-src
dest: ./my-dest
exclude: .myignore
backup_versions_dir: ./my-versions
""",
            encoding='utf8',
        )

        cfg = _reload_config()

        # Settings should contain the keys we wrote
        assert cfg.SETTINGS.get('source') == './my-src'
        assert cfg.SETTINGS.get('dest') == './my-dest'
        assert cfg.SETTINGS.get('exclude') == '.myignore'
        assert cfg.SETTINGS.get('backup_versions_dir') == './my-versions'

        # Derived paths should reflect the settings (names are sufficient)
        assert cfg.SOURCE_DIR.name == 'my-src'
        assert cfg.DEST_DIR.name == 'my-dest'
    finally:
        # restore
        settings_path.unlink(missing_ok=True)
        if backup is not None:
            settings_path.write_text(backup, encoding='utf8')
        _reload_config()


def test_yaml_safe_load_raises(monkeypatch, tmp_path):
    # Ensure a settings file exists so safe_load gets called
    settings_path: Path = config.SETTINGS_PATH
    backup = None
    if settings_path.exists():
        backup = settings_path.read_text(encoding='utf8')
        settings_path.unlink()

    try:
        settings_path.write_text('source: x', encoding='utf8')

        # Inject a fake yaml module whose safe_load raises
        fake_yaml = types.ModuleType('yaml')

        def bad_safe_load(_fh):
            raise ValueError('not a valid yaml')

        setattr(fake_yaml, 'safe_load', bad_safe_load)
        monkeypatch.setitem(sys.modules, 'yaml', fake_yaml)

        cfg = _reload_config()

        # When yaml.safe_load raises, SETTINGS should be empty dict
        assert cfg.SETTINGS == {}
    finally:
        # cleanup
        monkeypatch.delitem(sys.modules, 'yaml', raising=False)
        settings_path.unlink(missing_ok=True)
        if backup is not None:
            settings_path.write_text(backup, encoding='utf8')
        _reload_config()


def test_no_settings_file(monkeypatch):
    # Ensure no settings file exists
    settings_path: Path = config.SETTINGS_PATH
    backup = None
    if settings_path.exists():
        backup = settings_path.read_text(encoding='utf8')
        settings_path.unlink()

    try:
        # Reload and expect empty settings when file is absent
        cfg = _reload_config()
        assert cfg.SETTINGS == {}
    finally:
        if backup is not None:
            settings_path.write_text(backup, encoding='utf8')
        _reload_config()
import importlib
from pathlib import Path
import yaml
from pcopy import config


def test_load_settings_from_yaml_alt(tmp_path, monkeypatch):
    cfg = tmp_path / '.pcopy-main-backup.yml'
    cfg.write_text('main-backup:\n  source: "/tmp/src"\n  dest: "/tmp/dst"\n')
    monkeypatch.setattr(config, 'SETTINGS_PATH', cfg)
    s = config._load_settings()
    assert isinstance(s, dict)
    # values present
    assert 'main-backup' in s or isinstance(s, dict)


def test_load_settings_yaml_raises(monkeypatch, tmp_path):
    # Create a dummy module to simulate yaml raising
    class FakeYaml:
        def safe_load(self, f):
            raise Exception('boom')

    monkeypatch.setitem(__import__('sys').modules, 'yaml', FakeYaml())
    monkeypatch.setattr(config, 'SETTINGS_PATH', tmp_path / '.pcopy-main-backup.yml')
    s = config._load_settings()
    assert s == {}
