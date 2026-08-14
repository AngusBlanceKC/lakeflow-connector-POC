# Lakeflow Connector POC

Proof-of-concept work for evaluating and developing Lakeflow community connectors.

The upstream Lakeflow community connectors repository is included under [`lakeflow-community-connectors/`](./lakeflow-community-connectors/).

## Fake APIs

Local FastAPI services used to simulate upstream APIs for connector development
live under [`fake-apis/`](./fake-apis/). The Visit Create v2 simulator includes
authentication, CRUD resources, revision-based reads, webhooks, permissions,
event scoping, and configurable request limits. See its [README](./fake-apis/visit-create-v2/README.md).

## POC connector

The current proof-of-concept connectors include Visit Create v2, Fusion
(Circdata), GEVME, FairVerify Ticketdata v2, and ShowOff ASP v1.4. Their source, schemas, generated Lakeflow sources, and API
documentation are under
[`lakeflow-community-connectors/src/databricks/labs/community_connector/sources/visit_create_v2/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/visit_create_v2/).

The Fusion/Circdata source is under
[`lakeflow-community-connectors/src/databricks/labs/community_connector/sources/fusion/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/fusion/).

The GEVME source and simulator are under
[`lakeflow-community-connectors/src/databricks/labs/community_connector/sources/gevme/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/gevme/)
and [`fake-apis/gevme/`](./fake-apis/gevme/).

The FairVerify Ticketdata v2 source and simulator are under
[`lakeflow-community-connectors/src/databricks/labs/community_connector/sources/fairverify_ticketdata_v2/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/fairverify_ticketdata_v2/)
and [`fake-apis/fairverify-ticketdata-v2/`](./fake-apis/fairverify-ticketdata-v2/).

The ShowOff ASP v1.4 source and simulator are under
[`lakeflow-community-connectors/src/databricks/labs/community_connector/sources/showoff_asp_v1_4/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/showoff_asp_v1_4/)
and [`fake-apis/showoff-asp-v1-4/`](./fake-apis/showoff-asp-v1-4/).
