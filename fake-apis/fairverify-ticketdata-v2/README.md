# FairVerify Ticketdata v2 simulator

Persistent FastAPI simulator for an inferred FairVerify Ticketdata v2 integration.
FairVerify publicly describes event ticketing, visitor management, Entry ticket
verification, and API integrations, but does not publish the private Ticketdata v2
wire contract.

## Access and links

- API base URL: https://navy-affordable-devoted-gathered.trycloudflare.com/fairverify
- Health check: [FairVerify health](https://navy-affordable-devoted-gathered.trycloudflare.com/fairverify/health)
- Tickets endpoint: https://navy-affordable-devoted-gathered.trycloudflare.com/fairverify/api/v2/events/demo-event-001/tickets
- Event ID: `demo-event-001`
- API key: `demo-fairverify-api-key`
- Bearer token: `demo-fairverify-access-token`
- Required headers: `X-FairVerify-API-Key` or `Authorization: Bearer ...`

The Quick Tunnel URL only works while `cloudflared` is running. These credentials
are intentionally fake and local-only.

## Run locally

```bash
uv run --project . uvicorn app:app --host 127.0.0.1 --port 8030
curl http://127.0.0.1:8030/health
curl -H 'X-FairVerify-API-Key: demo-fairverify-api-key' \
  'http://127.0.0.1:8030/api/v2/events/demo-event-001/tickets?limit=10'
curl -X POST -H 'X-FairVerify-API-Key: demo-fairverify-api-key' \
  http://127.0.0.1:8030/api/v2/tickets/fv-ticket-00001/verify
```

## Persistence and Faker

State is stored in `data/fairverify-ticketdata-v2.json` using atomic replacement.
One Faker ticket is generated every 60 seconds while the service is running, up
to 250 generated tickets. Set the interval or per-tick count to `0` to disable.

```text
FAIRVERIFY_GENERATE_INTERVAL_SECONDS=60
FAIRVERIFY_GENERATE_PER_TICK=1
FAIRVERIFY_MAX_GENERATED_TICKETS=250
FAIRVERIFY_DATA_FILE=data/fairverify-ticketdata-v2.json
FAIRVERIFY_RATE_LIMIT=60
FAIRVERIFY_RATE_WINDOW_SECONDS=60
```

Reset data with:

```bash
curl -X POST -H 'X-FairVerify-API-Key: demo-fairverify-api-key' \
  http://127.0.0.1:8030/admin/reset
```

## Cloudflare Quick Tunnel

```bash
cloudflared tunnel --url http://127.0.0.1:8030
```

Use the generated HTTPS hostname as the DAB `base_url`. See
[`fake-apis/cloudflare/README.md`](../cloudflare/README.md).

## Public research and gaps

- [FairVerify Ticketing](https://fairverify.de/ticketing/)
- [FairVerify Ticketing shop](https://fairverify.de/ticketing-shop/)
- [FairVerify API integration overview](https://fairverify.de/)

Public pages confirm API integrations and ticket verification but do not expose
Ticketdata v2 endpoint paths, authentication placement, response fields,
pagination, deletion semantics, or rate limits. Treat the local contract as an
assumption until FairVerify supplies private documentation or record-mode access.
