---
name: develop-connector
description: Research an upstream API and build a production-shaped Databricks Lakeflow community connector plus a persistent local FastAPI simulator and Databricks Asset Bundle. Use this whenever the user asks to develop, copy, simulate, ingest from, or deploy a connector for an API, especially when they mention `/develop-connector`, Lakeflow community connectors, Delta Live Tables, Databricks, FastAPI, Faker, Cloudflare Tunnel, or a local API that Databricks must reach.
compatibility: Requires a git repository, Python/uv, the Lakeflow community connector source tree, and optionally the Databricks CLI. Internet access is needed for API research; Databricks deployment also needs an authenticated CLI profile and a publicly reachable HTTPS API URL.
---

# Develop Connector

Build an end-to-end connector proof of concept that behaves like a real API
integration: researched source contract, local simulator, Lakeflow connector,
Databricks bundle, connectivity probe, tests, and documented run commands.

## Operating principles

- Start with the API's primary documentation, OpenAPI specification, SDK, or
  source repository. Record what is documented and label reasonable inferences.
- Treat the Lakeflow connector as framework code. Databricks executes the
  generated/merged connector through its Lakeflow runtime; it does not merely
  run the handwritten Python file as an ordinary script.
- Keep the simulator and connector in parallel, predictable locations. Use a
  stable local data file so Faker-generated records survive restarts.
- Make progress with safe assumptions, but do not commit secrets, tunnel tokens,
  access tokens, or unrelated dirty-worktree changes.
- Prefer serverless Lakeflow pipelines for the first deployment. A classic
  cluster stuck in Azure capacity acquisition is an infrastructure problem,
  not evidence that the connector or API is broken.

## Repository layout

For an API slug such as `visit_create_v2`, create or update:

```text
fake-apis/
  README.md
  <api-dir>/
    README.md
    app.py
    pyproject.toml
    uv.lock
    data/<api>.json
    tests/                         # if simulator-specific tests are useful

lakeflow-community-connectors/src/databricks/labs/community_connector/sources/<api_slug>/
  __init__.py
  connector_spec.yaml
  pyproject.toml
  README.md
  <api_slug>_api_doc.md
  <api_slug>_schemas.py
  <api_slug>.py
  _generated_<api_slug>_python_source.py

lakeflow-community-connectors/tests/unit/sources/<api_slug>/
  test_<api_slug>_lakeflow_connect.py

deployment/<api_slug>_dab/
  databricks.yml
  README.md
  <api_slug>_pipeline.py
  <api_slug>_smoke_pipeline.py
  _generated_<api_slug>_python_source.py
  connectivity_probe.py
  resources/<api_slug>.pipeline.yml
  resources/<api_slug>_smoke.pipeline.yml
  resources/connectivity_probe.job.yml

develop-connector/README.md       # workflow notes, when useful
```

Use the repository's existing naming and package conventions if they differ.
Do not duplicate a generated source by hand: regenerate it with the repository
merge script, then copy the generated file into the DAB.

## Phase 1: inspect and branch

1. Read `AGENTS.md`, repository READMEs, connector templates, and the existing
   source interface before editing.
2. Check `git status --short`, current branch, remotes, and relevant history.
3. Create a focused branch such as `agent/<api-slug>-connector`. Preserve
   unrelated user changes; do not reset, stash, or delete them implicitly.
4. Identify the exact API base URL, credentials, target resources, and desired
   deployment catalog/schema. If credentials are missing, use placeholders and
   document the required environment/config values.

## Phase 2: research the API

Research and record, per resource:

- base URL and versioning;
- authentication scheme, credential names, headers, and error responses;
- resource paths, HTTP methods, request parameters, filters, and response shape;
- pagination and ordering;
- stable primary key and change cursor/revision semantics;
- deletes, tombstones, webhooks, and whether reads are snapshot, append, or CDC;
- rate limits, retry headers, timeouts, idempotency, and relevant status codes;
- nested objects, nullable fields, enums, timestamps, and type conversions.

Use official API documentation as the source of truth. If the public docs are
incomplete, inspect SDK behavior or carefully test the live API and document
the inference. Keep a concise API reference in `<api_slug>_api_doc.md`.

## Phase 3: build the FastAPI simulator

Create a lightweight simulator that is useful for connector development rather
than a toy endpoint:

- expose `/health` without authentication and return a small JSON success body;
- implement the researched resource paths and representative filters;
- implement the researched auth model. For Basic auth, the Visit Create
  pattern is an API key as the username with an empty password;
- return realistic HTTP errors, pagination, cursor/revision behavior, deletes,
  and rate-limit headers where the real API has them;
- use a low-frequency Faker generator (for example, one small batch at startup
  or every few minutes) instead of a tight loop that consumes the machine;
- persist generated records in JSON/CSV under `data/`; load and update the file
  atomically enough for local use, and make IDs/cursors stable across restarts;
- include a simulator README with install, start, credentials, endpoint, and
  reset-data commands. Never put real credentials in source control.

Run it locally and test both `/health` and at least one authenticated resource.
If a browser visits a resource URL and receives `{"detail":"Not Found"}`,
that is normally a path mismatch, not an authentication failure; confirm the
exact API path with `curl` and the simulator's route list.

## Phase 4: implement the Lakeflow connector

Follow the repository's `LakeflowConnect` contract and templates. The source
should include:

- constructor option parsing with explicit defaults and no secrets in logs;
- `list_tables`, `get_table_schema`, `read_table_metadata`, and `read_table`;
- one schema and metadata entry per supported resource;
- a bounded request page size and request timeout;
- retries for 429/5xx responses, honoring a valid `Retry-After` value and
  backing off with a hard maximum;
- response validation before yielding records;
- stable primary keys and correct offset/cursor progression;
- filters mapped to the API's exact parameter names;
- a clear `ValueError` for unsupported tables.

Important Lakeflow contract detail: the framework passes `start_offset=None` on
the first read. Normalize it before accessing fields, for example:

```python
start_offset = start_offset or {}
from_revision = int(start_offset.get("revision", table_options.get("from_revision", "0")))
```

Use only ingestion metadata values supported by the installed framework, such
as `snapshot`, `append`, `cdc`, or `cdc_with_deletes`. Do not invent an
`incremental` ingestion type. Use snapshot metadata for resources without a
reliable cursor, and CDC metadata only when the API's cursor/delete behavior
supports it.

Add focused unit tests for first-read `None`, subsequent offsets, pagination,
filters, auth, retries, invalid responses, and unsupported tables. Then run the
repository's merge script, typically:

```bash
python3 tools/scripts/merge_python_source.py <api_slug>
cp src/databricks/labs/community_connector/sources/<api_slug>/_generated_<api_slug>_python_source.py \
  ../../deployment/<api_slug>_dab/_generated_<api_slug>_python_source.py
```

## Phase 5: create the Databricks Asset Bundle

The DAB should deploy Lakeflow assets, not a standalone Python process:

- configure the target host, catalog, schema, public API base URL, and API key
  as variables or target overrides;
- default to `serverless: true` for pipeline resources;
- make the main pipeline register one materialized view/table per connector
  resource;
- add a one-resource smoke pipeline for fast debugging;
- include `connectivity_probe.py`, a dependency-free Python job that tests DNS,
  HTTPS, `/health`, and one authenticated API request from Databricks itself;
- include a DAB job resource for the probe and document bundle-root commands.

Use the Databricks CLI from the directory containing `databricks.yml`:

```bash
databricks auth profiles
databricks current-user me --profile DEFAULT
databricks bundle validate -t dev --profile DEFAULT
databricks bundle deploy -t dev --profile DEFAULT
databricks bundle run <api_slug>_smoke_pipeline -t dev --profile DEFAULT
databricks bundle run <api_slug>_pipeline -t dev --profile DEFAULT
```

If OAuth is stale, reauthenticate explicitly with
`databricks auth login --profile DEFAULT`; retry without forcing plaintext
storage unless the local CLI setup requires it.

## Phase 6: make a local API reachable from Databricks

Databricks serverless cannot reach `127.0.0.1` on the developer machine. A
Cloudflare Quick Tunnel is sufficient for short-lived testing and does not
require buying a domain:

```bash
cloudflared tunnel --url http://127.0.0.1:8000
```

Use the generated `https://<random>.trycloudflare.com` URL in the DAB variable,
keep the tunnel terminal running, and document the procedure under
`fake-apis/cloudflare/`. The URL is temporary and has no production uptime
guarantee. A named tunnel or a hosted service is appropriate for persistent
testing.

The decisive network test must run from Databricks, not only from the laptop:

1. `curl` locally against the public tunnel URL.
2. Run the pure-Python DAB probe from Databricks.
3. Test `/health` at the root health path. If the API base is
   `/create/v2`, do not assume `/create/v2/health` exists; strip the API path
   or configure an explicit health URL.
4. Test the authenticated resource endpoint with the documented auth format.
5. Only after the probe passes, debug Lakeflow connector behavior.

This separates DNS/TLS/tunnel/auth failures from connector-runtime failures.

## Phase 7: debug like the Lakeflow runtime

Use this order when a pipeline fails:

1. Validate the DAB and inspect the exact deployed workspace files.
2. Run the Databricks-side connectivity probe.
3. Run the one-table smoke pipeline.
4. Inspect the pipeline update state and error events with the CLI.
5. Check `start_offset is None` handling, metadata ingestion type, resource
   path, query parameter names, schema types, and generated-source freshness.
6. Run the full pipeline only after smoke succeeds.
7. Query Unity Catalog tables and counts, for example with the Databricks SQL
   CLI tooling, and inspect table schemas with `databricks tables get`.

Do not mistake a browser's 404, a local-only success, an expired Databricks
OAuth token, or a pending classic cluster for the same class of bug. Record the
observed error, the smallest reproduction, the fix, and the verification.

## Phase 8: self-review, documentation, and handoff

Before committing, review:

- API behavior is represented in simulator, connector, and docs consistently;
- no secrets, tokens, private URLs, or accidental generated artifacts are
  committed;
- the fake API persists data and Faker generation is bounded;
- generated connector source matches the handwritten source;
- tests, `git diff --check`, bundle validation, smoke run, probe, and full run
  have been attempted or their blocker is documented;
- only files belonging to this connector are changed. Remove unrelated POCs
  only when the user explicitly requests it, as in a connector-specific branch
  cleanup.

Commit focused changes, push the requested branch, and report the branch,
commit, commands, endpoints, credentials placeholders, test results, deployed
pipeline/job names, and any intentionally uncommitted local data state.
