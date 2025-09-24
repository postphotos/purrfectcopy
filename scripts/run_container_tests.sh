#!/usr/bin/env bash
set -euo pipefail

# Builds the Alpine test image and runs the three smoke-tests locally:
# 1) dry-run as root
# 2) real-run as root
# 3) dry-run as non-root (RUN_AS=nonroot)

IMAGE_NAME=pcopy-smoketest:local
DOCKERFILE=Dockerfile.alpine

echo "Building image ${IMAGE_NAME}..."
docker build -f "$DOCKERFILE" -t "$IMAGE_NAME" .

echo "Running dry-run as root..."
docker run --rm "$IMAGE_NAME" --dry-run

echo "Running real-run as root (may modify container data)..."
docker run --rm "$IMAGE_NAME"

echo "Running dry-run as non-root..."
docker run --rm -e RUN_AS=nonroot "$IMAGE_NAME" --dry-run

echo "Container smoke tests complete." 

echo "Running inception test inside the container (runs run-all-tests.sh --no-docker)"
# Override the image ENTRYPOINT and run the project test script inside the container
docker run --rm --entrypoint /bin/sh "$IMAGE_NAME" -c "./run-all-tests.sh --no-docker"

echo "Inception test complete."
