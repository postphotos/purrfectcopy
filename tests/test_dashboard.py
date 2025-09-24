from pcopy.dashboard import BackupDashboard


def test_dashboard_format_elapsed_and_progress():
    d = BackupDashboard(boring=True)
    s = d.format_elapsed(125)
    assert isinstance(s, str)
    assert d.files_progress(10, 3) == '3/10'


def test_show_message_boring(capsys):
    d = BackupDashboard(boring=True)
    d.show_message('hi')
    captured = capsys.readouterr()
    assert 'hi' in captured.out
