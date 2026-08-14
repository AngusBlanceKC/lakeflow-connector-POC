# Lakeflow Connector POC

Proof-of-concept work for evaluating and developing Lakeflow community connectors.

The upstream Lakeflow community connectors repository is included under [`lakeflow-community-connectors/`](./lakeflow-community-connectors/).

## Fake APIs

Local FastAPI services used to simulate upstream APIs for connector development
live under [`fake-apis/`](./fake-apis/). The Visit Create v2 simulator includes
authentication, CRUD resources, revision-based reads, webhooks, permissions,
event scoping, and configurable request limits. See its [README](./fake-apis/visit-create-v2/README.md).

## POC connectors

### StungEvents

The StungEvents connector is a proof of concept for ingesting events from the free, public StungEvents REST/JSON API. Reads do not require authentication. It exposes the API's `events` resource as a snapshot table and supports the documented city, country, category, date-range, limit, and offset filters.

- Connector: [`lakeflow-community-connectors/src/databricks/labs/community_connector/sources/stungevents/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/stungevents/)
- API documentation: [StungEvents API documentation](https://docs.stungevents.com/)

The public API does not document a reliable change cursor or delete feed, so this POC intentionally models the source as a snapshot rather than claiming incremental-delete support.
