# Fake APIs

This directory contains small FastAPI services that simulate real-world APIs
for local connector development and end-to-end Lakeflow testing.

The reusable simulator checklist is in
[`develop-connector/references/fake-api-contract.md`](../develop-connector/references/fake-api-contract.md).
It covers persistence, deterministic seed data, bounded Faker generation,
authentication, permissions, pagination/cursors, deletes, webhooks, rate
limits, resilience, and test/documentation expectations.

## Available APIs

- [`visit-create-v2`](visit-create-v2/README.md) — a Visit Create v2 simulator
  with authentication, request limits, pagination, and resource endpoints.
- [`fusion-circdata`](fusion-circdata/README.md) — a Fusion/Circdata simulator
  for the private People and EventTicket integration streams.
- [`gevme`](gevme/README.md) — a GEVME Registration API v2 simulator for
  OAuth-protected event attendees.
- [`fairverify-ticketdata-v2`](fairverify-ticketdata-v2/README.md) — an
  inferred FairVerify Ticketdata v2 simulator for event tickets and scans.
- [`showoff-asp-v1-4`](showoff-asp-v1-4/README.md) — an ASP ShowOff API v1.4
  simulator with Basic-to-Bearer authentication and paginated resources.
- [`livebuzz`](livebuzz/README.md) — a LiveBuzz event API simulator for
  exhibitors, speakers, sessions, and attendees.
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
