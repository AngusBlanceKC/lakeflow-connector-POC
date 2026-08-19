# GEVME API v2 simulator

Persistent FastAPI simulator for the GEVME Registration API v2. It models the
OAuth-protected attendee read API documented by GEVME, including event-scoped
attendee reads, filters, rate limits, persistent JSON state, and bounded Faker
generation.

## Access and links

- API base URL: `https://<cloudflareURL>/gevme`
- Health check: `https://<cloudflareURL>/gevme/health`
- Attendees endpoint: `https://<cloudflareURL>/gevme/apiv2/api/events/demo-event-001/attendees`

```bash
export CLOUDFLARE_URL="$(rg -o 'https://[[:alnum:]-]+\.trycloudflare\.com' "${TMPDIR:-/tmp}/fake-api-cloudflare-logs"/*.tunnel.log | tail -1)"
curl -H 'Authorization: Bearer demo-access-token' \
  "${CLOUDFLARE_URL}/gevme/apiv2/api/events/demo-event-001/attendees?limit=10"
```
- Event ID: `demo-event-001`
- OAuth client ID: `demo-client-id`
- OAuth client secret: `demo-client-secret`
- Demo access token: `demo-access-token`
- Required header: `Authorization: Bearer demo-access-token`

The Quick Tunnel URL only works while the `cloudflared` process is running.
These credentials are intentionally fake and local-only.

## Run locally

```bash
uv run --project . uvicorn app:app --host 127.0.0.1 --port 8020
```

```bash
curl http://127.0.0.1:8020/health
curl -H 'Authorization: Bearer demo-access-token' \
  'http://127.0.0.1:8020/apiv2/api/events/demo-event-001/attendees?limit=10'
```

The connector's base URL is the simulator root; it adds `/apiv2/api` to match
GEVME's documented API base.

## OAuth token simulation

```bash
curl -X POST http://127.0.0.1:8020/apiv2/api/oauth/access_token \
  -d grant_type=client_credentials \
  -d client_id=demo-client-id \
  -d client_secret=demo-client-secret \
  -d scope=root
```

GEVME's public integration guide documents authorization-code OAuth and the
same access-token endpoint. The client-credentials form above is a local test
convenience; validate the real grant and scopes with GEVME credentials.

## Persistence and Faker

State is retained in `data/gevme.json` using atomic replacement. By default one
new attendee is generated every 60 seconds while the service is running, up to
250 generated attendees. Configure with:

```text
GEVME_GENERATE_INTERVAL_SECONDS=60
GEVME_GENERATE_PER_TICK=1
GEVME_MAX_GENERATED_ATTENDEES=250
GEVME_DATA_FILE=data/gevme.json
GEVME_RATE_LIMIT=60
GEVME_RATE_WINDOW_SECONDS=60
```

Set the interval or per-tick count to `0` to disable generation. Reset local
data with `curl -X POST -u admin:reset-demo http://127.0.0.1:8020/admin/reset`.

## Cloudflare Quick Tunnel

With the API running, use a second terminal:

```bash
cloudflared tunnel --url http://127.0.0.1:8020
```

Use the resulting `https://<random>.trycloudflare.com` hostname in the DAB's
`base_url` variable. See [`fake-apis/cloudflare/README.md`](../cloudflare/README.md).

## Research references and known gaps

- [GEVME API v2 documentation](https://www.gevme.com/apiv2/docs)
- [GEVME Registration API integration guide](https://support-reg.gevme.com/support/solutions/articles/36000357144)

The public docs do not publish complete response schemas, cursor semantics,
tenant headers, or the production permission provisioning workflow. The
simulator uses stable JSON attendees and offset pagination for local testing;
the connector documents these as assumptions until record-mode access is
available.
