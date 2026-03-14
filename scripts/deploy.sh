#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
kubectl apply -f k8s/sudoku-configmap.yaml
kubectl apply -f k8s/sudoku-redis-deployment.yaml
kubectl apply -f k8s/sudoku-redis-service.yaml
kubectl apply -f k8s/sudoku-app-deployment.yaml
kubectl apply -f k8s/sudoku-app-service.yaml
kubectl rollout status deployment/sudoku-redis
kubectl rollout status deployment/sudoku-app
kubectl get pods -o wide
kubectl get svc
