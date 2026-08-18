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

The bundle uses the shared `cloudflare_url` variable and routes Visit Create
through `/visit-create/create/v2`. If the Quick Tunnel is restarted, pass its
new URL at deploy time:

```bash
databricks bundle deploy -t dev --profile DEFAULT \
  --var="cloudflare_url=https://YOUR-TUNNEL.trycloudflare.com" \
  --var="api_key=demo-api-key"
```

The pipeline uses serverless compute. Quick Tunnel URLs are temporary. Keep both the FastAPI process and
`./fake-apis/cloudflare/run_quick_tunnels.sh` running while the pipeline
starts and reads data.
