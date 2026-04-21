#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

kubectl apply -f k8s/sudoku-configmap.yaml
kubectl apply -f k8s/sudoku-app-deployment.yaml
kubectl apply -f k8s/sudoku-app-service.yaml

kubectl rollout status deployment/sudoku-app --timeout=5m

kubectl get pods -o wide | grep -E 'sudoku|NAME'
kubectl get svc | grep -E 'sudoku|redis|NAME'
