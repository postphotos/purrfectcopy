import importlib

import pcopy.runner as runner


def test_main_boring_alias(monkeypatch):
    called = {}

    def fake_run_backup(source=None, dest=None, dry_run=False, boring=False):
        called['args'] = dict(source=source, dest=dest, dry_run=dry_run, boring=boring)
        return 0

    monkeypatch.setattr(runner, 'run_backup', fake_run_backup)

    # simulate --boring
    rc = runner.main(['--boring'])
    assert rc == 0
    assert called['args']['boring'] is True

    # simulate --quiet
    rc = runner.main(['--quiet'])
    assert rc == 0
    assert called['args']['boring'] is True
