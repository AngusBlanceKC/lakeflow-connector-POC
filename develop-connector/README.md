# `develop-connector`

This repository-level skill captures the repeatable workflow used to create
the Visit Create v2 simulator and Lakeflow connector. It is intended to be
invoked as `/develop-connector` when an agent is pointed at a new upstream API.

The full instructions are in [SKILL.md](SKILL.md). The test prompts used to
refine the workflow are in [evals/evals.json](evals/evals.json).

The workflow delegates connector-specific phases to the existing skills in
`lakeflow-community-connectors/.claude/skills/`; it owns the project-level fake
API contract and Databricks/Cloudflare orchestration.

If your agent only discovers skills from a conventional project skills folder,
link or copy this directory into that folder; keep the source here so the
workflow travels with the repository.
