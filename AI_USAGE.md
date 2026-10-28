# AI tool usage

## Tools used

- OpenAI Codex (ChatGPT) was used as an implementation and troubleshooting assistant.
- The candidate ran commands, reviewed outputs, and made environment-specific decisions in WSL, Docker Desktop, Kind, Rancher, and the browser.

## Representative interactions

1. Asked for a breakdown of the assessment, then used the requirement files as a checklist for the implementation.
2. Asked for help implementing the MiniPay API, operator UI, SQL reports, Kubernetes manifests, and incident investigations. Generated work was reviewed against the supplied requirements and exercised with actual requests and commands.
3. Asked for help diagnosing the Kubernetes starter manifest. Compared its image, probe port, Service selector/target port, namespace, and database assumptions with the deployed manifests and checked the resulting Kind workloads.
4. Asked for a Python L2 transaction diagnostic utility. Unit tests were run in WSL, followed by a live health check and lookup of a real Kind transaction.

## Validation and engineering ownership

- API suite: `python -m pytest -q tests/api` (7 passed in the final run, including the null-completion-time regression case).
- Python support tool suite: `python -m pytest -q tests/python` (8 passed).
- Combined API and Python run: 15 passed, with 8 Starlette/FastAPI deprecation warnings.
- Browser journeys: Playwright suite (3 passed).
- Kubernetes: checked node/workload/PVC readiness, API health, UI payment flow, and a Deployment restart/rollout.
- SQL: ran all seven reports and compared `EXPLAIN (ANALYZE, BUFFERS)` before and after adding a transaction reference index.
- The candidate ran the documented commands, reviewed their outputs and the project documentation, and should be prepared to explain and modify the AI-assisted implementation. Synthetic payments use a local mock; no real money moves.

## Corrections made to AI-assisted guidance

- An initial Rancher troubleshooting explanation confused the internal user ID printed by the reset command with the UI login name. After the login failed, we corrected the guidance: the UI login name is `admin`; the generated ID is an internal identifier. Credentials are intentionally not recorded here.
- The first support-tool check used the default Compose API address on port 8080, while the example transaction lived in the separate Kind database on port 8081. The not-found result exposed that environment mismatch; the tool was rerun with `MINIPAY_API_URL=http://127.0.0.1:8081` while the Kubernetes port-forward was active, and it returned the expected successful transaction report.
- Rancher registration was not represented as successful. The candidate verified browser/agent reachability failures and retained the limitation in the evidence rather than claiming Rancher managed the Kind workloads.
