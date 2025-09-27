import pytest
from pcopy import runner
import pcopy.config as config


def _make_prompt_responder(answers):
    it = iter(answers)
    def ask(prompt, default=None):
        try:
            return next(it)
        except StopIteration:
            return default or ''
    return ask


def test_rsync_command_screen_run(monkeypatch, capsys):
    monkeypatch.setattr(config, 'SETTINGS', {'job1': {'source': '/src', 'dest': '/dst'}})
    # simulate selecting 1, then press Enter to continue
    monkeypatch.setattr('rich.prompt.Prompt.ask', _make_prompt_responder(['1', '']))
    called = {}
    def fake_run_backup(source=None, dest=None, dry_run=False, boring=False, **k):
        called['cmd'] = (source, dest, dry_run)
        return 0
    monkeypatch.setattr(runner, 'run_backup', fake_run_backup)
    rc = runner._show_menu()
    out = capsys.readouterr().out
    assert rc == 0
    assert 'rsync -a --info=progress2' in out
    assert '--dry-run' in out  # dry-run command shown
    assert called['cmd'][0] == '/src'
    assert called['cmd'][1] == '/dst'


def test_rsync_command_screen_dryrun(monkeypatch, capsys):
    monkeypatch.setattr(config, 'SETTINGS', {'job1': {'source': '/s2', 'dest': '/d2'}})
    # simulate selecting dry-run form 'd1', then press Enter
    monkeypatch.setattr('rich.prompt.Prompt.ask', _make_prompt_responder(['d1', '']))
    called = {}
    def fake_run_backup(source=None, dest=None, dry_run=False, boring=False, **k):
        called['cmd'] = (source, dest, dry_run)
        return 0
    monkeypatch.setattr(runner, 'run_backup', fake_run_backup)
    rc = runner._show_menu()
    out = capsys.readouterr().out
    assert rc == 0
    # dry-run command should be shown and include --dry-run
    assert 'rsync -a --info=progress2' in out
    assert '--dry-run' in out
    assert called['cmd'][2] is True


def test_rsync_command_screen_run_all(monkeypatch, capsys):
    monkeypatch.setattr(config, 'SETTINGS', {
        'job1': {'source': '/src1', 'dest': '/dst1'},
        'job2': {'source': '/src2', 'dest': '/dst2'},
    })
    # simulate selecting 'R' then pressing Enter to continue
    monkeypatch.setattr('rich.prompt.Prompt.ask', _make_prompt_responder(['R', '']))
    called = {'runs': []}
    def fake_run_backup(source=None, dest=None, dry_run=False, boring=False, **k):
        called['runs'].append((source, dest, dry_run))
        return 0
    monkeypatch.setattr(runner, 'run_backup', fake_run_backup)
    rc = runner._show_menu()
    out = capsys.readouterr().out
    assert rc == 0
    # Ensure commands for both jobs printed
    assert 'rsync -a --info=progress2 /src1 /dst1' in out
    assert 'rsync -a --info=progress2 /src2 /dst2' in out
    assert len(called['runs']) == 2


def test_rsync_command_screen_dryrun_all(monkeypatch, capsys):
    monkeypatch.setattr(config, 'SETTINGS', {
        'j1': {'source': '/a', 'dest': '/b'},
        'j2': {'source': '/c', 'dest': '/d'},
    })
    # simulate selecting 'D' then pressing Enter to continue
    monkeypatch.setattr('rich.prompt.Prompt.ask', _make_prompt_responder(['D', '']))
    called = {'runs': []}
    def fake_run_backup(source=None, dest=None, dry_run=False, boring=False, **k):
        called['runs'].append((source, dest, dry_run))
        return 0
    monkeypatch.setattr(runner, 'run_backup', fake_run_backup)
    rc = runner._show_menu()
    out = capsys.readouterr().out
    assert rc == 0
    assert '--dry-run' in out
    assert len(called['runs']) == 2
