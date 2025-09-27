#!/usr/bin/env bash
set -euo pipefail

# Run the real integration test flow using an existing or freshly-built smoke image
# Usage: ./scripts/run_real_integration.sh [image-tag] [src-dir] [dst-dir]

IMAGE_TAG=${1:-pcopy-smoketest:real}
SRC_DIR=${2:-$(pwd)/tmp-src}
DST_DIR=${3:-$(pwd)/tmp-dst}
HOME_DIR=${4:-$(pwd)/tmp-home}
ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

mkdir -p "${SRC_DIR}" "${DST_DIR}" "${HOME_DIR}"

if [ ! -f "${SRC_DIR}/hello.txt" ]; then
  echo "creating ${SRC_DIR}/hello.txt"
  echo "hello world" > "${SRC_DIR}/hello.txt"
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found; cannot run container-based integration" >&2
  exit 2
fi

# Run setup.sh inside the container and then run pcopy (non-dry-run)
set -x

docker run --rm \
  -v "${SRC_DIR}:/data/src:rw" \
  -v "${DST_DIR}:/data/dst:rw" \
  -v "${HOME_DIR}:/home/tester:rw" \
  "${IMAGE_TAG}" \
  /bin/sh -c "cd /app && HOME=/home/tester /app/setup.sh --no-deps && pcopy do main-backup"

RC=$?
set +x

if [ ${RC} -ne 0 ]; then
  echo "Container run exited with code ${RC}" >&2
  exit ${RC}
fi

echo "Integration run completed; check ${DST_DIR} for copied files"