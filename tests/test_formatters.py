import pytest
from pcopy import runner


def test_parse_transferred_bytes_bytes_and_units():
    assert runner._parse_transferred_bytes_ml('Total transferred file size: 12345 bytes') == 12345
    assert runner._parse_transferred_bytes_ml('12345 bytes') == 12345
    assert runner._parse_transferred_bytes_ml('1.2MB') == int(1.2 * 1024 * 1024)
    assert runner._parse_transferred_bytes_ml('1.2 MB') == int(1.2 * 1024 * 1024)
    assert runner._parse_transferred_bytes_ml('2G') == 2 * 1024 ** 3
    assert runner._parse_transferred_bytes_ml('') is None
    assert runner._parse_transferred_bytes_ml(None) is None


def test_format_bytes_human_readable():
    assert runner._format_bytes_ml(0) == '0 bytes'
    assert runner._format_bytes_ml(500) == '500 bytes'
    assert runner._format_bytes_ml(1500).endswith('KB')
    assert runner._format_bytes_ml(1024 * 1024).endswith('MB')
    large = 5 * 1024 ** 3
    assert runner._format_bytes_ml(large).endswith('GB')


def test_format_duration_human_readable():
    assert runner._format_duration_ml(None) == '0s'
    assert runner._format_duration_ml(0) == '0s'
    assert runner._format_duration_ml(59) == '59s'
    assert runner._format_duration_ml(60) == '1m 0s'
    assert runner._format_duration_ml(3661) == '1h 1m 1s'


def test_parse_and_format_round_trip():
    s = 'Total transferred file size: 2048 bytes'
    n = runner._parse_transferred_bytes_ml(s)
    assert n == 2048
    assert 'KB' in runner._format_bytes_ml(n)
