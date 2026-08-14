# Visit Create v2 Community Connector

This connector reads the Visit Create JSON API v2, including revision-based
incremental reads and the event-scoped resources exposed by the local simulator
in [`fake-apis/visit-create-v2/`](../../../../../../../../fake-apis/visit-create-v2/).

## Configuration

Create a Unity Catalog connection with:

- `api_key`: Visit API key; the connector sends it as the Basic Auth username.
- `expo_id`: Event/expo identifier, defaulting to the simulator's demo expo when
  used directly from Python.
- `base_url`: API root, for example `http://127.0.0.1:8000/create/v2` for the
  local simulator.

Supported table options are `limit`, `from_revision`, `show_deleted`,
`webhook_id`, `contact_reference`, `contact_id`, and `registration_states`.

## Tables

`expos`, `visitors`, `partners`, `participants`, `contents`, `licenses`,
`payments`, `actions`, `connections`, `activities`, `touchpoints`, `orders`,
`questions`, `registrationTypes`, `registrationForms`, and `webhooks`.

All event resources use `revision` as the incremental cursor. Visitor and
partner deletes are retained as tombstones when `show_deleted=true`. Webhooks
are treated as a snapshot because their API representation does not expose the
same record revision field.

## Local test

Start the simulator, then configure the connector with the values below:

```text
base_url = http://127.0.0.1:8000/create/v2
api_key = demo-api-key
expo_id = 0rwwipz7fufs1
```
