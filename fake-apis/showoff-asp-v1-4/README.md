# ShowOff ASP API v1.4 simulator

Persistent FastAPI simulator for the official ShowOff API v1.4 contract.

## Access and links

- API base URL: `https://<cloudflareURL>/showoff`
- Health check: `https://<cloudflareURL>/showoff/health`
- Visitors endpoint: `https://<cloudflareURL>/showoff/public/visitors`

```bash
curl -H 'Authorization: Bearer demo-showoff-access-token' \
  "${CLOUDFLARE_URL}/showoff/public/visitors?O=0&L=10"
```
- API key: `demo-showoff-api-key`
- API secret: `demo-showoff-api-secret`
- Bearer token: `demo-showoff-access-token`
- Site UUID: `demo-site-001`

The Quick Tunnel URL only works while `cloudflared` is running. These credentials
are intentionally fake and local-only.

Here, `<cloudflareURL>` means the temporary hostname printed by Cloudflare,
without `https://` or the API route suffix. Set `CLOUDFLARE_URL` manually from
that terminal output before running the authenticated example.

## Run locally

```bash
uv run --project . uvicorn app:app --host 127.0.0.1 --port 8040
curl http://127.0.0.1:8040/health
curl -u demo-showoff-api-key:demo-showoff-api-secret -X POST http://127.0.0.1:8040/public/token
curl -H 'Authorization: Bearer demo-showoff-access-token' \
  'http://127.0.0.1:8040/public/visitors?O=0&L=10'
```

## Persistence and Faker

State is stored in `data/showoff-asp-v1-4.json` with atomic replacement. One
Faker visitor is generated every 60 seconds while running, up to 250 generated
visitors. Set the interval or per-tick count to `0` to disable generation.

```text
SHOWOFF_GENERATE_INTERVAL_SECONDS=60
SHOWOFF_GENERATE_PER_TICK=1
SHOWOFF_MAX_GENERATED_VISITORS=250
SHOWOFF_DATA_FILE=data/showoff-asp-v1-4.json
SHOWOFF_RATE_LIMIT=60
SHOWOFF_RATE_WINDOW_SECONDS=60
```

## Cloudflare

```bash
cloudflared tunnel --url http://127.0.0.1:8040
```

Use the generated HTTPS hostname as the DAB `base_url`. See
[`fake-apis/cloudflare/README.md`](../cloudflare/README.md).

## Research

- [Official ShowOff v1.4 API documentation](https://api.showoff.asp.events/public/)
- [ASP API documentation announcement](https://support.asp.events/hc/en-us/articles/33386716905373-Where-can-I-find-your-API-documentation)

The simulator implements the documented token flow, Bearer resource calls,
pagination headers, rate-limit shape, and core resources. It intentionally uses
synthetic records and local credentials.
