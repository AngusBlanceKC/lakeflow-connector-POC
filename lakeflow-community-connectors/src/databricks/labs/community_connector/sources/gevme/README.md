# GEVME Registration Lakeflow connector

Reads event attendees from GEVME Registration API v2.

## Local links and credentials

The matching simulator is [fake-apis/gevme](../../../../../../fake-apis/gevme/README.md).
Its README contains the current API link, Databricks pipeline link, demo OAuth
credentials, and Cloudflare instructions. The simulator defaults are:

- event ID: `demo-event-001`
- access token: `demo-access-token`
- client ID: `demo-client-id`
- client secret: `demo-client-secret`

These are intentionally fake local-development values only.

## Tables

| Table | Description | Ingestion |
|---|---|---|
| `attendees` | Event attendee/registration records | snapshot |

The public API documentation does not publish a complete attendee response
schema or production cursor contract. Run record-mode validation with GEVME
credentials before treating this connector as production-ready.
