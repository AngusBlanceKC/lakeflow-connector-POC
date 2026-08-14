---
name: develop-connector
description: Orchestrate an end-to-end API connector build: research a source, create a realistic persistent FastAPI simulator, delegate connector work to the Lakeflow repository skills, test and self-review it, and deploy it as a Databricks pipeline. Use whenever the user asks for `/develop-connector`, `/validate-connector`, `/self-review-connector`, API replication, a fake API, Lakeflow/community connector work, Databricks deployment, Cloudflare reachability, Faker data, or an API connector copied into the repository.
compatibility: Requires this repository, the nested `lakeflow-community-connectors` checkout, Python/uv, and optionally an authenticated Databricks CLI. Internet access is needed for API research; live auth and deployment are sequential gates.
---

# Develop Connector: workflow orchestrator

This skill is the project-level coordinator. It owns the end-to-end workflow and
the fake API. It delegates connector-specific work to the existing skills in
`lakeflow-community-connectors/.claude/skills/` instead of copying their
implementation rules into this file.

Read [references/fake-api-contract.md](references/fake-api-contract.md) before
creating or reviewing a simulator.

## Required repository locations

For source name `<source_name>` and API slug `<source_slug>`:

```text
fake-apis/<source_slug>/
lakeflow-community-connectors/src/databricks/labs/community_connector/sources/<source_name>/
lakeflow-community-connectors/tests/unit/sources/<source_name>/
deployment/<source_slug>_dab/
```

The connector repository is the source of truth for Lakeflow package layout,
interfaces, tests, generated-source merging, and connector documentation.

## Delegate to the existing connector skills

Use the corresponding skill or command from the nested connector repository in
the phase where it is listed. Pass the source name, table scope, relevant paths,
and artifacts already produced. Read the target `SKILL.md` before invoking it.

| Workflow phase | Delegate to | Expected output |
|---|---|---|
| Research READ APIs | `/research-source-api <source>` | `sources/<source>/<source>_api_doc.md` |
| Collect credentials | `/authenticate-source <source>` | interactive auth and `tests/unit/sources/<source>/configs/dev_config.json` |
| Implement connector | `/implement-connector <source>` | `sources/<source>/<source>.py` and schemas/tests as appropriate |
| Run/fix tests | `/test-and-fix-connector <source>` | passing simulate or record-mode pytest suite |
| Public docs | `/create-connector-document <source>` | `sources/<source>/README.md` |
| Connector spec | `/generate-connector-spec <source>` | `sources/<source>/connector_spec.yaml` |
| Deploy connector | `/deploy-connector <source>` | configured/running Databricks pipeline |
| Research write APIs | `/research-write-api-of-source <source>` | documented write-back contract |
| Implement write-back tests | `/write-back-testing <source>` | source-specific write utilities/tests |
| Validate completed connector | `/validate-connector <source>` | auth, live tests, optional deployment gate |
| Self-review completed connector | `/self-review-connector <source>` | scored `tests/unit/sources/<source>/SELF_REVIEW.md` |

The exact skill files live under:

```text
lakeflow-community-connectors/.claude/skills/
lakeflow-community-connectors/.claude/commands/validate-connector.md
lakeflow-community-connectors/.claude/commands/develop-connector.md
```

Do not implement a second connector framework in this project skill. If the
nested repository changes its Lakeflow contract, follow its skill and templates.

## End-to-end sequence

### 1. Establish scope safely

- Read repository instructions and the nested connector repository's relevant
  skill files.
- Inspect `git status --short`, branch, remotes, and existing source artifacts.
- Use a focused branch unless the user explicitly asks to work directly on
  `main`. Preserve unrelated dirty files and never reset or stash them without
  permission.
- Normalize names: keep the upstream source name for the connector package and
  use a filesystem-safe slug for `fake-apis/` and `deployment/`.
- Identify source URL/docs, resources, target catalog/schema, and whether the
  user wants simulated-only, live validation, write-back, or deployment.

### 2. Research the source first

Delegate READ research to `/research-source-api`. The API document must cover
authentication, endpoints, parameters, response schemas, pagination, ordering,
primary keys, cursors/revisions, deletes, rate limits, errors, and known gaps.
Use official docs first and label inferences. If write-back is in scope, run
`/research-write-api-of-source` separately; do not mix undocumented writes into
the READ contract.

### 3. Build the fake API in parallel with the contract

Create `fake-apis/<source_slug>/` as a FastAPI simulator matching the researched
API. Apply every item in the fake API contract reference. At minimum it must:

- have an unauthenticated `/health` endpoint;
- implement realistic resource paths, auth, permissions, filters, pagination,
  cursors, deletes/tombstones, and representative errors;
- persist state in `data/*.json`, `*.csv`, or `*.jsonl` and retain it between
  process restarts using atomic writes;
- seed deterministic baseline records so tests are reproducible;
- use Faker only in bounded, low-frequency batches with a hard cap and an
  environment-configurable interval; never run an unbounded tight generator;
- expose configuration through environment variables and document defaults;
- include a README with install/start commands, credentials, endpoint examples,
  reset-data instructions, and Cloudflare guidance;
- include simulator tests or smoke commands for health, auth, pagination,
  persistence, rate limits, and one write/delete path when supported.

Run the simulator locally before the connector tests. A browser 404 such as
`{"detail":"Not Found"}` usually means the URL path is wrong, not that auth
failed. Check the exact route and use `curl` with the documented credentials.

### 4. Delegate connector implementation and artifacts

Run the existing skills in dependency order:

1. `/implement-connector <source>`
2. `/generate-connector-spec <source>`
3. `/create-connector-document <source>`
4. `/test-and-fix-connector <source>` in `simulate` mode

The nested repository's `LakeflowConnect` contract governs offsets, schemas,
metadata, and generated source. In particular, the first Lakeflow read can pass
`start_offset=None`; the implementation must normalize that before reading
offset fields. Do not invent metadata values such as `incremental`; use values
supported by the installed framework. Regenerate merged source using the
nested repository's tooling and copy it to the DAB only after the source passes.

If the API supports writes and the user requested them, run research-write,
write-back-testing, and test-and-fix after READ behavior is stable.

### 5. Authenticate and validate against the live source when requested

Run `/authenticate-source <source>` only when live tests are requested or
required. It owns the browser credential flow and writes the dev config in the
nested repository's expected location. Never commit that file or echo secrets.
Then run `/validate-connector <source>`, which owns record-mode tests, drift
validation, and optional deployment gates.

### 6. Create the Databricks deployment layer

Use `/deploy-connector <source>` for the connector repository's native pipeline
deployment. For this project's realistic local-source POC, also create a DAB at
`deployment/<source_slug>_dab/` containing:

- `databricks.yml` with target, catalog/schema, public API URL, and secret
  references or placeholders;
- a main Lakeflow pipeline with one materialized view/table per resource;
- a one-resource smoke pipeline;
- a dependency-free Databricks-side connectivity probe job;
- the regenerated connector source and a README with bundle-root commands.

The DAB deploys Lakeflow assets; it is not a way to run the connector as an
ordinary local Python process. Prefer serverless for the first run.

### 7. Make local APIs reachable from Databricks

Databricks cannot call the developer machine's `127.0.0.1`. For short-lived
testing, use a Cloudflare Quick Tunnel without buying a domain. The complete
repository-specific guide is
[`fake-apis/cloudflare/README.md`](../fake-apis/cloudflare/README.md).

Install and verify the CLI:

```bash
# macOS
brew install cloudflared

# verify on any platform after installing by the platform's package method
cloudflared --version
```

Start the FastAPI service first, then create the temporary public HTTPS URL:

```bash
# in the fake API directory
<your-venv>/bin/uvicorn app:app --host 127.0.0.1 --port 8000

# in a second terminal
cloudflared tunnel --url http://127.0.0.1:8000
```

Copy the generated `https://<random>.trycloudflare.com` URL into the DAB/API
configuration. Quick Tunnels do not require `cloudflared tunnel login`, an
account, or a purchased domain. Keep the tunnel terminal running; the URL
changes when the process stops. A message about no default config file is
normal for a Quick Tunnel because it is not using a named-tunnel config.

For a stable hostname, a Cloudflare account and a domain managed in that
account are required. The CLI setup is:

```bash
cloudflared tunnel login
cloudflared tunnel create <tunnel-name>
cloudflared tunnel list
# copy fake-apis/cloudflare/config.example.yml to ~/.cloudflared/config.yml
# replace the tunnel UUID and hostname in that config
cloudflared tunnel route dns <tunnel-name> api.example.com
cloudflared tunnel --config ~/.cloudflared/config.yml run <tunnel-name>
```

Keep `~/.cloudflared/` and tunnel credentials out of git. Use the generated
hostname as `https://api.example.com/<api-base-path>` for the connector.

Always separate network debugging from connector debugging:

1. Confirm the local API: `curl http://127.0.0.1:8000/health`.
2. Confirm the public tunnel: `curl https://<tunnel-host>/health`.
3. Confirm auth and the exact resource path with `curl -u <api-key>:` or the
   source's documented auth headers.
4. Run the pure-Python probe from Databricks to verify DNS, TLS, `/health`, and
   one authenticated resource request.
5. If the API base is `/create/v2`, test `/health` at the root unless the
   simulator explicitly exposes `/create/v2/health`; do not infer the health
   path from the resource base path.
6. Only after the Databricks-side probe passes, run the smoke pipeline.

If public curl works but the Databricks probe fails, inspect the tunnel process,
hostname, HTTPS certificate, workspace egress policy, and API path before
changing connector code. If the probe passes but Lakeflow fails, debug the
connector contract and generated source instead.

### 8. Debug and verify in order

Use the narrowest reproduction first:

1. `databricks bundle validate` from the directory containing `databricks.yml`.
2. Databricks-side connectivity probe.
3. One-table smoke pipeline.
4. Pipeline update/error inspection with the Databricks CLI.
5. Check generated-source freshness, `start_offset=None`, metadata ingestion
   type, resource paths, filters, schemas, retries, and cursor advancement.
6. Full pipeline.
7. `databricks tables get` and SQL row-count checks for representative outputs.

If the CLI says the OAuth refresh token is invalid, reauthenticate with
`databricks auth login --profile DEFAULT`. If a classic cluster remains pending
on cloud capacity, retry serverless before changing connector code.

### 9. Review, clean up, and hand off

Run `/self-review-connector <source>` after tests, docs, and spec generation.
Resolve blockers or report them with file/line evidence. Check that the fake
API, API document, connector, generated source, DAB, and docs agree. Remove
unrelated POCs only when explicitly requested. Use `git diff --check`, keep
secrets and dev configs out of commits, commit focused files, and push the
requested branch or `main`.

Report the resulting paths, credentials placeholders, simulator commands,
public URL requirements, probe/pipeline/job names, tests, row-count evidence,
commit/branch, and any intentionally uncommitted persistent data file.
