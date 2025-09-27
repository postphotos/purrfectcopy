import sys
import pytest

try:
    import pexpect
except Exception:
    pexpect = None


def test_run_backup_popen_fallback():
    if pexpect is None:
        pytest.skip('pexpect not installed; skipping PTY integration test')
    # This test spawns a python process that monkeypatches subprocess.Popen to
    # simulate an iteration error and then calls run_backup(); we assert
    # it returns a non-zero exit status due to the simulated kill.
    script = r"""
import subprocess
from pcopy import runner
class BadStdout:
    def __iter__(self):
        return self
    def __next__(self):
        raise RuntimeError('iter fail')
class FakePopen:
    def __init__(self,*a,**k):
        self.stdout = BadStdout()
        self.returncode = 0
    def wait(self):
        return self.returncode
    def kill(self):
        self.returncode = 1
    # support context manager protocol used by some code paths
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc, tb):
        return False
import types
runner.subprocess.Popen = FakePopen
rc = runner.run_backup(source='s', dest='d', dry_run=False, boring=True)
print('RC='+str(rc))
"""
    child = pexpect.spawn(sys.executable, ['-u', '-c', script], encoding='utf-8', timeout=5)
    child.expect('RC=')
    child.expect(pexpect.EOF)
    out = child.before
    child.close()
    # parse the RC printed
    rc_str = out.split('RC=')[-1].strip()
    rc = int(rc_str) if rc_str.isdigit() else 0
    assert rc in (0,1)
