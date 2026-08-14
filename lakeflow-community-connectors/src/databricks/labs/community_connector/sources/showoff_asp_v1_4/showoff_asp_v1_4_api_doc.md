# ShowOff ASP API v1.4 research

## Authentication

The official v1.4 documentation requires an API key and secret. `POST
/public/token` uses HTTP Basic Auth and returns a time-limited token. Resource
requests use `Authorization: Bearer <token>`; the `Authentication-Info` header
reports expiry. Basic-auth resource calls are supported but have more
restrictive rate limits.

## Pagination and limits

Collection resources use `O` (offset), `L` (limit), and `S` (sort). Responses
include RFC 5988 `Link`, `X-Records-Total`, `X-Records-Filtered`, and
`X-Records-Page` headers. HTTP 429 responses include `Retry-After`.

## Core resources

The v1.4 reference documents Addresses, Exhibitors, Forms/FormSubmissions,
Libraries, Products, Seminars/Sessions, Sites, Site Speakers, Speakers, Stands,
Visitor Groups, and Visitors. This connector implements the core collection
reads for visitors, exhibitors, seminars, sessions, speakers, sites, and
products. Webhook subscriptions and write operations are documented separately
and are not included in this READ connector.

Reference: https://api.showoff.asp.events/public/
