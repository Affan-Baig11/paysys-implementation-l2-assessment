# Linux environment evidence

Initial environment capture: 2026-10-28, Ubuntu 26.04.1 LTS under WSL 2.

## Initial OS, resource, and connectivity observations

- `uname -a` and `/etc/os-release`: Ubuntu 26.04.1 LTS; Linux kernel `6.18.54.1-microsoft-standard-WSL2`; x86_64.
- `nproc`: 8 logical CPUs.
- `free -h`: 7.6 GiB total memory, 6.9 GiB available, 2.0 GiB swap.
- `df -h`: Linux root filesystem 1007 GiB total, 1.3 GiB used, 955 GiB available. WSL also exposes a small tools mount at 100%; it is separate from the Linux root filesystem.
- Initial `ss -tulpn`: DNS resolver sockets were listening; MiniPay was not running at the time of that initial capture.
- `getent hosts github.com`: resolved to `20.207.73.82`.
- `curl -I --max-time 10 https://github.com`: HTTP 200. Full raw headers were not retained because response headers can include session-cookie data.

## Current runtime capture

After services are running, capture process memory, per-directory disk usage, listening ports, application logs, health, and Kubernetes pod/PVC status with:

```bash
bash evidence/capture-linux.sh
```

The script saves output to `evidence/linux-runtime.txt`. Review the capture for secrets before committing. For a Kind health check, keep the Kubernetes port-forward active and run:

```bash
MINIPAY_HEALTH_URL=http://127.0.0.1:8081/health bash evidence/health-check.sh
```

## L2 investigation approach

- High CPU: identify the process with `ps`/`top`, correlate with application logs and request load, then check for repeated work or expensive queries.
- Low disk: check `df -h`, find large directories with `du`, and clean only known disposable artifacts after confirming they are not database data.
- Unreachable API: verify DNS, listening ports, container/pod readiness, Service endpoints, health checks, and recent logs in that order.
- Repeated process termination: inspect pod/container restart counts, events, resource limits, and previous container logs; fix the underlying cause before restarting repeatedly.

The runtime capture in `evidence/linux-runtime.txt` records a fresh health check, process/memory snapshot, directory sizes, listening ports, recent logs, and the healthy Kind pods/PVC. The original console output was reviewed and summarized with machine/user identifiers omitted.
