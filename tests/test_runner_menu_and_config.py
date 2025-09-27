import json
from types import SimpleNamespace
import yaml

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


def test_show_menu_quit(monkeypatch):
    monkeypatch.setattr('rich.prompt.Prompt.ask', _make_prompt_responder(['q']))
    rc = runner._show_menu()
    assert rc == 0


def test_show_menu_named_run(monkeypatch):
    # Add a named backup config and ensure selecting '1' calls run_backup
    monkeypatch.setattr(config, 'SETTINGS', {'job1': {'source': 's', 'dest': 'd'}})
    called = {}

    def fake_run_backup(source=None, dest=None, dry_run=False, boring=False):
        called['args'] = dict(source=source, dest=dest, dry_run=dry_run, boring=boring)
        return 0

    monkeypatch.setattr(runner, 'run_backup', fake_run_backup)
    monkeypatch.setattr('rich.prompt.Prompt.ask', _make_prompt_responder(['1']))
    rc = runner._show_menu()
    assert rc == 0
    assert called['args']['source'] == 's'


def test_show_menu_dryrun_named(monkeypatch):
    monkeypatch.setattr(config, 'SETTINGS', {'job1': {'source': 'sx', 'dest': 'dx'}})
    called = {}

    def fake_run_backup(source=None, dest=None, dry_run=False, boring=False):
        called['args'] = dict(source=source, dest=dest, dry_run=dry_run, boring=boring)
        return 0

    monkeypatch.setattr(runner, 'run_backup', fake_run_backup)
    monkeypatch.setattr('rich.prompt.Prompt.ask', _make_prompt_responder(['d1']))
    rc = runner._show_menu()
    assert rc == 0
    assert called['args']['dry_run'] is True


def test_show_menu_custom(monkeypatch):
    called = {}

    def fake_run_backup(source=None, dest=None, dry_run=False, boring=False):
        called['args'] = dict(source=source, dest=dest, dry_run=dry_run, boring=boring)
        return 0

    monkeypatch.setattr(runner, 'run_backup', fake_run_backup)
    # First choice 'c', then source, then dest
    monkeypatch.setattr('rich.prompt.Prompt.ask', _make_prompt_responder(['c', 'sourceX', 'destY']))
    rc = runner._show_menu()
    assert rc == 0
    assert called['args']['source'] == 'sourceX'


def test_load_slogans_from_user_yaml(tmp_path, monkeypatch):
    # create YAML settings file containing slogans and cat_facts
    yaml_path = tmp_path / 'user.yml'
    yaml_content = {'slogans': ['u1'], 'cat_facts': ['cf1']}
    yaml_path.write_text(yaml.safe_dump(yaml_content), encoding='utf8')

    monkeypatch.setattr(config, 'SETTINGS_PATH', yaml_path)
    # ensure package slogans path does not interfere
    monkeypatch.setattr(config, 'SLOGANS_PATH', tmp_path / 'noexist.json')
    config.reload_settings()
    assert 'u1' in config.SLOGANS
    assert 'cf1' in config.CAT_FACTS
