# LiveBuzz connector

Reads event content from the LiveBuzz JSON API: `exhibitors`, `speakers`,
`sessions`, and `attendees`.

Connection parameters are `base_url`, `campaign`, and the event API `api_key`.
The API may require Databricks egress IP allowlisting. `bearer` is retained as
an optional compatibility credential for older LiveBuzz integrations.

The simulator contract and research notes are in
`livebuzz_api_doc.md`; production endpoint details remain account-gated and
must be confirmed against the event's LiveBuzz API Documentation page.

Supported table options:

- `page_size`: request page size, default 100, maximum 100.
- `max_records_per_batch`: client admission-control cap, default 1000.
