# Fake APIs

This directory contains small FastAPI services that simulate real-world APIs
for local connector development and end-to-end Lakeflow testing.

## Available APIs

- [`visit-create-v2`](visit-create-v2/README.md) — a Visit Create v2 simulator
  with authentication, request limits, pagination, and resource endpoints.
- [`cloudflare`](cloudflare/README.md) — notes and configuration examples for
  exposing a local fake API through a Cloudflare Quick Tunnel.

## Common workflow

1. Start the fake API locally with its project README.
2. Check `/health` before testing authenticated endpoints.
3. Use the documented API key or credentials for connector requests.
4. If Databricks needs to reach the API, expose the local port through a
   Cloudflare Tunnel and use the generated HTTPS URL as the connector base URL.

## Persistent generated data

Fake APIs may use Faker to add a small number of realistic records during
startup or on a low-frequency background interval. Generated records are kept
in each API's local JSON/CSV data file, so IDs and previously generated data
survive restarts. These files are intentionally local test state rather than
production data; reset them only when you want a fresh simulation.

Do not commit credentials, tunnel tokens, or private production data. The
Cloudflare Quick Tunnel URL is temporary and changes when the tunnel restarts.
