# LiveBuzz Databricks Asset Bundle

From this directory:

```bash
databricks bundle validate -t dev
databricks bundle deploy -t dev
```

The default API URL is local-only. Databricks cannot reach `127.0.0.1`; set
`cloudflare_url` to the active Cloudflare Quick Tunnel URL with `--var`, and
keep the tunnel process running. The bundle includes a full four-table
pipeline.
