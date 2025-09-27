#!/bin/bash

# -----------------------------------------------------------------------------
#  Purrfect Backup - Setup Script v1.0 🛠️
# -----------------------------------------------------------------------------
#  This script sets up the Purrfect Backup environment and installs the pcopy alias.
#

set -e

# Accept --no-deps to skip installing uv and Python dependencies (useful for CI/test)
NO_DEPS=false
TUI=false
for arg in "$@"; do
    case "$arg" in
        --no-deps) NO_DEPS=true ;;
        --tui) TUI=true ;;
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

# --- Create a main named backup in ~/.pcopy-main-backup.yml
MAIN_SETTINGS="$HOME/.pcopy-main-backup.yml"
SKIP_WRITE=false
if [ -f "$MAIN_SETTINGS" ]; then
    echo "⚠️  Found existing $MAIN_SETTINGS"
    if [ -t 0 ]; then
        # Interactive terminal: ask whether to keep the existing settings
        read -p "Do you want to keep the existing settings at $MAIN_SETTINGS? [Y/n] " keep_settings
        case "$keep_settings" in
            [Nn]*)
                ts=$(date +%Y%m%d_%H%M%S)
                mv "$MAIN_SETTINGS" "${MAIN_SETTINGS}.bak.${ts}"
                echo "→ Moved existing settings to ${MAIN_SETTINGS}.bak.${ts}"
                ;;
            *)
                echo "→ Keeping existing settings at $MAIN_SETTINGS"
                SKIP_WRITE=true
                ;;
        esac
    else
        # Non-interactive: preserve previous behavior and back up the settings
        ts=$(date +%Y%m%d_%H%M%S)
        mv "$MAIN_SETTINGS" "${MAIN_SETTINGS}.bak.${ts}"
        echo "→ Moved existing settings to ${MAIN_SETTINGS}.bak.${ts}"
    fi
fi

# If running non-interactively (e.g., inside CI or a container), read
# paths from env vars or fall back to sensible defaults so setup doesn't hang.
# If requested, run TUI mode (prompt_toolkit) to provide a richer interactive
# experience.
if [ "${TUI:-false}" = "true" ]; then
    if command -v python3 >/dev/null 2>&1; then
        python3 ./scripts/setup_tui.py
        exit 0
    else
        echo "⚠️  Python3 not found; cannot run TUI. Falling back to default prompts."
    fi
fi

# Only prompt for new source/dest if we're not keeping the existing settings
if [ "$SKIP_WRITE" != "true" ]; then
    if [ -t 0 ]; then
        # interactive terminal — prompt the user with path-completion when possible
        # Friendly slogans to make setup delightful
        SLOGANS=("May your backups be purrfect!" "Backing up = peace of mind 🐾" "Cats approve this backup")
        SLOGAN=${SLOGANS[$((RANDOM % ${#SLOGANS[@]}))]}
        echo "🐱 $SLOGAN"

        if [ -n "$BASH_VERSION" ]; then
            # Bash: enable readline/tab completion during read
            read -e -p "Enter the path you want to back up (source) [tab works]: " SRC_PATH
            read -e -p "Enter the destination path for backups [tab works]: " DST_PATH
        elif [ -n "$ZSH_VERSION" ]; then
            # Zsh: use vared for inline editing with completion
            echo "(You can use TAB to complete paths in zsh)"
            vared -p "Enter the path you want to back up (source): " -c SRC_PATH
            vared -p "Enter the destination path for backups: " -c DST_PATH
        else
            read -p "Enter the path you want to back up (source): " SRC_PATH
            read -p "Enter the destination path for backups: " DST_PATH
        fi
        # Offer to create the destination if it doesn't exist
        if [ ! -e "$DST_PATH" ]; then
            read -p "Destination '$DST_PATH' does not exist. Create it now? [Y/n] " create_dst
            case "$create_dst" in
                [Nn]*) echo "Will not create destination; please ensure it exists before running backups." ;;
                *) mkdir -p "$DST_PATH" && echo "Created $DST_PATH" ;;
            esac
        fi
    else
        echo "ℹ️  Non-interactive setup detected — reading backup paths from environment or using defaults"
        SRC_PATH=${PCOPY_MAIN_SRC:-"/data"}
        DST_PATH=${PCOPY_MAIN_DST:-"/backup"}
        echo "→ Using source: $SRC_PATH"
        echo "→ Using dest:   $DST_PATH"
    fi
fi

# Only write new settings if the user didn't ask to keep the existing file
if [ "$SKIP_WRITE" != "true" ]; then
    cat > "$MAIN_SETTINGS" <<EOF
main-backup:
    source: "$SRC_PATH"
    dest: "$DST_PATH"
rsync_options: []
EOF
    echo "✅ Wrote $MAIN_SETTINGS"
else
    echo "ℹ️  Using existing settings at $MAIN_SETTINGS; no new settings were written."
fi

# Add a small shell completion helper for the 'pcopy' function so tabbing is delightful
COMPLETION_MARKER="# pcopy_completion"
if ! grep -q "$COMPLETION_MARKER" "$SHELL_CONFIG" 2>/dev/null; then
    echo "" >> "$SHELL_CONFIG"
    echo "$COMPLETION_MARKER" >> "$SHELL_CONFIG"
    if [ -n "$BASH_VERSION" ]; then
        cat >> "$SHELL_CONFIG" <<'BASHCOMP'
_pcopy() {
  local cur
  cur="${COMP_WORDS[COMP_CWORD]}"
  COMPREPLY=( $(compgen -W "do main-backup --dry-run --help" -- "$cur") )
}
complete -F _pcopy pcopy
BASHCOMP
    elif [ -n "$ZSH_VERSION" ]; then
        cat >> "$SHELL_CONFIG" <<'ZSHCOMP'
_pcopy() {
  compadd do main-backup --dry-run --help
}
compdef _pcopy pcopy
ZSHCOMP
    fi
    echo "✅ Installed simple pcopy tab-completion into $SHELL_CONFIG"
fi

# --- Move loose scripts in project root (except setup.sh and run-backup.sh) into ./scripts
SCRIPTS_DIR="$PROJECT_DIR/scripts"
mkdir -p "$SCRIPTS_DIR"
shopt -s nullglob
for f in "$PROJECT_DIR"/*.sh; do
    base=$(basename "$f")
    if [ "$base" != "setup.sh" ] && [ "$base" != "run-backup.sh" ]; then
        target="$SCRIPTS_DIR/$base"
        if [ -e "$target" ]; then
            ts=$(date +%Y%m%d_%H%M%S)
            mv "$target" "${target}.bak.${ts}"
        fi
        mv "$f" "$target"
        chmod +x "$target"
        echo "Moved $f -> $target"
    fi
done
shopt -u nullglob

# Ask to run a dry-run now
echo ""
read -p "Would you like to run a dry-run of the backup now? [y/N] " doit
case "$doit" in
    [Yy]*)
        echo "Running dry-run..."
        ./run-backup.sh --dry-run || echo "Dry-run completed with non-zero exit code"
        ;;
    *)
        echo "Ok — you can run: pcopy do main-backup --dry-run" ;;
esac

# Add pcopy function to both bashrc and zshrc (prefer detected shell but ensure both are covered)
BASH_CONFIG="$HOME/.bashrc"
ZSH_CONFIG="$HOME/.zshrc"
# Helper to append function if missing
_append_pcopy_if_missing() {
    target_file="$1"
    if [ ! -f "$target_file" ]; then
        touch "$target_file"
    fi
    if ! grep -q "pcopy()" "$target_file" 2>/dev/null; then
        echo "" >> "$target_file"
        echo "# Purrfect Backup pcopy function" >> "$target_file"
        echo "pcopy() {" >> "$target_file"
        echo "    if [ \"\$1\" = \"do\" ] || [ \"\$1\" = \"main-backup\" ]; then" >> "$target_file"
        echo "        shift" >> "$target_file"
        echo "        ./run-backup.sh \"\$@\"" >> "$target_file"
        echo "    else" >> "$target_file"
        echo "        ./run-backup.sh \"\$@\"" >> "$target_file"
        echo "    fi" >> "$target_file"
        echo "}" >> "$target_file"
        echo "✅ Installed pcopy function into $target_file"
    fi
}

# Prefer current shell to notify the user which file to source, but add to both.
if [ -n "$ZSH_VERSION" ] || ( [ -z "$ZSH_VERSION" ] && [ "${SHELL##*/}" = "zsh" ] ); then
    PREFERRED="$ZSH_CONFIG"
else
    PREFERRED="$BASH_CONFIG"
fi

_append_pcopy_if_missing "$BASH_CONFIG"
_append_pcopy_if_missing "$ZSH_CONFIG"

if [ -f "$PREFERRED" ]; then
    echo "🔄 Please run 'source $PREFERRED' or restart your terminal to use pcopy."
else
    echo "🔄 Please restart your terminal to use pcopy."
fi