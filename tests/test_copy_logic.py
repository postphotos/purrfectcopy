from pathlib import Path
import time
import os

from pcopy.copy_logic import perform_backup


def test_perform_backup_timestamp_and_new_copy(tmp_path: Path, monkeypatch):
    src = tmp_path / 'src'
    dst = tmp_path / 'dst'
    src.mkdir()
    dst.mkdir()

    # create an existing file in dest and a newer file in source
    src_f = src / 'file1.txt'
    dst_f = dst / 'file1.txt'
    src_f.write_text('new content')
    # sleep to ensure mtime difference
    time.sleep(0.01)
    dst_f.write_text('old content')
    # make src newer than dest
    os.utime(str(src_f), None)
    # create a new file present only in src
    new_src = src / 'new.txt'
    new_src.write_text('hello')

    # Run without rsync to test Python-only behavior
    res = perform_backup(src, dst, run_rsync=False)
    # timestamped file should exist in dst
    assert len(res['timestamped']) == 1
    ts_path = Path(res['timestamped'][0])
    assert ts_path.exists()
    # new file should have been copied
    assert (dst / 'new.txt').exists()
    assert res['rsync_used'] is False


def test_perform_backup_skips_when_source_missing(tmp_path: Path):
    s = tmp_path / 'noexist'
    d = tmp_path / 'd'
    d.mkdir()
    try:
        perform_backup(s, d, run_rsync=False)
    except FileNotFoundError:
        assert True
    else:
        assert False, 'expected FileNotFoundError'
