#!/usr/bin/env bash
set -euo pipefail

IMAGE_TAG="${1:-0.2.0}"
IMAGE_NAME="sudoku-app:${IMAGE_TAG}"
TAR_FILE="sudoku-app_${IMAGE_TAG}.tar"

cd "$(dirname "$0")/.."

docker save -o "${TAR_FILE}" "${IMAGE_NAME}"
sudo k3s ctr images import "${TAR_FILE}"

echo "Imported ${IMAGE_NAME} into k3s containerd"
