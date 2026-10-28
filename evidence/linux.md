# Linux environment evidence

Initial environment capture: 2026-10-28, from Ubuntu 26.04.1 LTS running under WSL 2.

## Commands and results

- OS/kernel: uname -a and /etc/os-release
  - Ubuntu 26.04.1 LTS; Linux kernel 6.18.54.1-microsoft-standard-WSL2; x86_64.
- CPU: nproc
  - 8 logical CPUs.
- Memory: free -h
  - 7.6 GiB total; 6.9 GiB available; 2.0 GiB swap.
- Disk: df -h
  - Linux root filesystem: 1007 GiB total, 1.3 GiB used, 955 GiB available.
  - WSL also exposes a small tools mount at 100% usage; that is separate from the Linux root filesystem.
- Listening ports: ss -tulpn
  - DNS resolver sockets were listening on local resolver addresses. No MiniPay application was running at this initial capture.
- DNS: getent hosts github.com
  - Resolved to 20.207.73.82.
- Network: curl -I --max-time 10 https://github.com
  - GitHub returned HTTP 200.

The initial raw curl output was intentionally not retained because response headers can include session-cookie data. Process, per-directory disk, and application-log evidence will be added after those checks are collected and the services are running.
