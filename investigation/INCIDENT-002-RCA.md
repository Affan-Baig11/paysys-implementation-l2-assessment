# INCIDENT-002 – Application Unavailable After Deployment

## Summary

The supplied Kubernetes manifest contains defects that prevent reliable access to MiniPay. We deliberately inspected and corrected it, then deployed the application and PostgreSQL to a local Kind cluster.

## Observations and reproduction

The starter manifest uses `YOUR_IMAGE_HERE`, probes port 8081 although the API listens on 8080, and defines a Service selector that does not match the Deployment's pod label. The Service also targets port 8081. It assumes a `minipay` namespace and a `minipay-db` service that it does not create. Applying/running this manifest in a fresh cluster can fail to start the image, keep pods unready, and leave the Service without endpoints.

## Evidence and validation commands

```bash
kubectl get nodes
kubectl get all,pvc -n minipay
kubectl rollout status statefulset/minipay-db -n minipay
kubectl rollout status deployment/minipay-api -n minipay
kubectl port-forward -n minipay service/minipay-api 8081:80
curl -i http://127.0.0.1:8081/health
curl -i http://127.0.0.1:8081/
```

The Kind node reached `Ready`; system pods were `Running`. Deployment evidence showed API 2/2 ready, PostgreSQL 1/1 ready, and a 1 GiB PVC `Bound`. Health returned HTTP 200 with `{"status":"ok","database":"ok"}` and homepage GET returned HTTP 200. An authenticated health request also returned 200.

The browser UI completed a transaction flow through the Kubernetes Service: transaction `TXN725A974BA3D3`, payment ID 1, amount `100.00`, status `SUCCESS`, customer `Testing-Kube`, and one callback attempt. `curl -I /` returned 405 because the homepage route supports GET; normal browser GET succeeded.

## Root causes

1. Placeholder image reference was not runnable.
2. Readiness probe port 8081 did not match API port 8080.
3. Service selector `app: minipay-backend` did not match pod label `app: minipay-api`.
4. Service target port 8081 did not match the API listener.
5. Namespace, database workload/service, persistent storage, and configuration/secret resources were absent.

## Correction

Created the Kubernetes deployment in `kubernetes/`: local API image built and loaded into Kind; matching API labels and Service ports; two API replicas; PostgreSQL StatefulSet and Service; 1 GiB PVC; ConfigMap for non-sensitive settings/schema; Secret generated during deployment. Readiness probes check `/health` (including DB connectivity); startup/liveness check `/` so a DB outage does not restart a healthy API process. Both workloads specify resource requests and limits.

## Preventive controls

- Run server-side manifest validation and `kubectl diff` before rollout.
- Check Service selectors against pod-template labels and Service target ports against named container ports.
- Check images, namespace, ConfigMaps, Secrets, PVC binding, and readiness before exposing a release.
- Gate release on rollout status and an authenticated API smoke test.
- Keep generated secrets and local credential files out of Git.

## Validation after correction

The Kind node was `Ready`; API rollout reached 2/2, database reached 1/1, PVC was `Bound`, both HTTP health and homepage GET returned 200, and the UI completed customer/payment/search successfully through the Kubernetes Service.
