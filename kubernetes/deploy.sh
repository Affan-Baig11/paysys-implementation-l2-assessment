#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

kubectl apply -f kubernetes/00-namespace.yaml
kubectl apply -f kubernetes/10-configmap.yaml
kubectl create configmap minipay-db-schema -n minipay \
  --from-file=001-schema.sql=database/schema.sql \
  --dry-run=client -o yaml | kubectl apply -f -

if ! kubectl get secret minipay-credentials -n minipay >/dev/null 2>&1; then
  DB_PASSWORD="$(openssl rand -hex 24)"
  API_KEY="$(openssl rand -hex 24)"
  kubectl create secret generic minipay-credentials -n minipay \
    --from-literal=postgres-password="$DB_PASSWORD" \
    --from-literal=api-key="$API_KEY" \
    --from-literal=database-url="postgresql://minipay:${DB_PASSWORD}@minipay-db:5432/minipay"
  printf '%s\n' "$API_KEY" > .k8s-api-key
  chmod 600 .k8s-api-key
  printf 'Created local credentials. API key is stored in ignored file .k8s-api-key.\n'
else
  printf 'Using existing minipay-credentials Secret.\n'
fi

docker build -t minipay-api:local -f api/Dockerfile .
kind load docker-image minipay-api:local --name minipay
kubectl apply -f kubernetes/20-database.yaml
kubectl rollout status statefulset/minipay-db -n minipay --timeout=180s
kubectl apply -f kubernetes/30-api.yaml
kubectl rollout status deployment/minipay-api -n minipay --timeout=180s
kubectl get all,pvc -n minipay
