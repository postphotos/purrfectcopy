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
	# Ensure 'pip' is available. If `python -m pip` is missing we prefer to use
	# an existing `pip3`/`pip` on PATH (e.g. from pyenv shims) before attempting
	# to bootstrap via ensurepip. This helps on developer machines where the
	# active `python` may not have pip but the user has pip3 available.
	BUILD_INSTALLED=false
	if ! python -m pip --version >/dev/null 2>&1; then
		echo "python -m pip not available in this Python; checking for pip3/pip on PATH..."
		PIP_CMD=""
		if command -v pip3 >/dev/null 2>&1; then
			PIP_CMD="pip3"
		elif command -v pip >/dev/null 2>&1; then
			PIP_CMD="pip"
		fi

		if [ -n "$PIP_CMD" ]; then
			echo "Found '$PIP_CMD' on PATH; trying to use it to install 'build'..."
			if "$PIP_CMD" install --upgrade --no-cache-dir build; then
				BUILD_INSTALLED=true
				echo "Installed 'build' via $PIP_CMD"
			else
				echo "Failed to install 'build' via $PIP_CMD; will try ensurepip..." >&2
			fi
		fi

		if [ "$BUILD_INSTALLED" != "true" ]; then
			echo "Attempting to bootstrap pip with ensurepip..."
			if python -m ensurepip --upgrade >/dev/null 2>&1; then
				echo "Bootstrapped pip via ensurepip"
			else
				echo "Failed to bootstrap pip with ensurepip. Please ensure pip is available in your environment." >&2
				echo "You can try: python -m ensurepip --upgrade" >&2
				exit 1
			fi
		fi
	fi

	# Finally, ensure 'build' is installed using python -m pip if not already.
	if [ "$BUILD_INSTALLED" != "true" ]; then
		if ! python -m pip install --upgrade --no-cache-dir build; then
			echo "Failed to install 'build' with python -m pip. This commonly happens when your system is low on disk space." >&2
			echo "Try freeing some space or manually installing 'build' in your venv with:" >&2
			echo "python -m pip install --upgrade --no-cache-dir build" >&2
			echo "If you have aggressive caching or a small /tmp, consider setting PIP_CACHE_DIR to a directory on a drive with space." >&2
			echo "Example: PIP_CACHE_DIR=~/.cache/pip python -m pip install --upgrade --no-cache-dir build" >&2
			exit 1
		fi
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

		# Prepare a fake HOME on the host to mount into the container so setup.sh
		# can write shell config files (this keeps the project mount read-only
		# while allowing setup to modify HOME).
		tmp_home=$(mktemp -d)
		cat > "$tmp_home/.pcopy-main-backup.yml" <<'YAML'
		main-backup:
		  source: "/data/source"
		  dest: "/data/dest"
		rsync_options:
		  - "--verbose"
		YAML

		echo "Smoke-test: run setup.sh --no-deps inside container and exercise dry-run backup"
		# Mount project read-only to simulate image contents, provide a writable HOME, and run setup+dry-run backup.
		docker run --rm \
		  -e HOME=/home/tester \
		  -v "$tmp_home":/home/tester:rw \
		  -v "$(pwd)":/app:ro -w /app \
		  pcopy-smoketest:latest \
		  /bin/bash -eux -c "\
		    /bin/bash ./setup.sh --no-deps && \
		    PCOPY_TEST_MODE=1 ./run-backup.sh do main-backup --dry-run\
		  "

		echo "Smoke-test: also exercise non-root run (dry-run)"
		docker run --rm \
		  -e RUN_AS=nonroot -e HOME=/home/tester \
		  -v "$tmp_home":/home/tester:rw \
		  -v "$(pwd)":/app:ro -w /app \
		  pcopy-smoketest:latest \
		  /bin/bash -eux -c "\
		    /bin/bash ./setup.sh --no-deps && \
		    PCOPY_TEST_MODE=1 ./run-backup.sh do main-backup --dry-run\
		  "

		# Clean up temporary home
		rm -rf "$tmp_home"
	else
		echo "Docker daemon not running; skipping container smoke-tests."
	fi
else
	echo "Docker CLI not found; skipping container smoke-tests."
fi

echo "All tests (including container smoke-tests where available) executed."
