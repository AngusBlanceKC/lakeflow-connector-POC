# GEVME API v2 research

## Confirmed public contract

- API base: `https://www.gevme.com/apiv2/api`.
- OAuth 2.0 is the documented authorization mechanism.
- Access tokens are requested at `/oauth/access_token`.
- Attendee reads use `GET /events/{event_id}/attendees`.
- The endpoint requires the user and client to have `attendee_attendee`
  permission.
- Public docs list filters including `limit`, `orderBy`, `where[email]`,
  `modifiedFrom`, `modifiedTo`, `createdFrom`, and `createdTo`.
- Public integration guidance recommends at most 500 calls per minute and
  1,000 records per call.

## Connector assumptions

The public documentation does not publish a complete response schema or cursor
format. This connector assumes a JSON array (or `items`/`data` envelope),
offset pagination for local simulation, and a snapshot table because deletions
and CDC semantics are not described in the public READ contract.

The simulator accepts a bearer token and exposes a client-credentials shortcut
for local testing. The documented production flow is authorization code OAuth;
validate token acquisition, scopes, tenant/organisation routing, pagination,
and response fields with a real GEVME account before production use.

## References

- https://www.gevme.com/apiv2/docs
- https://support-reg.gevme.com/support/solutions/articles/36000357144
