# FairVerify Ticketdata v2 Databricks bundle

Deploys the inferred FairVerify Ticketdata v2 connector as a serverless
Lakeflow pipeline, a ticket smoke pipeline, and a Databricks-side connectivity
probe.

```bash
databricks bundle validate -t dev --profile DEFAULT
databricks bundle deploy -t dev --var='base_url=https://<quick-tunnel>.trycloudflare.com' --profile DEFAULT
```

The paired simulator README is [here](../../fake-apis/fairverify-ticketdata-v2/README.md)
and must be updated with the actual API and pipeline links after deployment.
