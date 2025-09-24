#!/bin/bash

# -----------------------------------------------------------------------------
#  Purrfect Backup - Launcher v1.0 🚀
# -----------------------------------------------------------------------------
#  This script sets up the environment and launches the Python TUI.
#

# --- Ensure we are running as root (for rsync permissions) ---
if [ "$EUID" -ne 0 ]; then
  echo "😿 This script needs root privileges for rsync. Re-running with sudo..."
  # Re-execute this script with sudo, passing all arguments along
  exec sudo "$0" "$@"
fi

# --- Check for Dependencies ---
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