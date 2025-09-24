#!/bin/sh
set -e
# entrypoint wrapper: run as root by default, or as non-root if RUN_AS=nonroot
if [ "${RUN_AS:-}" = "nonroot" ]; then
  if command -v su-exec >/dev/null 2>&1; then
    exec su-exec tester uv run app.py "$@"
  else
    # fallback to su if su-exec missing
    exec su tester -s /bin/sh -c "uv run app.py $*"
  fi
else
  exec uv run app.py "$@"
fi
