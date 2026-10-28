# Rancher evidence and environment limitation

## Attempt and cluster visibility

- Started Rancher Manager v2.15.2 as a single Docker container for local development/testing, with HTTPS on port 8443 and a persistent Docker volume.
- Rancher UI opened at `https://localhost:8443` and displayed one active cluster named `local`, using Rancher's embedded K3s v1.36.2+k3s1. This is Rancher's own local management cluster; MiniPay runs separately in Kind (`kind-minipay`).
- Restarted the Rancher container and returned to the dashboard successfully.

Commands used:

```bash
docker run -d --restart=unless-stopped --name rancher-manager \
  -p 8082:80 -p 8443:443 -v rancher-data:/var/lib/rancher \
  --privileged rancher/rancher:v2.15.2
docker stop rancher-manager
docker start rancher-manager
```

## Registration attempt and blocker

Rancher needs its configured `server-url` to be reachable by both browser users and downstream cluster agents. The first instance used `https://localhost:8443`, which is reachable by the Windows browser but refers to the agent pod itself when used inside Kind.

A second clean test instance was created with a separate data volume. The candidate URL `https://host.docker.internal:8443` returned `pong` from a MiniPay pod, confirming Kind-side reachability. Windows Chrome could not resolve `host.docker.internal` (`DNS_PROBE_FINISHED_NXDOMAIN`). The corresponding Docker Desktop address `192.168.65.254` timed out from Chrome. The WSL shell also returned no result for `getent hosts host.docker.internal`.

The new setup therefore could not be completed from Windows Chrome with a URL also reachable from Kind. The new test container was stopped, and the original Rancher dashboard was restored. No Windows hosts-file or system DNS change was made. The Kind cluster and MiniPay workloads remain healthy and independently accessible with kubectl.

## Scope and operational procedure

Rancher installation was feasible and its dashboard/local cluster were demonstrated. Registration of the separate Kind cluster was blocked by the split Windows/WSL/Docker DNS and routing behavior above; MiniPay workloads therefore do not appear in Rancher's UI. This is a documented environment limitation rather than a successful Rancher-managed MiniPay deployment.

If the Kind cluster is registered in a network where the Rancher `server-url` is reachable from both the browser and cluster agents, the operational workflow is:

1. Open the downstream cluster and select the `minipay` project/namespace.
2. Open Workloads to check API Deployment replicas and the PostgreSQL StatefulSet; inspect pod status and recent events.
3. Open a pod's Logs view to inspect API or database startup and request logs.
4. Inspect the Deployment's environment variable references, probes, and resource requests/limits. Secret values should remain masked and never be copied into evidence.
5. Use the workload scale control or edit replicas to scale the API; use the rollout/restart control to restart it, then verify Ready replicas and health.
6. Use cluster/workload overview health and resource panels where metrics are available. This local test did not install Rancher's monitoring stack, so detailed historical CPU/memory charts are not claimed.

Kubernetes-side workload visibility, logs, secret references, resource settings, health checks, storage, and a successful rollout restart are validated in `kubernetes-deployment.md` and `../investigation/INCIDENT-002-RCA.md`.
