# FairVerify Ticketdata v2 API research

FairVerify publicly describes event ticketing, visitor management, Entry/self-check-in,
visitor data, and API integrations. It states that tickets can be verified through
an API, but does not publish a public Ticketdata v2 reference.

The local contract uses `GET /api/v2/events/{event_id}/tickets`, `GET /api/v2/events`,
and a verification write smoke surface at `POST /api/v2/tickets/{ticket_id}/verify`.
Authentication accepts an API key header or bearer token locally. Production base URL,
authentication, response envelopes, pagination/cursors, tenant headers, rate limits,
deletes, and write semantics are TBD pending private documentation or record-mode access.

References:

- https://fairverify.de/ticketing/
- https://fairverify.de/ticketing-shop/
- https://fairverify.de/
