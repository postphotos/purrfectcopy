from pcopy.dashboard import BackupDashboard


def test_format_elapsed_and_files_progress():
    d = BackupDashboard(boring=False)
    assert d.format_elapsed(30) == '0m'
    assert d.format_elapsed(3600) == '1h0m'
    assert d.files_progress(0, 0) == '0/0'


def test_show_message_non_boring(capsys):
    d = BackupDashboard(boring=False)
    d.show_message('hi')
    captured = capsys.readouterr()
    assert 'hi' in captured.out
