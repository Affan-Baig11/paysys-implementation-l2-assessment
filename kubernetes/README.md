# MiniPay on Kubernetes

This directory deploys the demo API and PostgreSQL to a local Kubernetes cluster. The API image is built locally and loaded into Kind. Database and API credentials are generated into a Kubernetes Secret at deploy time and are not stored in Git.

## Prerequisites

- Docker is running.
- `kubectl` and Kind are installed.
- The active context is `kind-minipay` (or another cluster you intend to use).
- Run commands from the repository root.

## Deploy

The deployment script creates the namespace, generates a local API key and database password when the Secret is absent, creates the schema ConfigMap from the canonical `database/schema.sql`, builds and loads the API image, and applies the database and API workloads:

```bash
./kubernetes/deploy.sh
```

On first deployment, the generated API key is stored in the ignored local file `.k8s-api-key`; read it locally with `cat .k8s-api-key` to sign in to the UI. Do not share it or include it in evidence. If the Secret already existed and the file is missing, retrieve the key locally with `kubectl get secret minipay-credentials -n minipay -o jsonpath='{.data.api-key}' | base64 -d`.

## Verify and access

```bash
kubectl get all,pvc -n minipay
kubectl rollout status statefulset/minipay-db -n minipay
kubectl rollout status deployment/minipay-api -n minipay
kubectl logs -n minipay statefulset/minipay-db
kubectl logs -n minipay deployment/minipay-api --all-pods=true
kubectl port-forward -n minipay service/minipay-api 8081:80
```

In another terminal, check `http://127.0.0.1:8081/` in a browser and run:

```bash
curl -i http://127.0.0.1:8081/health
```

The UI accepts the generated API key. Stop port-forwarding with Ctrl+C. To inspect rollout status after changing a manifest, run `kubectl rollout status deployment/minipay-api -n minipay`; to restart it, run `kubectl rollout restart deployment/minipay-api -n minipay`.

## Storage and secrets

PostgreSQL runs as a single-replica StatefulSet with a 1 GiB PVC. The local Kind StorageClass supplies the volume. The database schema is mounted as an initialization script and is applied by the official PostgreSQL image when the data directory is first initialized. To reset this disposable demo database, remove the StatefulSet PVC only after confirming its data is no longer needed; deleting a PVC destroys the stored database contents.

Secrets are generated at deployment time with `openssl` and passed directly to `kubectl`; they are not written to a YAML file. The generated values are suitable only for this local assessment demo.

## Limits

This is a local single-node Kind demonstration. It shows Kubernetes deployment, service discovery, probes, resource requests/limits, Secret references, and persistent storage. It is not a highly available or production-hardened payment platform. Rancher evaluation and limitations are recorded separately in `../evidence/rancher.md`.
