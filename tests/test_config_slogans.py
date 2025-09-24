import importlib
import pathlib

import pcopy.config as config


def test_slogans_fallback(monkeypatch):
    # Force Path.open to raise to trigger the slogans fallback
    def bad_open(self, *args, **kwargs):
        raise Exception('open failed')

    monkeypatch.setattr(pathlib.Path, 'open', bad_open)
    try:
        cfg = importlib.reload(config)
        assert cfg.SLOGANS == ['Backup running...']
        assert cfg.CAT_FACTS == ['Cats sleep a lot.']
    finally:
        importlib.reload(config)
