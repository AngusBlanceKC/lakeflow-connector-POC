# Visit Create v2 DAB

This Databricks Asset Bundle deploys a Lakeflow Declarative Pipeline
that reads the local Visit Create v2 FastAPI simulator through the Cloudflare
Quick Tunnel.

Run these commands from this directory and use the `DEFAULT` Databricks CLI profile:

```bash
databricks bundle validate -t dev --profile DEFAULT
databricks bundle deploy -t dev --profile DEFAULT
databricks bundle run visit_create_v2_pipeline -t dev --profile DEFAULT
```

The bundle also includes a one-table connectivity diagnostic:

```bash
databricks bundle run visit_create_v2_smoke_pipeline -t dev --profile DEFAULT
```

The default `base_url` is the current temporary Quick Tunnel URL. If the tunnel
is restarted, pass its new URL at deploy time:

```bash
databricks bundle deploy -t dev --profile DEFAULT \
  --var="base_url=https://YOUR-TUNNEL.trycloudflare.com/create/v2" \
  --var="api_key=demo-api-key"
```

The current development target uses the existing `sh-iso` cluster because the
serverless update could not reach the temporary Cloudflare Quick Tunnel in this
workspace. Quick Tunnel URLs are temporary. Keep both the FastAPI process and
`cloudflared tunnel --url http://127.0.0.1:8000` running while the pipeline
starts and reads data.
