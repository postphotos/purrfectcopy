#!/usr/bin/env bash
# Deterministic no-warning demo helper.
# Usage: ./scripts/demo-clean.sh [duration_seconds]
set -euo pipefail

DURATION=${1:-0.2}
PCOPY_TEST_MODE=${PCOPY_TEST_MODE:-1}

python3 -c "import os; os.environ.setdefault('PCOPY_TEST_MODE', '${PCOPY_TEST_MODE}'); from pcopy.dashboard_live import LiveDashboard; LiveDashboard(test_mode=True).run_demo(duration=${DURATION})"
