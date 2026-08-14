# Lakeflow Connector POC

Proof-of-concept work for evaluating and developing Lakeflow community connectors.

The upstream Lakeflow community connectors repository is included under [`lakeflow-community-connectors/`](./lakeflow-community-connectors/).

## Fake APIs

Local FastAPI services used to simulate upstream APIs for connector development
live under [`fake-apis/`](./fake-apis/). The Visit Create v2 simulator includes
authentication, CRUD resources, revision-based reads, webhooks, permissions,
event scoping, and configurable request limits. See its [README](./fake-apis/visit-create-v2/README.md).

## POC connector

The current proof-of-concept connectors include Visit Create v2 and Fusion
(Circdata). Their source, schemas, generated Lakeflow sources, and API
documentation are under
[`lakeflow-community-connectors/src/databricks/labs/community_connector/sources/visit_create_v2/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/visit_create_v2/).

The Fusion/Circdata source is under
[`lakeflow-community-connectors/src/databricks/labs/community_connector/sources/fusion/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/fusion/).
