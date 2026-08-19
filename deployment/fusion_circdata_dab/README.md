# Fusion (Circdata) Databricks deployment

This DAB deploys the Fusion Lakeflow connector.
The public Fusion integration API is private, so the defaults target the local
simulator. For Databricks, replace `base_url` with a Cloudflare tunnel URL and
keep the tunnel running.

Current Cloudflare URL: `https://<cloudflareURL>`

Set it before deployment:

```bash
export CLOUDFLARE_URL="$(rg -o 'https://[[:alnum:]-]+\.trycloudflare\.com' "${TMPDIR:-/tmp}/fake-api-cloudflare-logs"/*.tunnel.log | tail -1)"
databricks bundle deploy -t dev --var="cloudflare_url=${CLOUDFLARE_URL}" --profile DEFAULT
```

From this directory:

```bash
databricks bundle validate -t dev --profile DEFAULT
databricks bundle deploy -t dev --profile DEFAULT
databricks bundle run fusion_pipeline -t dev --profile DEFAULT
```

The deployed outputs are `fusion_people` and `fusion_event_tickets` in the
configured catalog/schema.

For a local simulator, start `fake-apis/fusion-circdata` and use a Quick Tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

The Fusion credentials are represented by the simulator's event ID, username,
password, install name, and API key. Do not commit real values.
