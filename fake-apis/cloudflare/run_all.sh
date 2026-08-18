#!/usr/bin/env bash
set -euo pipefail

# Start every simulator on a distinct local port plus the shared gateway on
# port 8000. Run the Cloudflare tunnel separately.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
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
  echo "Starting ${dir} on http://127.0.0.1:${port}"
  (
    cd "${repo_root}/fake-apis/${dir}"
    uv run --project . uvicorn app:app --host 127.0.0.1 --port "${port}"
  ) &
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
) &
pids+=("$!")

echo "All fake APIs are starting. Press Ctrl-C to stop them."
wait
