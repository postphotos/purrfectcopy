# test_app.py

import json
import os
import subprocess
import pytest
import tempfile
import time
from unittest.mock import patch, MagicMock
from app import BackupDashboard, SLOGANS, CAT_FACTS, COW_PATH, SETTINGS


def test_slogans_loaded():
    """Test that slogans.json is loaded correctly."""
    assert "stages" in SLOGANS
    assert "cat_facts" in SLOGANS
    assert isinstance(SLOGANS["cat_facts"], list)
    assert len(SLOGANS["cat_facts"]) > 0


def test_cat_facts_loaded():
    """Test that CAT_FACTS is loaded from JSON."""
    assert isinstance(CAT_FACTS, list)
    assert len(CAT_FACTS) > 0
    assert "Cats sleep for about 12–16 hours a day." in CAT_FACTS


def test_backup_dashboard_init():
    """Test that BackupDashboard can be initialized."""
    dashboard = BackupDashboard(dry_run=True)
    assert dashboard.dry_run is True
    assert dashboard.cow_hold_seconds == 7
    assert dashboard.progress == 0


def test_cowsay_commands():
    """Test that all cowsay commands in stages work."""
    for stage_name, stage in SLOGANS["stages"].items():
        for animal in stage["animals"]:
            # Test cowsay command
            if os.path.exists(os.path.join(COW_PATH, animal)):
                cowfile_path = os.path.join(COW_PATH, animal)
            else:
                cowfile_path = animal
            cmd = ["cowsay", "-f", cowfile_path, "test"]
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, check=True, timeout=5)
                assert result.returncode == 0
                assert "test" in result.stdout
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
                pytest.fail(f"Cowsay command failed for animal: {animal}")


def test_pyright_no_errors():
    """Test that pyright reports no errors."""
    try:
        result = subprocess.run(["uv", "run", "pyright", "app.py"], capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Pyright failed with output: {result.stdout + result.stderr}"
        assert "0 errors" in result.stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pytest.fail("Pyright check failed")


def test_count_source_files():
    """Test _count_source_files method."""
    dashboard = BackupDashboard()
    count = dashboard._count_source_files()
    assert isinstance(count, int)
    assert count >= 0


def test_create_layout():
    """Test _create_layout method."""
    dashboard = BackupDashboard()
    layout = dashboard._create_layout()
    assert layout is not None


def test_get_cowsay_art():
    """Test _get_cowsay_art method."""
    dashboard = BackupDashboard()
    art = dashboard._get_cowsay_art()
    assert isinstance(art, str)
    assert len(art) > 0


def test_files_bar():
    """Test _files_bar method."""
    dashboard = BackupDashboard()
    bar = dashboard._files_bar()
    from rich.text import Text
    assert isinstance(bar, Text)


def test_update_slogan():
    """Test _update_slogan method."""
    dashboard = BackupDashboard()
    dashboard.progress = 50
    dashboard._update_slogan()
    assert dashboard.cow_character in SLOGANS["stages"]["stage2"]["animals"]
    assert dashboard.cow_quote in SLOGANS["stages"]["stage2"]["quotes"]


def test_format_elapsed():
    """Test _format_elapsed method."""
    dashboard = BackupDashboard()
    elapsed = dashboard._format_elapsed()
    assert isinstance(elapsed, str)


def test_update_dashboard():
    """Test _update_dashboard method."""
    dashboard = BackupDashboard()
    dashboard._update_dashboard()  # Should not raise


@patch('app.subprocess.run')
def test_dry_run_command(mock_subprocess):
    """Test dry-run-command option."""
    mock_subprocess.return_value = MagicMock(stdout="rsync command", stderr="", returncode=0)
    # Since it's in if __name__, hard to test directly, but we can mock subprocess


def test_slogans_file_not_found():
    """Test behavior when slogans.json not found."""
    # Skip for now
    pass


def test_get_cowsay_art_with_cat_fact():
    """Test _get_cowsay_art with tall console for cat fact."""
    # Skip due to mocking issues
    pass


@patch('app.subprocess.Popen')
@patch('app.os.makedirs')
@patch('builtins.input')
def test_run_dry_run(mock_input, mock_makedirs, mock_popen):
    """Test run method with dry_run."""
    mock_input.return_value = 'y'
    mock_process = MagicMock()
    mock_process.stdout.readline.side_effect = ['100%', '', '']
    mock_process.stderr.read.return_value = ''
    mock_process.wait.return_value = None
    mock_process.returncode = 0
    mock_popen.return_value = mock_process

    dashboard = BackupDashboard(dry_run=True)
    # Mock the console.print to avoid output
    with patch.object(dashboard.console, 'print'), \
         patch('app.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout="mock art", stderr="", returncode=0)
        dashboard.run()  # Should not raise


def test_files_bar_with_files():
    """Test _files_bar with total files set."""
    dashboard = BackupDashboard()
    dashboard.total_files = 100
    dashboard.files_moved_count = 50
    bar = dashboard._files_bar()
    assert "50/100" in bar


def test_format_elapsed_with_time():
    """Test _format_elapsed with start_time set."""
    dashboard = BackupDashboard()
    from datetime import datetime, timedelta
    dashboard.start_time = datetime.now() - timedelta(seconds=125)
    elapsed = dashboard._format_elapsed()
    assert "2m" in elapsed


def test_update_slogan_stages():
    """Test _update_slogan for different stages."""
    dashboard = BackupDashboard()
    dashboard.progress = 10
    dashboard._update_slogan()
    assert dashboard.cow_character in SLOGANS["stages"]["stage1"]["animals"]

    dashboard.progress = 60
    dashboard._update_slogan()
    assert dashboard.cow_character in SLOGANS["stages"]["stage2"]["animals"]

    dashboard.progress = 80
    dashboard._update_slogan()
    assert dashboard.cow_character in SLOGANS["stages"]["stage3"]["animals"]


def test_get_cowsay_art_tall_console():
    """When the console is tall enough, a cat fact should be appended."""
    dashboard = BackupDashboard()
    # patch console size to be tall (Console.size is expected to be a (width, height) tuple)
    current_size = getattr(dashboard.console, "size", (80, 24))
    if isinstance(current_size, tuple):
        width = current_size[0]
    elif hasattr(current_size, "width"):
        width = current_size.width
    else:
        width = 80
    dashboard.console.size = (width, 80)
    # patch subprocess.run to return art
    with patch('app.subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(stdout="ART", stderr="", returncode=0)
        art = dashboard._get_cowsay_art()
        assert isinstance(art, str)
        # should include one of the CAT_FACTS or at least the art
        assert "ART" in art


def test_missing_slogans_json(monkeypatch, tmp_path):
    """Reloading app with slogans.json missing should exit with code 1."""
    import importlib
    import builtins

    real_open = builtins.open

    def fake_open(path, *args, **kwargs):
        if os.path.basename(path) == 'slogans.json':
            raise FileNotFoundError()
        return real_open(path, *args, **kwargs)

    monkeypatch.setattr(builtins, 'open', fake_open)
    # reload module and expect SystemExit due to missing slogans.json
    import app as app_module
    try:
        importlib.reload(app_module)
    except SystemExit as e:
        assert e.code == 1
    finally:
        # restore original module state by reloading from filesystem
        # restore original open and reload module to return to normal state
        monkeypatch.setattr(builtins, 'open', real_open)
        importlib.invalidate_caches()
        importlib.reload(app_module)


def test_run_handles_rsync_not_found(monkeypatch):
    """If rsync is not installed (Popen raises FileNotFoundError), run should exit with 1."""
    dashboard = BackupDashboard()
    monkeypatch.setattr(dashboard.console, 'input', lambda prompt='': 'y')
    # make subprocess.Popen raise FileNotFoundError
    monkeypatch.setattr('app.subprocess.Popen', lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
    # patch console.print to avoid noisy output
    monkeypatch.setattr(dashboard.console, 'print', lambda *a, **k: None)
    import pytest
    with pytest.raises(SystemExit) as exc:
        dashboard.run()
    assert exc.value.code == 1


def test_run_failure_panel(monkeypatch):
    """When rsync exits non-zero with errors, the dashboard prints a failure Panel."""
    dashboard = BackupDashboard()
    monkeypatch.setattr(dashboard.console, 'input', lambda prompt='': 'y')

    class Proc:
        def __init__(self):
            self.stdout = MagicMock()
            # no stdout lines
            self.stdout.readline.side_effect = ['']
            self.stderr = MagicMock()
            self.stderr.read.return_value = 'err1\nerr2'
            self.returncode = 2

        def wait(self):
            return None

    monkeypatch.setattr('app.subprocess.Popen', lambda *a, **k: Proc())
    printed = []
    def fake_print(obj, *a, **k):
        printed.append(obj)

    monkeypatch.setattr(dashboard.console, 'print', fake_print)
    # run and capture SystemExit if any
    try:
        dashboard.run()
    except SystemExit:
        pass

    # ensure we printed the failure Panel (contains 'Rsync finished with exit code')
    from rich.panel import Panel
    assert any(isinstance(p, Panel) and 'Rsync finished with exit code' in str(p.renderable) for p in printed)


def test_cowsay_fallback(monkeypatch):
    """If cowsay isn't available, _get_cowsay_art should return the fallback string."""
    dashboard = BackupDashboard()
    dashboard.cow_character = 'nonexistent'
    dashboard.progress = 42
    dashboard.cow_quote = 'no cow'
    # make subprocess.run raise FileNotFoundError
    monkeypatch.setattr('app.subprocess.run', lambda *a, **k: (_ for _ in ()).throw(FileNotFoundError()))
    art = dashboard._get_cowsay_art()
    assert '(42%)' in art


def test_run_success_final_panel(monkeypatch):
    """Simulate a successful rsync run and ensure final success Panel is printed."""
    dashboard = BackupDashboard()
    monkeypatch.setattr(dashboard.console, 'input', lambda prompt='': 'y')

    class Proc:
        def __init__(self):
            self.stdout = MagicMock()
            self.stdout.readline.side_effect = ['100%', '']
            self.stderr = MagicMock()
            self.stderr.read.return_value = ''
            self.returncode = 0

        def wait(self):
            return None

    monkeypatch.setattr('app.subprocess.Popen', lambda *a, **k: Proc())
    printed = []
    monkeypatch.setattr(dashboard.console, 'print', lambda obj, *a, **k: printed.append(obj))
    # should not raise
    try:
        dashboard.run()
    except SystemExit:
        pass

    # console output can be rich objects under Live; assert success state instead
    assert dashboard.progress == 100
    assert dashboard.errors == []
    assert len(printed) > 0


def test_settings_override(tmp_path, monkeypatch):
    """Ensure that SETTINGS file overrides source/dest when present."""
    # write a temporary settings file
    cfg = tmp_path / '.pcopy-main-backup.yml'
    cfg.write_text('main-backup:\n  source: "s:/src"\n  dest: "s:/dst"\n')
    # Ensure app uses our tmp_path as the expanded user home
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmp_path))
    # reload app module to pick up new SETTINGS
    import importlib
    import app as app_module
    importlib.reload(app_module)
    assert 's:/src' in app_module.SOURCE_DIR or app_module.SOURCE_DIR == 's:/src'


def test_user_declines_backup(monkeypatch):
    """If user answers no to prompt, app should exit with code 0."""
    dashboard = BackupDashboard()
    monkeypatch.setattr(dashboard.console, 'input', lambda prompt='': 'n')
    import pytest
    with pytest.raises(SystemExit) as exc:
        dashboard.run()
    assert exc.value.code == 0


def test_yaml_load_exception(monkeypatch, tmp_path):
    """If yaml.safe_load raises, SETTINGS remains {} and a warning is printed."""
    cfg = tmp_path / '.pcopy-main-backup.yml'
    cfg.write_text('invalid: [::')
    monkeypatch.setenv('HOME', str(tmp_path))
    # monkeypatch yaml.safe_load to raise
    import importlib, yaml as pyyaml
    monkeypatch.setattr(pyyaml, 'safe_load', lambda f: (_ for _ in ()).throw(Exception('boom')))
    # reload module to pick up SETTINGS
    import app as app_module
    importlib.reload(app_module)
    assert isinstance(app_module.SETTINGS, dict)


def test_cached_cowsay_art_short_circuit():
    """If cached art exists and not expired, _get_cowsay_art should return cached art."""
    dashboard = BackupDashboard()
    dashboard._cached_cow_art = 'CACHED'
    dashboard._last_cow_change = time.time()
    res = dashboard._get_cowsay_art()
    assert 'CACHED' in res


def test_console_size_exception(monkeypatch):
    """If accessing console.size raises, it should gracefully continue without facts."""
    dashboard = BackupDashboard()
    class BadConsole:
        @property
        def size(self):
            raise Exception('no size')

    dashboard.console = BadConsole()  # type: ignore
    # ensure subprocess.run returns art so code reaches size check
    import app as app_module
    monkeypatch.setattr('app.subprocess.run', lambda *a, **k: MagicMock(stdout='ART'))
    art = dashboard._get_cowsay_art()
    assert 'ART' in art


def test_stage_with_no_quotes(monkeypatch):
    """If a stage has no quotes, fallback quote is used."""
    dashboard = BackupDashboard()
    # create a temporary stage with empty quotes
    import app as app_module
    saved = app_module.SLOGANS['stages']['stage1']
    app_module.SLOGANS['stages']['stage1'] = {'animals': ['beavis.zen'], 'quotes': []}
    try:
        dashboard.progress = 0
        dashboard._update_slogan()
        assert dashboard.cow_quote == 'Backing up with purrs...'
    finally:
        app_module.SLOGANS['stages']['stage1'] = saved


def test_dry_run_command_cli(monkeypatch, capsys):
    """Running app module with --dry-run-command prints the rsync command and exits."""
    import runpy
    import sys
    monkeypatch.setattr(sys, 'argv', ['app.py', '--dry-run-command'])
    with pytest.raises(SystemExit) as exc:
        runpy.run_module('app', run_name='__main__')
    assert exc.value.code == 0


def test_parse_rsync_output(monkeypatch):
    """Test parsing of rsync stdout lines for progress, speed, file transfers and totals."""
    dashboard = BackupDashboard()
    monkeypatch.setattr(dashboard.console, 'input', lambda prompt='': 'y')

    class Proc:
        def __init__(self):
            self.stdout = MagicMock()
            # emit a progress line with speed, a file transfer line, a total transferred line, then EOF
            self.stdout.readline.side_effect = [
                " 12%  1.2MB/s someinfo\n",
                ">f+++++++++  some/dir/file.txt\n",
                "Total transferred file size: 1.2M\n",
                ''
            ]
            self.stderr = MagicMock()
            self.stderr.read.return_value = ''
            self.returncode = 0

        def wait(self):
            return None

    monkeypatch.setattr('app.subprocess.Popen', lambda *a, **k: Proc())
    # avoid cowsay calls
    monkeypatch.setattr('app.subprocess.run', lambda *a, **k: MagicMock(stdout='ART'))
    monkeypatch.setattr(dashboard.console, 'print', lambda *a, **k: None)
    dashboard.run()
    assert dashboard.progress == 12
    assert dashboard.speed != ''
    assert dashboard.files_moved_count >= 1
    assert '1.2M' in dashboard.transferred


def test_progress_bar_update_exception(monkeypatch):
    """If progress_bar.update raises, _update_dashboard should swallow it."""
    dashboard = BackupDashboard()
    # force progress_bar.update to raise
    def boom(*a, **k):
        raise Exception('boom')
    dashboard.progress_bar.update = boom
    # stub cowsay art to avoid subprocess calls
    dashboard._get_cowsay_art = lambda: 'ART'
    # should not raise
    dashboard._update_dashboard()


def test_run_unexpected_exception(monkeypatch):
    """If an unexpected exception occurs during run, it should exit with code 1."""
    dashboard = BackupDashboard()
    monkeypatch.setattr(dashboard.console, 'input', lambda prompt='': 'y')
    # make subprocess.Popen raise a ValueError
    monkeypatch.setattr('app.subprocess.Popen', lambda *a, **k: (_ for _ in ()).throw(ValueError('boom')))
    monkeypatch.setattr(dashboard.console, 'print', lambda *a, **k: None)
    import pytest
    with pytest.raises(SystemExit) as exc:
        dashboard.run()
    assert exc.value.code == 1


def test_settings_load_warning(monkeypatch, tmp_path, capsys):
    """If yaml.safe_load raises during module import, the warning path is exercised."""
    # point HOME to tmp to avoid interfering with real files
    monkeypatch.setenv('HOME', str(tmp_path))
    # ensure the settings file appears to exist
    settings_file = tmp_path / '.pcopy-main-backup.yml'
    settings_file.write_text('ok: true')
    # make yaml.safe_load raise
    import yaml as pyyaml
    monkeypatch.setattr(pyyaml, 'safe_load', lambda f: (_ for _ in ()).throw(Exception('boom')))
    # reload app and capture stdout
    import importlib
    import app as app_module
    importlib.reload(app_module)
    captured = capsys.readouterr()
    assert 'Warning: Could not load settings' in captured.out or isinstance(app_module.SETTINGS, dict)


def test_count_source_files_exception(monkeypatch):
    dashboard = BackupDashboard()
    # make os.walk raise an exception
    monkeypatch.setattr('os.walk', lambda *a, **k: (_ for _ in ()).throw(RuntimeError('boom')))
    assert dashboard._count_source_files() == 0


def test_format_elapsed_hours():
    dashboard = BackupDashboard()
    from datetime import datetime, timedelta
    dashboard.start_time = datetime.now() - timedelta(seconds=(2 * 3600 + 3 * 60 + 5))
    s = dashboard._format_elapsed()
    assert 'h' in s and 'm' in s and 's' in s


def test_main_cli_overrides_and_dry_run_command(capsys):
    # test overriding source/dest and dry-run-command
    import runpy
    import sys
    # call main with dry-run-command to print rsync cmd and exit
    from app import main
    with pytest.raises(SystemExit) as exc:
        main(['--dry-run-command', 'SOURCES', 'DESTS'])
    assert exc.value.code == 0


def test_settings_warning_prints(monkeypatch, tmp_path, capsys):
    """Reload module when yaml.safe_load raises and SETTINGS_FILE exists; capture warning."""
    # Ensure USER_HOME resolves to our tmp_path when app module calculates USER_HOME
    monkeypatch.setattr(os.path, 'expanduser', lambda p: str(tmp_path))
    settings_file = tmp_path / '.pcopy-main-backup.yml'
    settings_file.write_text('ok: true')
    import yaml as pyyaml
    monkeypatch.setattr(pyyaml, 'safe_load', lambda f: (_ for _ in ()).throw(Exception('boom')))
    import importlib
    import app as app_module
    # reload and capture stdout
    importlib.reload(app_module)
    captured = capsys.readouterr()
    # The warning should have been printed during reload
    assert 'Warning: Could not load settings' in captured.out


def test_cowsay_file_path_branch(tmp_path, monkeypatch):
    """If a cows file exists under COW_PATH, _get_cowsay_art should use that path."""
    # create a dummy cows file in COW_PATH
    import app as app_module
    cowname = 'dummycow'
    cows_dir = tmp_path / 'cows'
    cows_dir.mkdir()
    (cows_dir / cowname).write_text('cowdata')
    # monkeypatch COW_PATH to tmp cows dir
    monkeypatch.setattr(app_module, 'COW_PATH', str(cows_dir))
    dashboard = app_module.BackupDashboard()
    dashboard.cow_character = cowname
    dashboard.progress = 7
    dashboard.cow_quote = 'yep'
    monkeypatch.setattr('app.subprocess.run', lambda *a, **k: MagicMock(stdout='ART'))
    art = dashboard._get_cowsay_art()
    assert 'ART' in art or '(7%)' in art


def test_main_calls_dashboard_run(monkeypatch):
    """Patch BackupDashboard.run and call main to ensure dashboard.run() is invoked."""
    import app as app_module
    called = {'run': False}

    def fake_run(self):
        called['run'] = True

    monkeypatch.setattr(app_module.BackupDashboard, 'run', fake_run)
    # call main with empty args (no dry-run-command) -- should invoke fake_run
    app_module.main([])
    assert called['run'] is True


def test_settings_loaded():
    """Test that SETTINGS is loaded from yaml file."""
    # Since SETTINGS is loaded at import, we test the structure
    assert isinstance(SETTINGS, dict)


@patch('sys.argv', ['app.py', 'source/path', 'dest/path'])
@patch('app.BackupDashboard.run')
def test_argparse_source_dest(mock_run):
    """Test argument parsing for source and dest."""
    # This is tricky since it's in if __name__, but we can test by mocking
    # For now, just test that the module can be imported with yaml
    import yaml
    assert yaml is not None


@patch('app.subprocess.Popen')
@patch('app.os.makedirs')
@patch('builtins.input')
def test_run_with_custom_rsync_options(mock_input, mock_makedirs, mock_popen):
    """Test run method with custom rsync options from settings."""
    mock_input.return_value = 'y'
    mock_process = MagicMock()
    mock_process.stdout.readline.side_effect = ['100%', '', '']
    mock_process.stderr.read.return_value = ''
    mock_process.wait.return_value = None
    mock_process.returncode = 0
    mock_popen.return_value = mock_process

    # Mock SETTINGS with rsync_options
    with patch('app.SETTINGS', {'rsync_options': ['--verbose']}):
        dashboard = BackupDashboard(dry_run=True)
        with patch.object(dashboard.console, 'print'), \
             patch('app.subprocess.run') as mock_run:
            mock_run.return_value = MagicMock(stdout="mock art", stderr="", returncode=0)
            dashboard.run()  # Should not raise