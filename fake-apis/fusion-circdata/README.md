# Fusion (Circdata) API simulator

This FastAPI service simulates the private Fusion API formerly known as
Circdata. Public integration documentation identifies the `People` and
`VisitorIntegrationApi/api/EventTicket` streams and requires an event ID,
username, password, install name, and API key.

## Current public API

- Cloudflare base URL: `https://<cloudflareURL>/fusion`
- Health check: `https://<cloudflareURL>/fusion/health`
- People endpoint: `https://<cloudflareURL>/fusion/People`
- Event tickets endpoint: `https://<cloudflareURL>/fusion/VisitorIntegrationApi/api/EventTicket`

```bash
export CLOUDFLARE_URL="$(rg -o 'https://[[:alnum:]-]+\.trycloudflare\.com' "${TMPDIR:-/tmp}/fake-api-cloudflare-logs"/*.tunnel.log | tail -1)"
curl -u demo-user:demo-password \
  -H 'X-Fusion-Install-Name: demo-install' \
  -H 'X-Fusion-API-Key: demo-api-key' \
  "${CLOUDFLARE_URL}/fusion/People?eventId=demo-event-001&limit=2"
```

This is a temporary Cloudflare Quick Tunnel and works only while the local
simulator, gateway, and `cloudflared` processes are running.

Here, `<cloudflareURL>` means the temporary hostname printed by Cloudflare,
without `https://` or the API route suffix. Get it with:

```bash
export CLOUDFLARE_URL="$(rg -o 'https://[[:alnum:]-]+\.trycloudflare\.com' "${TMPDIR:-/tmp}/fake-api-cloudflare-logs"/*.tunnel.log | tail -1)"
```

## Start

```bash
cd fake-apis/fusion-circdata
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn app:app --host 127.0.0.1 --port 8010
```

Default test credentials:

```text
event_id=demo-event-001
username=demo-user
password=demo-password
install_name=demo-install
api_key=demo-api-key
```

Test it locally:

```bash
curl http://127.0.0.1:8010/health
curl -u demo-user:demo-password \
  -H 'X-Fusion-Install-Name: demo-install' \
  -H 'X-Fusion-API-Key: demo-api-key' \
  'http://127.0.0.1:8010/People?eventId=demo-event-001&limit=2'
```

## Behavior

- Persistent state: `data/fusion-circdata.json`, written atomically.
- Deterministic seed records for people and event tickets.
- Low-volume Faker generation: one person every 60 seconds by default, capped
  at 250 generated people.
- Configurable rate limiting, credentials, event, data file, and generator.
- Snapshot-style reads with `limit` and `offset`; public documentation does not
  confirm a cursor or delete feed.
- `/health` is unauthenticated; data endpoints require Basic auth plus install
  name and API key headers.

Delete the JSON file to reset seed data. Do not expose the default credentials
through a long-lived public tunnel.
