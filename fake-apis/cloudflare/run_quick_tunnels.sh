#!/usr/bin/env bash
set -euo pipefail

# Domain-free development mode: one Cloudflare Quick Tunnel for the shared
# path gateway. The gateway routes each URL prefix to a local API.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
log_dir="${TMPDIR:-/tmp}/fake-api-cloudflare-logs"
mkdir -p "${log_dir}"
pids=()

cleanup() {
  trap - EXIT INT TERM
  for pid in "${pids[@]}"; do
    kill "$pid" 2>/dev/null || true
  done
}
trap cleanup EXIT INT TERM

start_api() {
  local dir="$1"
  local port="$2"
  (
    cd "${repo_root}/fake-apis/${dir}"
    uv run --project . uvicorn app:app --host 127.0.0.1 --port "${port}"
  ) >"${log_dir}/${dir}.api.log" 2>&1 &
  pids+=("$!")
}

start_tunnel() {
  local name="$1"
  local port="$2"
  cloudflared tunnel --url "http://127.0.0.1:${port}" \
    >"${log_dir}/${name}.tunnel.log" 2>&1 &
  pids+=("$!")
}

start_api visit-create-v2 8100
start_api fusion-circdata 8010
start_api gevme 8020
start_api fairverify-ticketdata-v2 8030
start_api showoff-asp-v1-4 8040
start_api livebuzz 8050

(
  cd "${repo_root}/fake-apis/cloudflare"
  uv run --with 'fastapi>=0.110,<1.0' --with 'httpx>=0.27,<1.0' \
    --with 'uvicorn[standard]>=0.29,<1.0' uvicorn gateway:app \
    --host 127.0.0.1 --port 8000
) >"${log_dir}/gateway.api.log" 2>&1 &
pids+=("$!")

sleep 2
start_tunnel gateway 8000

echo "Quick Tunnels are starting. URLs and logs are in ${log_dir}:"
echo "  rg 'https://.*trycloudflare.com' ${log_dir}"
echo "Press Ctrl-C to stop all APIs and tunnels."
wait
