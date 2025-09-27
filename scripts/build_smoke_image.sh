#!/usr/bin/env bash
set -euo pipefail

# Build the smoke/test image for real integration tests
# Usage: ./scripts/build_smoke_image.sh [image-tag] [dockerfile]

IMAGE_TAG=${1:-pcopy-smoketest:smoke}
DOCKERFILE=${2:-Dockerfile.smoke}
ROOT_DIR=$(cd "$(dirname "$0")/.." && pwd)

echo "Building Docker image ${IMAGE_TAG} from ${DOCKERFILE} (cwd=${ROOT_DIR})"

if ! command -v docker >/dev/null 2>&1; then
  echo "docker not found in PATH; please install Docker or run on a machine with docker available" >&2
  exit 2
fi

docker build -f "${ROOT_DIR}/${DOCKERFILE}" -t "${IMAGE_TAG}" "${ROOT_DIR}" \
  --progress=plain

echo "Built ${IMAGE_TAG}"