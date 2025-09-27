import json
import subprocess
import sys
from pathlib import Path


def test_import_time_pcopy_slogans_env(tmp_path):
    data = {'slogans': ['ImportEnvSlogan'], 'cat_facts': ['import fact']}
    p = tmp_path / 'import-slogans.json'
    p.write_text(json.dumps(data), encoding='utf8')

    # Spawn a fresh Python process that sets the env var and imports pcopy.config
    code = f"""
import os
os.environ['PCOPY_SLOGANS'] = r'{str(p)}'
# import the module fresh
import importlib
c = importlib.import_module('pcopy.config')
print('SLOGANS_CONTAINS_IMPORT_MARKER' if 'ImportEnvSlogan' in c.SLOGANS else 'NO')
"""
    res = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    assert 'SLOGANS_CONTAINS_IMPORT_MARKER' in res.stdout
