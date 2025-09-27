from pcopy.dashboard_live import LiveDashboard


def test_update_from_rsync_line_parses_progress_and_files():
    dash = LiveDashboard(test_mode=True, cow_hold_seconds=0)

    # Simulate rsync progress line
    dash.update_from_rsync_line(' 45% 1.23MB/s 0:00:02')
    assert dash.progress == 45

    # Simulate file transfer line (rsync style)
    dash.update_from_rsync_line('>f+++++++++ some/path/file.txt')
    assert dash.current_file.endswith('some/path/file.txt')
    assert dash.files_moved_count >= 1

    # Simulate total transferred line
    dash.update_from_rsync_line('Total transferred file size: 1.23M bytes')
    assert '1.23' in dash.transferred
