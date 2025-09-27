import os
import tempfile
import yaml

from pcopy import config


def test_reload_settings_reads_yaml(monkeypatch, tmp_path):
    # create a temporary settings YAML with slogans and cat_facts
    data = {'slogans': ['YAML Slogan 1', 'YAML Slogan 2'], 'cat_facts': ['YAML fact']}
    p = tmp_path / 'settings.yml'
    p.write_text(yaml.safe_dump(data), encoding='utf8')

    # point SETTINGS_PATH at our temp file
    monkeypatch.setattr(config, 'SETTINGS_PATH', p)
    # ensure reload_settings uses the new file
    config.reload_settings()

    assert 'YAML Slogan 1' in config.SLOGANS
    assert 'YAML fact' in config.CAT_FACTS
    assert isinstance(config.SLOGANS_DATA, dict)
    assert config.SLOGANS_DATA.get('quotes') is not None
