#!/usr/bin/env bash
set -u

output="${1:-evidence/linux-runtime.txt}"
mkdir -p "$(dirname "$output")"
{
  echo "MiniPay Linux runtime evidence"
  date -Is
  echo "## OS and kernel"
  uname -a
  cat /etc/os-release | sed -n '1,6p'
  echo "## CPU and memory"
  nproc
  free -h
  echo "## Disk capacity and repository directory sizes"
  df -h / /home
  du -xhd1 "$PWD" 2>/dev/null | sort -h
  echo "## Highest memory processes"
  ps -eo pid,comm,%cpu,%mem,rss --sort=-%mem | head -n 8
  echo "## Listening TCP ports"
  ss -lntp
  echo "## DNS and health"
  getent hosts github.com || true
  curl --fail --silent --show-error --max-time 5 http://127.0.0.1:8080/health || true
  echo
  MINIPAY_HEALTH_URL="${MINIPAY_HEALTH_URL:-http://127.0.0.1:8080/health}" bash evidence/health-check.sh || true
  echo "## Compose status and recent application logs"
  docker compose ps
  docker compose logs --tail=10 api db
  echo "## Kubernetes workload status"
  kubectl get pods,pvc -n minipay 2>&1 || true
} 2>&1 | tee "$output"

echo "Saved evidence to $output"
