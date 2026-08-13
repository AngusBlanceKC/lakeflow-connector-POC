# StungEvents API

## Source

StungEvents provides a public event-discovery REST API. Read endpoints return JSON and do not require an API key.

Official documentation: <https://docs.stungevents.com/>

## Authentication

No authentication is required for public read endpoints.

## Supported table

### `events`

`GET https://api.stungevents.com/events`

The endpoint returns an object containing an `events` array. Supported query parameters include:

- `city`
- `country`
- `category`
- `from`
- `to`
- `limit` (maximum 100)
- `offset`

The connector maps the table options `from_date` and `to_date` to the API's `from` and `to` parameters.

## Ingestion behavior

The public endpoint exposes upcoming events and offset pagination, but does not document a reliable update cursor or delete/tombstone feed. The connector therefore implements `events` as a snapshot table. A downstream refresh can be scheduled when current event data is required.

## Rate limits

The documentation states a limit of 1,000 unauthenticated requests per IP per day.
