import json
import tempfile
from pathlib import Path

from pcopy import config


def test_env_slogans_override(monkeypatch, tmp_path):
    # Create a temporary slogans.json
    data = {'slogans': ['Env Slogan'], 'cat_facts': ['env fact']}
    p = tmp_path / 'env-slogans.json'
    p.write_text(json.dumps(data), encoding='utf8')

    # Set PCOPY_SLOGANS to point to our temp file
    monkeypatch.setenv('PCOPY_SLOGANS', str(p))

    # reload module-level variables by calling _load_slogans indirectly
    # by reassigning SLOGANS_PATH and calling reload_settings
    # In practice config module reads PCOPY_SLOGANS at import, so simulate by
    # forcing SLOGANS_PATH check: set SLOGANS_PATH to p if exists.
    monkeypatch.setattr(config, 'SLOGANS_PATH', Path(str(p)))
    config.reload_settings()

    assert 'Env Slogan' in config.SLOGANS
    assert 'env fact' in config.CAT_FACTS
    assert config.SLOGANS_DATA.get('slogans') is not None
