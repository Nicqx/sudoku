#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${1:-0.1.0}"
IMAGE_NAME="sudoku-app:${IMAGE_TAG}"

cd "$(dirname "$0")/.."
docker build -t "${IMAGE_NAME}" .
echo "Built ${IMAGE_NAME}"
