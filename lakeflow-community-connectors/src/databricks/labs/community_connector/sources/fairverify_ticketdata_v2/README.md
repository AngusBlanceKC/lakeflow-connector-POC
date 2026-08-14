# FairVerify Ticketdata v2 Lakeflow connector

Reads event and ticket snapshots from the local FairVerify Ticketdata v2 simulator
contract. Public FairVerify pages confirm ticketing, visitor data, API integrations,
and ticket verification; the production wire contract remains private.

The paired simulator README contains current API/pipeline links and demo credentials:
[fake-apis/fairverify-ticketdata-v2](../../../../../../fake-apis/fairverify-ticketdata-v2/README.md).

| Table | Description | Ingestion |
|---|---|---|
| `tickets` | Event ticket and visitor records | snapshot |
| `events` | Event metadata | snapshot |

Run live record-mode validation with FairVerify credentials before production use.
