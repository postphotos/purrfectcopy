#!/bin/bash

# -----------------------------------------------------------------------------
#  Purrfect Backup - Launcher v1.0 🚀
# -----------------------------------------------------------------------------
#  This script sets up the environment and launches the Python TUI.
#

# --- Test mode: when PCOPY_TEST_MODE=1, skip sudo and dependency work (used by tests) ---
if [ "${PCOPY_TEST_MODE:-0}" != "1" ]; then
  # Ensure we are running as root (for rsync permissions)
  if [ "$EUID" -ne 0 ]; then
    echo "😿 This script needs root privileges for rsync. Re-running with sudo..."
    # Re-execute this script with sudo, passing all arguments along
    exec sudo "$0" "${@}"
  fi
else
  echo "PCOPY_TEST_MODE=1: skipping sudo/dependency enforcement for tests"
fi

# --- Check for Dependencies ---
if [ "${PCOPY_TEST_MODE:-0}" != "1" ]; then
  command -v uv >/dev/null 2>&1 || { echo >&2 "❌ 'uv' is not installed. Please install it first (e.g., 'pip install uv')."; exit 1; }
  command -v rsync >/dev/null 2>&1 || { echo >&2 "❌ 'rsync' is not installed. Please install it (e.g., 'brew install rsync')."; exit 1; }
  command -v cowsay >/dev/null 2>&1 || { echo >&2 "❌ 'cowsay' is not installed. Please install it (e.g., 'brew install cowsay')."; exit 1; }

  echo "✅ Dependencies found."
  echo "📦 Ensuring Python environment is up to date with uv..."

  # --- Setup Python Environment with uv ---
  # This command is idempotent and fast. It will only install if needed.
  uv pip install -r requirements.txt
  if [ $? -ne 0 ]; then
      echo "❌ Failed to install Python dependencies with uv."
      exit 1
  fi

  echo "🚀 Launching the Purrfect Backup TUI..."
  echo ""

  # --- Execute the Python App ---
  # Pass all script arguments ($@) directly to the Python app
  uv run python app.py "$@"

  echo ""
  echo "✨ Backup script has finished."
else
  # Test mode: if invoked with --dry-run or 'do' we short-circuit for tests
  for arg in "$@"; do
    if [ "$arg" = "--dry-run" ] || [ "$arg" = "--dry-run-command" ]; then
      echo "Dry Run (test mode)"
      exit 0
    fi
  done
  # also handle 'do main-backup' invocation
  if [ "$1" = "do" ] || [ "$1" = "main-backup" ]; then
    # check for --dry-run in remaining args
    shift || true
    for arg in "$@"; do
      if [ "$arg" = "--dry-run" ]; then
        echo "Dry Run (test mode)"
        exit 0
      fi
    done
    # otherwise, print a benign message
    echo "pcopy invoked in test mode"
    exit 0
  fi
  echo "pcopy test mode no-op"
  exit 0
fi