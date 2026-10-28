# Kubernetes starter manifest findings

Reviewed `starter/kubernetes/broken-api.yaml` against the actual application port and Compose configuration.

| Finding | Impact | Correction |
|---|---|---|
| `image: YOUR_IMAGE_HERE` placeholder | No usable API image | Build `minipay-api:local` and load it into Kind |
| Readiness probe uses 8081; API listens on 8080 | Pod remains unready | Probe named HTTP port 8080 |
| Service selector `app: minipay-backend` differs from pod label `app: minipay-api` | No matching endpoints | Align selector and pod labels |
| Service targetPort is 8081 | Requests sent to wrong container port | Route to named HTTP port 8080 |
| Assumes namespace `minipay`, but no namespace manifest | Fresh-cluster apply fails | Add namespace manifest |
| Assumes `minipay-db`, but no database workload/service | API cannot resolve/connect to database | Add PostgreSQL StatefulSet and Service |
| No persistent volume | Database data not durable across pod replacement | Add 1 GiB PVC via StatefulSet |
| No ConfigMap/Secret/resources | Configuration and resource use unmanaged | Add ConfigMap, generated Secret, resource requests/limits |
| Liveness/readiness share DB-dependent health check | DB outage could cause unnecessary restarts | Readiness checks `/health`; startup/liveness check `/` |

Validation: Kind node Ready; API 2/2, PostgreSQL 1/1, PVC Bound; health and UI GET returned HTTP 200; browser transaction succeeded. See `INCIDENT-002-RCA.md` and `../evidence/kubernetes-deployment.md`.
