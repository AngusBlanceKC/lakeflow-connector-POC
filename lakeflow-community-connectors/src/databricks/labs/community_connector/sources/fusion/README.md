# Fusion (Circdata) Lakeflow connector

Reads attendee data from the private Fusion event platform, formerly known as
Circdata. The public integration contract identifies the `People` and
`VisitorIntegrationApi/api/EventTicket` streams.

## Connection parameters

- `base_url`: Fusion API base URL supplied by Fusion.
- `event_id`: Fusion event identifier.
- `username`: Fusion integration username.
- `password`: Fusion integration password.
- `install_name`: Fusion installation name.
- `api_key`: API key supplied by Fusion.

The exact private API authentication placement and pagination contract must be
confirmed with customer credentials in record mode. The implementation uses
Basic auth plus `X-Fusion-Install-Name` and `X-Fusion-API-Key` headers, matching
the local simulator.

## Tables

| Table | Description | Ingestion |
|---|---|---|
| `people` | Fusion people/attendee records | snapshot |
| `event_tickets` | Event registration/ticket records | snapshot |

The public Fusion integration documentation says deletions are not captured
and incremental synchronization is limited. Run `/validate-connector fusion`
with a real Fusion account before treating this connector as production-ready.

## Local simulator

The matching FastAPI simulator is in
[`fake-apis/fusion-circdata`](../../../../../../fake-apis/fusion-circdata/README.md).
It persists JSON state, uses bounded Faker generation, and exposes the same
logical credentials and two read streams for local testing.
