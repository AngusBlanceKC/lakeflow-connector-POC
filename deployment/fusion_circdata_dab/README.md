# Fusion (Circdata) Databricks deployment

This DAB deploys the Fusion Lakeflow connector and a small connectivity probe.
The public Fusion integration API is private, so the defaults target the local
simulator. For Databricks, replace `base_url` with a Cloudflare tunnel URL and
keep the tunnel running.

From this directory:

```bash
databricks bundle validate -t dev --profile DEFAULT
databricks bundle deploy -t dev --profile DEFAULT
databricks bundle run fusion_connectivity_probe -t dev --profile DEFAULT
databricks bundle run fusion_smoke_pipeline -t dev --profile DEFAULT
databricks bundle run fusion_pipeline -t dev --profile DEFAULT
```

The deployed outputs are `fusion_people` and `fusion_event_tickets` in the
configured catalog/schema. The probe checks DNS, TLS, `/health`, and the
authenticated People endpoint from Databricks itself before Lakeflow runs.

For a local simulator, start `fake-apis/fusion-circdata` and use a Quick Tunnel:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

The Fusion credentials are represented by the simulator's event ID, username,
password, install name, and API key. Do not commit real values.
