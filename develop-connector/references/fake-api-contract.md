# Reusable fake API contract

This is the checklist for attributes that are broadly useful when simulating a
real upstream API. Implement only the capabilities supported by the source, but
make unsupported behavior explicit in the simulator README.

## Identity and configuration

- API title, version, base path, resource names, and a stable test tenant/event
  identifier.
- Environment-driven host/port, data-file path, credentials, tenant scope,
  enabled resources, and feature flags.
- Safe development defaults that work locally but never resemble production
  credentials.
- A documented reset procedure that removes or replaces persistent test state.

## Connectivity and observability

- Unauthenticated `/health` with a small deterministic JSON response.
- OpenAPI/docs endpoints where FastAPI provides them.
- Request logging suitable for debugging without logging passwords or API keys.
- Response headers that expose request IDs when the real API has them.
- A clear startup error for malformed persisted state or invalid configuration.

## Authentication and authorization

- The same authentication shape as the source: Basic, bearer, API key header,
  OAuth-like token, or another documented scheme.
- Valid, invalid, missing, and expired credential behavior.
- Tenant/event/resource permission checks where the source has scopes.
- Optional client-IP restrictions only when useful for testing.
- No secrets committed in source, fixtures, logs, or example curl commands.

## Data model and persistence

- Deterministic seed records covering every important field and data type.
- Stable IDs, timestamps, relationships, nullable fields, enums, and realistic
  nested objects.
- A persistent JSON/CSV/JSONL file under `data/` so records survive restarts.
- Atomic or replace-on-success writes to avoid corrupting the state file.
- Explicit state shape including revision/cursor, records, tombstones, and
  webhook/event queues as applicable.
- A bounded file size and generated-record cap for long-running local tests.

## Generated data

- Faker or equivalent realistic values, seeded when reproducibility matters.
- A low-frequency startup or background batch, controlled by environment
  variables such as interval and records-per-tick.
- A hard lifetime cap and a way to disable generation (`0` interval/count).
- Monotonically increasing cursor/revision values for generated records.
- Generated IDs that are recognizable and do not collide with seed records.
- Persistence after generation so a connector can observe new data on a later
  run without the generator overwhelming the developer's machine.

## Read behavior

- List and detail paths as documented, including parent-scoped child paths.
- Query filters with exact parameter names and types.
- Page size limits, ordering, inclusive/exclusive cursor semantics, and empty
  page behavior.
- Snapshot, append, CDC, or CDC-with-deletes behavior that matches the source.
- Soft deletes/tombstones and a `showDeleted`-style switch where relevant.
- Realistic 400, 401, 403, 404, 409, 429, and 5xx responses.

## Write and event behavior

- CRUD only for resources documented as writable.
- Request validation and realistic validation errors.
- Idempotency behavior and conflict responses when the source supports them.
- Webhook create/list/update/delete and event filtering when write-back testing
  needs it.
- A persisted event/webhook queue when the connector must read generated events.

## Limits and resilience

- Per-client or per-credential request limits with a deterministic window.
- `Retry-After`, limit, remaining, and reset headers when applicable.
- Configurable latency/failure injection only when it helps test retry behavior.
- Request timeout expectations documented for connector authors.
- No unbounded loops, tasks, threads, or Faker generation.

## Tests and documentation

- Smoke test for `/health`.
- Auth success/failure tests.
- Pagination and cursor continuation tests across a page boundary.
- Persistence test: mutate/generate, restart/reload, confirm state remains.
- Rate-limit and retry-header test.
- CRUD/delete/webhook test for each simulated write surface.
- README with start commands, credentials placeholders, endpoint examples,
  environment table, data-reset instructions, and tunnel instructions.
