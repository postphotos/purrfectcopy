#!/bin/bash

# -----------------------------------------------------------------------------
#  Purrfect Backup - Setup Script v1.0 🛠️
# -----------------------------------------------------------------------------
#  This script sets up the Purrfect Backup environment and installs the pcopy alias.
#

set -e

# Accept --no-deps to skip installing uv and Python dependencies (useful for CI/test)
NO_DEPS=false
for arg in "$@"; do
    case "$arg" in
        --no-deps) NO_DEPS=true ;;
    esac
done

echo "🐾 Setting up Purrfect Backup..."

PROJECT_DIR="$(pwd)"

# If the project directory is mounted read-only (common in container CI), skip
# trying to create virtualenvs or install into the project tree. This makes
# setup.sh safe to run inside read-only containers used by CI smoke-tests.
if [ "$NO_DEPS" = false ]; then
    if [ ! -w "$PROJECT_DIR" ]; then
        echo "⚠️  Project directory $PROJECT_DIR is not writable. Skipping dependency installation and venv creation."
        echo "If you need to install dependencies, re-run setup.sh from a writable checkout with --no-deps omitted."
    else
        # --- Check for uv ---
        if ! command -v uv >/dev/null 2>&1; then
            echo "📦 Installing uv (Python package manager)..."
            if ! python -m pip install --upgrade pip >/dev/null 2>&1 || ! python -m pip install uv >/dev/null 2>&1; then
                echo "⚠️  Failed to install uv via pip; continuing without uv. You can install it manually later: python -m pip install uv"
            else
                echo "✅ uv installed"
            fi
        else
            echo "✅ uv is installed."
        fi

        # --- Install Python dependencies ---
        echo "📦 Installing Python dependencies (if possible)..."
        if command -v uv >/dev/null 2>&1; then
            if ! uv pip install -r requirements.txt >/dev/null 2>&1; then
                echo "⚠️  Failed to install Python dependencies with uv; continuing. If you need dependencies, run 'python -m pip install -r requirements.txt' locally."
            else
                echo "✅ Dependencies installed."
            fi
        else
            echo "⚠️  'uv' not available; skipping automated dependency installation."
        fi
    fi
else
    echo "--no-deps supplied; skipping uv and dependency installation."
fi

# --- Add pcopy alias to shell config ---
SHELL_CONFIG=""
if [ -n "$ZSH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
else
    echo "⚠️  Could not detect shell. Please manually add the pcopy function to your shell config."
    echo "Add this to your ~/.bashrc or ~/.zshrc:"
    echo ""
    echo "pcopy() {"
    echo "    if [ \"\$1\" = \"do\" ] || [ \"\$1\" = \"main-backup\" ]; then"
    echo "        shift"
    echo "        ./run-backup.sh \"\$@\""
    echo "    else"
    echo "        ./run-backup.sh \"\$@\""
    echo "    fi"
    echo "}"
    exit 0
fi

# Ensure shell config exists and create parent dir if necessary
mkdir -p "$(dirname "$SHELL_CONFIG")"
if [ ! -f "$SHELL_CONFIG" ]; then
    touch "$SHELL_CONFIG"
fi

if grep -q "pcopy()" "$SHELL_CONFIG" 2>/dev/null; then
    echo "ℹ️  pcopy function already exists in $SHELL_CONFIG"
else
    echo "" >> "$SHELL_CONFIG"
    echo "# Purrfect Backup pcopy function" >> "$SHELL_CONFIG"
    echo "pcopy() {" >> "$SHELL_CONFIG"
    echo "    if [ \"\$1\" = \"do\" ] || [ \"\$1\" = \"main-backup\" ]; then" >> "$SHELL_CONFIG"
    echo "        shift" >> "$SHELL_CONFIG"
    echo "        ./run-backup.sh \"\$@\"" >> "$SHELL_CONFIG"
    echo "    else" >> "$SHELL_CONFIG"
    echo "        ./run-backup.sh \"\$@\"" >> "$SHELL_CONFIG"
    echo "    fi" >> "$SHELL_CONFIG"
    echo "}" >> "$SHELL_CONFIG"
    echo "✅ Added pcopy function to $SHELL_CONFIG"
    echo "🔄 Please run 'source $SHELL_CONFIG' or restart your terminal to use pcopy."
fi

echo ""
echo "🎉 Setup complete! You can now use:"
echo "  ./run-backup.sh          # Run the backup with default paths"
echo "  pcopy source dest        # Run backup with custom source/dest"
echo "  pcopy do main-backup     # Run main-backup using settings file"
echo ""
echo "For more options, see ./run-backup.sh --help"