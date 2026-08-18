# Lakeflow Connector POC

Proof-of-concept work for evaluating and developing Lakeflow community connectors.

The upstream Lakeflow community connectors repository is included under [`lakeflow-community-connectors/`](./lakeflow-community-connectors/).

## Where the relevant code lives

For each source, start with the matching connector implementation under
[`lakeflow-community-connectors/src/databricks/labs/community_connector/sources/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/).
That folder contains the source client, schemas, connector specification,
API research, tests, and generated Lakeflow source code.

The local FastAPI simulator for each source is under [`fake-apis/`](./fake-apis/).
These services provide the local API behaviour used for connector development,
including authentication, pagination, request limits, persistent test data,
and incremental-read scenarios. The connector and simulator directories are:

- Visit Create v2.0 — [`sources/visit_create_v2/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/visit_create_v2/) and [`fake-apis/visit-create-v2/`](./fake-apis/visit-create-v2/)
- Fusion (Circdata) — [`sources/fusion/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/fusion/) and [`fake-apis/fusion-circdata/`](./fake-apis/fusion-circdata/)
- GEVME — [`sources/gevme/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/gevme/) and [`fake-apis/gevme/`](./fake-apis/gevme/)
- FairVerify Ticketdata v2 — [`sources/fairverify_ticketdata_v2/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/fairverify_ticketdata_v2/) and [`fake-apis/fairverify-ticketdata-v2/`](./fake-apis/fairverify-ticketdata-v2/)
- ShowOff ASP v1.4 — [`sources/showoff_asp_v1_4/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/showoff_asp_v1_4/) and [`fake-apis/showoff-asp-v1-4/`](./fake-apis/showoff-asp-v1-4/)
- LiveBuzz — [`sources/livebuzz/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/livebuzz/) and [`fake-apis/livebuzz/`](./fake-apis/livebuzz/)

Databricks bundle definitions and pipeline resources are under
[`deployment/`](./deployment/), with one DAB directory per connector.

## Fake APIs

Local FastAPI services used to simulate upstream APIs for connector development
live under [`fake-apis/`](./fake-apis/). The Visit Create v2 simulator includes
authentication, CRUD resources, revision-based reads, webhooks, permissions,
event scoping, and configurable request limits. See its [README](./fake-apis/visit-create-v2/README.md).

## POC connector

The current proof-of-concept connectors include Visit Create v2, Fusion
(Circdata), GEVME, FairVerify Ticketdata v2, ShowOff ASP v1.4, and LiveBuzz. Their source, schemas, generated Lakeflow sources, and API
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

The LiveBuzz source and simulator are under
[`lakeflow-community-connectors/src/databricks/labs/community_connector/sources/livebuzz/`](./lakeflow-community-connectors/src/databricks/labs/community_connector/sources/livebuzz/)
and [`fake-apis/livebuzz/`](./fake-apis/livebuzz/).

## Databricks resource naming

All DAB-created pipelines and connectivity jobs use the `LC-POC |` prefix so
they can be filtered together in Databricks. Each connector has `main`,
`smoke`, and `probe` resources, for example `LC-POC | LiveBuzz | main`.
