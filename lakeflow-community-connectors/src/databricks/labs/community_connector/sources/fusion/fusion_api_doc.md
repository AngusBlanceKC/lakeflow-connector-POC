# Fusion (Circdata) API research

## Research status

Fusion, formerly Circdata, exposes a private customer API. Public product and
integration documentation identifies the API family and fields but does not
publish a complete OpenAPI specification or stable public base URL. The
simulator and connector therefore keep the documented paths configurable and
mark transport details that require customer credentials as `TBD`.

## Sources

| Source | What it confirms | Confidence |
|---|---|---|
| [Swapcard Fusion integration](https://help.swapcard.com/en/articles/10202057-setting-up-a-fusion-integration-in-your-event) | Event ID, username, password, install name, API key; `EventTicket` visits stream; People fields; full refresh; no deletion capture; private API | High |
| [Fusion Event Management](https://www.fusion-events.co.uk/) | Fusion is the current product name for the former Circdata platform and provides event registration/attendee management | High |
| [Fusion Visit brochure](https://evessio.s3.amazonaws.com/customer/f5df061f-e5b4-40b1-8fc5-f7065cfc4e0b/event/49636f0e-58a9-4070-8c93-3794d90efc5b/media/media/31495a38-profile_CIRCDATA_VISIT_BROCHURE_2021.pdf) | Central event data and attendee/event-app concepts | Medium |

## Authentication

The documented integration requires:

- Event ID
- Username
- Password
- Install name
- API key supplied by Fusion

`TBD`: the exact header/query/body placement and whether the API uses Basic
authentication, an API-key header, or both. The simulator accepts the same
five logical values using configurable headers so connector behavior can be
tested without claiming an undocumented wire format.

## Base URL and resources

The public integration documentation links the private developer portal at
`developers.gofusion.com`. Configure `base_url` rather than hard-coding a
tenant hostname.

| Table | Path | Scope | Ingestion | Notes |
|---|---|---|---|---|
| `event_tickets` | `/VisitorIntegrationApi/api/EventTicket` | `event_id` | snapshot | Visits/attendee registrations; public integration docs identify this stream |
| `people` | `/People` | `event_id` | snapshot | Person records and custom fields; `Id` is the documented relationship key |

The source documentation does not publish pagination, ordering, rate limits,
or a change cursor. The implementation uses configurable page/offset
parameters for the simulator and defaults to snapshot metadata until live
record-mode testing confirms otherwise.

## People fields confirmed publicly

The Fusion integration documents these fields as strings:

`TITLE`, `FORENAME`, `SURNAME`, `EMAIL`, `TEL`, `MOBILE`, `FAX`, `COMPANY`,
`JOBTITLE`, `ADDR1`, `ADDR2`, `ADDR3`, `TOWN`, `COUNTY`, `POSTCODE`, `COUNTRY`,
`STATUS`, `BADGETYPE`, `CURRENCY`, `ATTENDED`, `BADGEID`.

`Id` is used to link People records. Additional fields are preserved by the
simulator as nullable fields only when discovered from a live response.

## Event ticket schema

`TBD`: the public documentation names the stream but does not expose a complete
schema. The simulator uses a conservative representative shape: `Id`,
`PersonId`, `EventId`, `TicketType`, `Status`, `RegisteredAt`, `UpdatedAt`, and
`CustomFields`. Live record mode must replace or extend this schema from actual
responses before production use.

## Pagination, deletes, and limits

- Full refresh is confirmed by the public integration documentation.
- Deletions are not captured by the documented integration.
- Incremental synchronization is limited by the provider and reportedly runs
  no more frequently than hourly in the public integration.
- Exact page parameters, maximum page size, rate-limit headers, retry policy,
  and response error schema are `TBD` pending private API access.

The connector therefore implements bounded requests, response validation, and
snapshot reads while keeping `page_size` and `page_offset` external options so
record-mode testing can adapt to the real service.

## Research log

Research performed 2026-08-14 UTC. Public pages were cross-checked; the private
developer portal could not be fetched without customer access. Do not promote
the inferred simulator transport to an official API claim.
