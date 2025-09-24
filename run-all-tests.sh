#!/usr/bin/env bash
set -euo pipefail

# Accept --no-docker to skip Docker smoke-tests
NO_DOCKER=false
for arg in "$@"; do
	case "$arg" in
		--no-docker) NO_DOCKER=true ;;
	esac
done

echo "Running pyright on pcopy..."
uv run pyright pcopy

echo "Ensuring 'build' package is available for wheel tests..."
if ! python -c "import build" >/dev/null 2>&1; then
	echo "Installing build package (using --no-cache-dir to reduce disk usage)..."
	# Ensure 'pip' bootstrap exists in this Python environment. Some venvs
	# are created without pip available; try to bootstrap it with ensurepip.
	if ! python -m pip --version >/dev/null 2>&1; then
		echo "pip not found in this Python environment; attempting to bootstrap with ensurepip..."
		if python -m ensurepip --upgrade >/dev/null 2>&1; then
			echo "Bootstrapped pip via ensurepip"
		else
			echo "Failed to bootstrap pip with ensurepip. Please ensure pip is available in your environment." >&2
			echo "You can try: python -m ensurepip --upgrade" >&2
			exit 1
		fi
	fi

	if ! python -m pip install --upgrade --no-cache-dir build; then
		echo "Failed to install 'build'. This commonly happens when your system is low on disk space." >&2
		echo "Try freeing some space or manually installing 'build' in your venv with:" >&2
		echo "python -m pip install --upgrade --no-cache-dir build" >&2
		echo "If you have aggressive caching or a small /tmp, consider setting PIP_CACHE_DIR to a directory on a drive with space." >&2
		echo "Example: PIP_CACHE_DIR=~/.cache/pip python -m pip install --upgrade --no-cache-dir build" >&2
		exit 1
	fi
fi

echo "Running pytest with coverage..."
uv run pytest --cov=pcopy --cov-report=term-missing

echo "Building smoke-test Docker image..."
if [ "$NO_DOCKER" = true ]; then
	echo "--no-docker supplied; skipping container smoke-tests."
elif command -v docker >/dev/null 2>&1; then
	# Check if docker daemon is available
	if docker info >/dev/null 2>&1; then
		echo "Building smoke-test Docker image..."
		docker build -f Dockerfile.alpine -t pcopy-smoketest:latest .

		echo "Smoke-test: dry-run as root"
		docker run --rm pcopy-smoketest:latest --dry-run

		echo "Smoke-test: real-run as root"
		docker run --rm pcopy-smoketest:latest || true

		echo "Smoke-test: dry-run as non-root"
		docker run --rm -e RUN_AS=nonroot pcopy-smoketest:latest --dry-run
	else
		echo "Docker daemon not running; skipping container smoke-tests."
	fi
else
	echo "Docker CLI not found; skipping container smoke-tests."
fi

echo "All tests (including container smoke-tests where available) executed."
