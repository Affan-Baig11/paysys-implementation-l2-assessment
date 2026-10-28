#!/usr/bin/env bash
set -eu

health_url="${MINIPAY_HEALTH_URL:-http://127.0.0.1:8080/health}"
printf 'Checking MiniPay health at %s\n' "$health_url"
curl --fail --silent --show-error --max-time 5 "$health_url"
printf '\nHealth check passed.\n'
