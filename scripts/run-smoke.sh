#!/usr/bin/env bash
# Build and run the smoke docker image quickly for local iteration
set -euo pipefail

IMAGE_TAG=${1:-pcopy-smoketest:smoke}

echo "Building smoke image ${IMAGE_TAG}..."
docker build -f Dockerfile.smoke -t ${IMAGE_TAG} .

echo "Running smoke image ${IMAGE_TAG} (PCOPY_TEST_MODE=1)..."
docker run --rm -e PCOPY_TEST_MODE=1 ${IMAGE_TAG}
