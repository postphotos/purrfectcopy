import time

from pcopy.dashboard_live import LiveDashboard


def test_run_demo_completes_quickly(monkeypatch):
    # Ensure demo runs quickly by reducing sleep via monkeypatch
    monkeypatch.setattr('time.sleep', lambda s: None)
    dash = LiveDashboard(demo_mode=True, test_mode=True, cow_hold_seconds=0)
    dash.run_demo(duration=1, steps=5)
    # At end, progress should be 100 and no errors
    assert dash.progress == 100
    assert dash.errors == []
