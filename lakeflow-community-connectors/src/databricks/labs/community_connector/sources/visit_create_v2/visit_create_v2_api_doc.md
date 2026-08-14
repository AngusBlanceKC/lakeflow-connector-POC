# Visit Create JSON API v2

## Authentication

Every API request uses HTTP Basic Authentication. Visit uses the API key as the
username; the password is blank. The connector stores the key in the `api_key`
connection parameter and never places it in a URL or table option.

```bash
curl -u demo-api-key: \
  http://127.0.0.1:8000/create/v2/expos
```

## Resources

The API root is `/create/v2`. `expos` is unscoped; other resources are read
under `/create/v2/{resource}/{expo_id}`. The connector exposes the resource as
a Lakeflow table with the same name. A page is a JSON array and supports
`limit` (maximum 100) and `fromRevision`.

## Incremental reads

The connector starts at revision `0`, reads pages until a short page is
returned, and stores one greater than the highest revision as its Lakeflow
offset because `fromRevision` is inclusive.
Visitor and partner soft deletes are included by default so downstream delete
handling can observe tombstones.

## Retry behavior

HTTP `429`, `500`, `502`, `503`, and `504` responses are retried up to four
times. Numeric `Retry-After` values are honored, with exponential backoff for
other transient failures. Requests have a 30-second timeout.

## Reference

The implementation follows the [Visit Create API knowledgebase](https://help.visitcloud.com/create/docs/user-guide/organisation/api/), the
[Visit JSON API overview](https://help.visitcloud.com/wp-content/uploads/2022/09/Create-Visits-API.pdf), and the
[JSON API v2 documentation](https://api.visitcloud.com/create/docs).
