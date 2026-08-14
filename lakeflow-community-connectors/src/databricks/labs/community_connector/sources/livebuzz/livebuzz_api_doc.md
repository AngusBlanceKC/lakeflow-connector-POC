# LiveBuzz API Documentation

## Authorization

The preferred authentication for this connector is the LiveBuzz API key sent
as `X-API-Key`. Public integration documentation confirms that credentials are
event-specific and that the API key is revealed in LiveControl's Account
Settings. LiveBuzz also supplies an event base URL and may require the caller's
IP address to be allowlisted. A bearer value is supported by older community
clients, but is not the primary connector method.

```http
GET https://<event-base-url>/campaign/<campaign>/api/exhibitors?limit=100&offset=0
X-API-Key: <api-key>
Accept: application/json
```

`TBD:` the account-gated API documentation at `control.buzz` must confirm the
exact production route and header spelling for a live account. The simulator
uses the route above and accepts `X-API-Key` or `Authorization: Bearer`.

## Object List

The documented LiveBuzz integration surface includes exhibitors, speakers,
seminars/sessions, and registration participants. This connector exposes the
stable first set as four tables: `exhibitors`, `speakers`, `sessions`, and
`attendees`. Resource discovery is not publicly documented, so the list is
static and can be extended after an authenticated API documentation export.

## Object Schema

`TBD:` LiveBuzz's schema endpoint is account-gated. The connector uses explicit
schemas based on the public integration field descriptions and the community
LiveBuzz client. The simulator returns JSON objects under a `data` array.

| Table | Fields |
|---|---|
| exhibitors | `id`, `identifier`, `companyName`, `logo`, `description`, `telephone`, `emailAddress`, `websiteUrl`, `stands`, `addresses`, `socialMediaChannels`, `status`, `updated_at` |
| speakers | `id`, `firstName`, `lastName`, `companyName`, `jobTitle`, `emailAddress`, `biography`, `updated_at` |
| sessions | `id`, `title`, `description`, `start`, `end`, `location`, `track`, `speaker_ids`, `updated_at` |
| attendees | `id`, `firstName`, `lastName`, `emailAddress`, `companyName`, `jobTitle`, `status`, `registered_at`, `updated_at` |

## Get Object Primary Keys

The public sources do not describe a primary-key endpoint. The connector uses
the stable `id` field for each table. `identifier` is retained for exhibitors
because the community client distinguishes the LiveBuzz exhibitor identifier
from its local database ID.

## Object's ingestion type

The source advertises real-time updates, but does not publicly document a
change-feed or delete endpoint. The connector treats all four tables as `cdc`
using `updated_at` as the cursor and `id` as the primary key. Deletes are not
currently represented. `TBD:` confirm whether a deleted/cancelled status or a
separate deletion feed is available in the account documentation.

## Read API for Data Retrieval

The connector performs `GET` requests against the event's API base URL. The
simulator and connector use:

```text
/campaign/{campaign}/api/{resource}?limit={limit}&offset={offset}&since={ISO-8601}
```

`limit` is capped at 100, `offset` is zero-based, and `since` is an exclusive
ISO-8601 `updated_at` filter. Responses are expected to be either an array or
an object with `data` and `meta.has_more` fields. The connector stops when the
page is empty or `has_more` is false and checkpoints the greatest
`updated_at` value returned.

`TBD:` exact production pagination parameter names, response envelope, cursor
semantics, and whether the production API supports `since` must be confirmed
from the account-gated documentation. The simulator deliberately implements
the contract used by this POC so connector behavior is testable.

LiveBuzz is documented by an integration partner as allowing 30 requests per
minute. The simulator defaults to the same limit and returns `429` with
`Retry-After`, `X-RateLimit-Limit`, and `X-RateLimit-Remaining` headers.

## Field Type Mapping

| API shape | Spark type | Notes |
|---|---|---|
| Identifier, name, status, URL, phone, email | string | Nullable unless required by the source |
| ISO-8601 timestamps | string | Kept as raw API values for source fidelity |
| `stands`, `speaker_ids` | array of strings | Relationships to event content |
| `addresses`, `socialMediaChannels` | array/object | Nested JSON retained without flattening |

## Known Gaps

Production access requires a LiveBuzz account, API key, event base URL, event
campaign, and IP allowlisting. No public source exposed the complete endpoint
schemas, deletion behavior, or exact pagination contract. Those details are
explicitly marked `TBD` instead of being presented as verified facts.

## Research Log

| Source Type | URL | Accessed (UTC) | Confidence | What it confirmed |
|---|---|---|---|---|
| Official LiveBuzz | https://www.livebuzz.co.uk/services/content-modules | 2026-08-14 | High | Exhibitors, products, sessions, speakers, and articles are LiveBuzz content modules |
| Official LiveBuzz | https://www.livebuzz.co.uk/services/registration | 2026-08-14 | High | Registration/event platform and attendee/exhibitor data context |
| Community integration guide | https://support.grip.events/integrations-with-livebuzz | 2026-08-14 | Medium | API key, event base URL, Account Settings/API Documentation location, IP allowlisting |
| Community integration guide | https://integrationadmin.rdmobile.com/Documentation/Home/DataConnectors/LiveBuzz | 2026-08-14 | Medium | 30 requests/minute, resource families, campaign documentation route, IP restriction |
| Community client | https://github.com/Burnthebook/craft3-livebuzz | 2026-08-14 | Medium | Exhibitor fields, bearer usage, JSON feed and campaign-specific configuration |
| Community client docs | https://docs.lineup.ninja/event/sources/livebuzz/ | 2026-08-14 | Medium | Environment/campaign identifiers and exhibitor status behavior |
