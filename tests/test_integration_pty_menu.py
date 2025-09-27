import sys
import pytest

try:
    import pexpect
except Exception:
    pexpect = None


def test_show_menu_quit():
    if pexpect is None:
        pytest.skip('pexpect not installed; skipping PTY integration test')
    script = r"""
from pcopy import runner
# Replace run_backup with a harmless stub so menu exits cleanly on choices
runner.run_backup = lambda *a, **k: 0
runner._show_menu()
"""
    child = pexpect.spawn(sys.executable, ['-u', '-c', script], encoding='utf-8', timeout=5)
    # expect the menu header then send 'q' to quit
    child.expect('Purrfect Backup')
    child.sendline('q')
    child.expect(pexpect.EOF)
    child.close()
    assert child.exitstatus == 0
