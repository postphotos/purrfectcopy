#!/usr/bin/env bash
# Demo script for maintainers: runs the interactive demo UI (non-destructive)
set -euo pipefail
PYTHONPATH=$(dirname "$0")/.. python3 -m pcopy.runner --demo
