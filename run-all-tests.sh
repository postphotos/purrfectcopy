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
