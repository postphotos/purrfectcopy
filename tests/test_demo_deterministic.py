import os

from pcopy.dashboard_live import LiveDashboard


def test_demo_is_deterministic(monkeypatch, tmp_path):
    # ensure PCOPY_TEST_MODE triggers deterministic demo
    monkeypatch.setenv('PCOPY_TEST_MODE', '1')
    dash1 = LiveDashboard(test_mode=True, cow_hold_seconds=0)
    dash1.run_demo(duration=0.1)
    cat1 = (dash1.cow_character, dash1.cow_quote)

    # run again in a fresh instance
    dash2 = LiveDashboard(test_mode=True, cow_hold_seconds=0)
    dash2.run_demo(duration=0.1)
    cat2 = (dash2.cow_character, dash2.cow_quote)

    assert cat1 == cat2
