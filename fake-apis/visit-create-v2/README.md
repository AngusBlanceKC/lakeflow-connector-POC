# Visit Create v2.0 simulator

A local FastAPI simulator for the documented Visit Create JSON API v2. It is
intended for connector development and demos, not production use.

## Current public API

- Cloudflare base URL: `https://<cloudflareURL>/visit-create`
- Health check: `https://<cloudflareURL>/visit-create/health`
- API base URL: `https://<cloudflareURL>/visit-create/create/v2`

```bash
export CLOUDFLARE_URL="$(rg -o 'https://[[:alnum:]-]+\.trycloudflare\.com' "${TMPDIR:-/tmp}/fake-api-cloudflare-logs"/*.tunnel.log | tail -1)"
curl -u demo-api-key: "${CLOUDFLARE_URL}/visit-create/create/v2/expos"
```

This is a temporary Cloudflare Quick Tunnel and works only while the local
simulator, gateway, and `cloudflared` processes are running.

Implemented behavior:

- Basic Authentication: API key is the username; password is ignored.
- API root: `/create/v2/`.
- Event-scoped resources and the unscoped `expos` endpoint.
- Core setup and event resources including orders, questions, registration types/forms, activities, touchpoints, contents, licenses, actions, connections, visitors, and partners.
- `limit` and `fromRevision` pagination.
- Revision-ordered records with monotonically increasing revisions.
- Soft deletes for `visitors` and `partners`, controlled by `showDeleted`.
- CRUD for the documented writable resources, including activities in current v2 behavior.
- Webhook CRUD and webhook-style `webhookId` filtering.
- Configurable API-key expiry, allowed client IPs, enabled expos, and read/write resource permissions.
- Deterministic per-client rate limiting with `429`, `Retry-After`, and `X-RateLimit-*` headers.
- Deterministic seed data for repeatable connector tests.
- JSON persistence for records and webhooks, with atomic writes after mutations.
- Low-volume Faker visitor generation in the background (one visitor every 30 seconds by default, capped at 500 generated visitors).

## Run locally

```bash
cd fake-apis/visit-create-v2
python -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app:app --reload --port 8000
```

The default API key is `demo-api-key`. Try:

```bash
curl -u demo-api-key: http://localhost:8000/create/v2/expos
curl -u demo-api-key: \
  'http://localhost:8000/create/v2/visitors/0rwwipz7fufs1?limit=2&fromRevision=1'
```

The connector base URL should be:
`http://localhost:8000/create/v2`.

## Simulator configuration

All settings are optional environment variables:

| Variable | Default | Purpose |
| --- | --- | --- |
| `VISIT_API_KEY` | `demo-api-key` | Basic-auth username/API key |
| `VISIT_RATE_LIMIT` | `60` | Requests per client per window |
| `VISIT_RATE_WINDOW_SECONDS` | `60` | Rate-limit window |
| `VISIT_ALLOWED_IPS` | unrestricted | Comma-separated client IP allow-list |
| `VISIT_ALLOWED_EXPOS` | demo expo | Comma-separated enabled expo IDs; use `*` for organisation scope |
| `VISIT_API_READ_RESOURCES` | `*` | Read permission resource list |
| `VISIT_API_WRITE_RESOURCES` | `*` | Write permission resource list |
| `VISIT_API_EXPIRES_AT` | unset | API-key expiry as Unix timestamp |
| `VISIT_DATA_FILE` | `data/visit-create-v2.json` | Persistent JSON state file |
| `VISIT_GENERATE_INTERVAL_SECONDS` | `30` | Seconds between Faker generation ticks; set `0` to disable |
| `VISIT_GENERATE_PER_TICK` | `1` | Maximum new visitors per tick |
| `VISIT_MAX_GENERATED_VISITORS` | `500` | Lifetime cap on generated visitors |

The real service lets administrators configure API keys for events and CRUD
permissions. These controls are intentionally environment-driven here so a
connector test can reproduce both successful and denied calls without changing
the application code. The rate limit is a local test guardrail; the public
documentation does not publish a numeric limit.

The JSON file is created on first start and is safe to keep between runs. Delete
it when you want to reset to the original seed data. Generated records use IDs
starting with `generated-`, making them easy to identify in tests.

Databricks cannot reach a service running on your laptop's `localhost`; for a
remote POC, run this FastAPI app on an accessible host or use a secure tunnel.

References: [Visit Create API knowledgebase](https://help.visitcloud.com/create/docs/user-guide/organisation/api/), [Visit Create JSON API overview](https://help.visitcloud.com/wp-content/uploads/2022/09/Create-Visits-API.pdf), and [Visit Create JSON API v2 documentation](https://api.visitcloud.com/create/docs).
