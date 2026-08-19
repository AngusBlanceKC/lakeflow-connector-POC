# GEVME Databricks bundle

This DAB deploys the GEVME Lakeflow connector as a serverless pipeline.

## Commands

Run from this directory:

```bash
databricks bundle validate -t dev --profile DEFAULT
databricks bundle deploy -t dev --var='cloudflare_url=https://navy-affordable-devoted-gathered.trycloudflare.com' --profile DEFAULT
```

The API simulator is [../../fake-apis/gevme/README.md](../../fake-apis/gevme/README.md),
which is the authoritative place for the current API URL, pipeline links, and
demo credentials. The Quick Tunnel must remain running throughout a pipeline
update.

## Outputs

The pipeline writes `raw_angus.default.gevme_attendees`. Pipeline links should
be added to the simulator README after deployment.
