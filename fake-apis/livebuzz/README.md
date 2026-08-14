# LiveBuzz fake API

Persistent FastAPI simulator for the LiveBuzz event JSON API contract. It
models exhibitors, speakers, sessions, and registration attendees, with API
key/bearer authentication, campaign scoping, pagination, a 30-request/minute
default limit, and bounded Faker attendee generation.

## Run locally

```bash
cd fake-apis/livebuzz
uv run uvicorn app:app --host 127.0.0.1 --port 8050
curl http://127.0.0.1:8050/health
curl -H 'X-API-Key: demo-livebuzz-api-key' \
  'http://127.0.0.1:8050/campaign/demo-event-2026/api/exhibitors?limit=2&offset=0'
```

The persistent state is `data/livebuzz.json`. It is atomically replaced and
survives restarts. Delete that file and restart to reseed the deterministic
baseline records. The default Faker generator adds one attendee every 60
seconds, capped at 250 generated attendees. Set
`LIVEBUZZ_GENERATE_INTERVAL_SECONDS=0` to disable it.

## Configuration

| Variable | Default |
|---|---|
| `LIVEBUZZ_CAMPAIGN` | `demo-event-2026` |
| `LIVEBUZZ_API_KEY` | `demo-livebuzz-api-key` |
| `LIVEBUZZ_BEARER` | `demo-livebuzz-bearer` |
| `LIVEBUZZ_RATE_LIMIT` | `30` |
| `LIVEBUZZ_GENERATE_INTERVAL_SECONDS` | `60` |
| `LIVEBUZZ_GENERATE_PER_TICK` | `1` |
| `LIVEBUZZ_MAX_GENERATED_ATTENDEES` | `250` |
| `LIVEBUZZ_DATA_FILE` | `data/livebuzz.json` |

## Access and links

- Local API: `http://127.0.0.1:8050`
- Health check: [http://127.0.0.1:8050/health](http://127.0.0.1:8050/health)
- Databricks main pipeline: `<deploy-livebuzz-dab-and-add-link>`
- Databricks smoke pipeline: `<deploy-livebuzz-dab-and-add-link>`
- Demo API key: `demo-livebuzz-api-key`
- Demo bearer: `demo-livebuzz-bearer`
- Campaign: `demo-event-2026`
- Required header: `X-API-Key: demo-livebuzz-api-key`

Quick Tunnel URLs only work while `cloudflared` is running. See
[`fake-apis/cloudflare/README.md`](../cloudflare/README.md) for the free
`trycloudflare.com` setup.
