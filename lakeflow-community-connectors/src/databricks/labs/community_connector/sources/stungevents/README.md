# StungEvents Community Connector

This connector reads public upcoming events from the free StungEvents REST API.

## Tables

| Table | Ingestion | Deletes |
|---|---|---|
| `events` | Snapshot | Not exposed by the public API |

## Configuration

No credentials are required. Optional table options are:

- `city`
- `country`
- `category`
- `from_date`
- `to_date`
- `limit` (default 100, maximum 100)

The source API and its limits are documented at <https://docs.stungevents.com/>.
