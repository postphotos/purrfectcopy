import importlib
import json
import os
import sys


def test_import_time_inprocess(tmp_path, monkeypatch):
    data = {'slogans': ['InProcSlogan'], 'cat_facts': ['inproc fact']}
    p = tmp_path / 'inproc-slogans.json'
    p.write_text(json.dumps(data), encoding='utf8')

    monkeypatch.setenv('PCOPY_SLOGANS', str(p))

    # Backup any existing module and remove cached submodule so a fresh import executes top-level code
    orig = sys.modules.get('pcopy.config')
    try:
        if 'pcopy.config' in sys.modules:
            del sys.modules['pcopy.config']

        c = importlib.import_module('pcopy.config')
        assert 'InProcSlogan' in c.SLOGANS
        assert 'inproc fact' in c.CAT_FACTS
    finally:
        # restore original module to avoid breaking other tests
        if orig is not None:
            sys.modules['pcopy.config'] = orig
