# Kubernetes deployment evidence

## Environment and workload

- Kind v0.33.0, cluster `minipay`, Kubernetes v1.37.0.
- Node `minipay-control-plane` reached `Ready`; kube-system pods were `Running`.
- API Deployment: 2/2 ready. PostgreSQL StatefulSet: 1/1 ready.
- PostgreSQL PVC: 1 GiB, `Bound`; API and DB Services are ClusterIP.

## Deployment and checks

```bash
./kubernetes/deploy.sh
kubectl get all,pvc -n minipay
kubectl rollout status statefulset/minipay-db -n minipay
kubectl rollout status deployment/minipay-api -n minipay
kubectl port-forward -n minipay service/minipay-api 8081:80
curl -i http://127.0.0.1:8081/health
curl -i http://127.0.0.1:8081/
```

`GET /health` returned HTTP 200 with database status `ok`; homepage GET returned HTTP 200. The UI created and searched transaction `TXN725A974BA3D3`: payment ID 1, amount `100.00`, `SUCCESS`, one callback attempt. The API key remains in the ignored local file `.k8s-api-key` and is intentionally omitted from evidence.

## Operational inspection

```bash
kubectl describe deployment minipay-api -n minipay
kubectl describe statefulset minipay-db -n minipay
kubectl logs -n minipay deployment/minipay-api --all-pods=true
kubectl logs -n minipay statefulset/minipay-db
kubectl rollout restart deployment/minipay-api -n minipay
kubectl rollout status deployment/minipay-api -n minipay
```

Rancher feasibility and any limitations are recorded in `rancher.md`.

## Restart validation

Ran `kubectl rollout restart deployment/minipay-api -n minipay` and waited with `kubectl rollout status`. The new ReplicaSet reached 2/2 updated and available replicas (Deployment revision 2). The previous pod was briefly `Terminating` as expected during the rolling update. `kubectl describe deployment` confirmed CPU/memory requests and limits, startup/liveness/readiness probes, and Secret references for `DATABASE_URL` and `API_KEY`. API logs showed startup plus successful `/` and `/health` probe responses. PostgreSQL remained 1/1 Ready and its PVC remained Bound.