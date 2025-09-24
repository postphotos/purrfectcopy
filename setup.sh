#!/bin/bash

# -----------------------------------------------------------------------------
#  Purrfect Backup - Setup Script v1.0 🛠️
# -----------------------------------------------------------------------------
#  This script sets up the Purrfect Backup environment and installs the pcopy alias.
#

set -e

echo "🐾 Setting up Purrfect Backup..."

# --- Check for uv ---
if ! command -v uv >/dev/null 2>&1; then
    echo "📦 Installing uv (Python package manager)..."
    pip install uv
    if [ $? -ne 0 ]; then
        echo "❌ Failed to install uv. Please install it manually: pip install uv"
        exit 1
    fi
fi

echo "✅ uv is installed."

# --- Install Python dependencies ---
echo "📦 Installing Python dependencies..."
uv pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install Python dependencies."
    exit 1
fi

echo "✅ Dependencies installed."

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

if [ -f "$SHELL_CONFIG" ]; then
    if grep -q "pcopy()" "$SHELL_CONFIG"; then
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
else
    echo "⚠️  Shell config file $SHELL_CONFIG not found. Please create it and add the pcopy function manually."
fi

echo ""
echo "🎉 Setup complete! You can now use:"
echo "  ./run-backup.sh          # Run the backup with default paths"
echo "  pcopy source dest        # Run backup with custom source/dest"
echo "  pcopy do main-backup     # Run main-backup using settings file"
echo ""
echo "For more options, see ./run-backup.sh --help"