import time
import shutil
import subprocess
from pcopy import cowsay_helper


def test_cowsay_cache_behavior(monkeypatch):
    # ensure cache is used when repeated
    cowsay_helper._CACHE.clear()
    # monkeypatch system cowsay to be unavailable
    monkeypatch.setattr(shutil, 'which', lambda name: None)
    a1 = cowsay_helper.cowsay_art('text', cow='x')
    # cached
    a2 = cowsay_helper.cowsay_art('text', cow='x')
    assert a1 == a2


def test_cowsay_system_invocation(monkeypatch):
    # simulate system cowsay available and subprocess returning output
    monkeypatch.setattr(shutil, 'which', lambda name: '/usr/bin/cowsay')

    def fake_check_output(cmd, stderr=None, text=False):
        return 'SYSTEM ART'

    monkeypatch.setattr(subprocess, 'check_output', fake_check_output)
    art = cowsay_helper.cowsay_art('yo', cow='datakitten')
    assert 'SYSTEM ART' in art
