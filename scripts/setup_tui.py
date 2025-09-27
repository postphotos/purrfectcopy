#!/usr/bin/env python3
"""Prompt-toolkit based TUI for pcopy setup.

Provides friendly prompts with path completion and validation.
"""
from prompt_toolkit import prompt
from prompt_toolkit.completion import PathCompleter
from prompt_toolkit.shortcuts import confirm
from pathlib import Path
import os

print("🐾 Welcome to the Purrfect Backup setup (TUI)")
print("We'll ask a couple of quick questions to configure your main backup.")

completer = PathCompleter(expanduser=True)

src = prompt('Source path: ', completer=completer)
if not src:
    src = '/data'

dst = prompt('Destination path: ', completer=completer)
if not dst:
    dst = '/backup'

print(f"Using source: {src}")
print(f"Using dest:   {dst}")
if not Path(dst).exists():
    if confirm(f"Destination {dst} does not exist — create it?"):
        Path(dst).mkdir(parents=True, exist_ok=True)
        print(f"Created {dst}")

# Write the settings
home = Path.home()
settings = home / '.pcopy-main-backup.yml'
if settings.exists():
    bak = settings.with_suffix(f'.bak')
    settings.rename(bak)
    print(f"Backed up existing settings to {bak}")

content = f"""main-backup:\n    source: \"{src}\"\n    dest: \"{dst}\"\nrsync_options: []\n"""
settings.write_text(content)
print(f"Wrote settings to {settings}")

# Optionally add completion snippet (same as setup.sh)
print("TUI setup complete — run 'pcopy do main-backup --dry-run' to verify the configuration.")
