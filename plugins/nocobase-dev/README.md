# nocobase-dev

Development plugin for **NocoBase v2** — every realistic management and development scenario covered through the **`nb` CLI** (primary surface) or the **REST API** (fallback when CLI is unavailable or inconvenient).

This plugin **auto-syncs** with [`nocobase/skills`](https://github.com/nocobase/skills) weekly. The 11 upstream skills (prefixed `nocobase-*` under `skills/`) are sync-managed — do not edit them by hand. The 5 unprefixed skills (`overview`, `auth`, `cli-recipes`, `api-reference`, `examples`) are hand-maintained custom additions for the REST-API path.

## What's inside

```
nocobase-dev/
├── .claude-plugin/plugin.json
├── README.md
├── LEARNINGS.md
├── references/
│   └── openapi/
│       └── nocobase.json                # OpenAPI 3.0.3, NocoBase v2.1.0-beta.29, 272 endpoints
└── skills/
    │   # Hand-maintained (no nocobase- prefix):
    ├── overview/                        # cardinal CLI-or-API rule + skill router
    ├── auth/                            # API Key bearer + OAuth IdP setup
    ├── cli-recipes/                     # nb CLI install + lifecycle + recipes
    ├── api-reference/                   # REST API map, points to bundled OpenAPI
    ├── examples/                        # end-to-end scenarios mixing CLI + API
    │
    │   # Sync-managed mirror of nocobase/skills (DO NOT EDIT — auto-overwritten):
    ├── nocobase-env-manage/             # bootstrap and lifecycle via nb
    ├── nocobase-data-modeling/          # collections, fields, relations, db views
    ├── nocobase-ui-builder/             # default UI authoring entry point
    ├── nocobase-workflow-manage/        # workflows, nodes, executions
    ├── nocobase-acl-manage/             # roles, permissions, role mode
    ├── nocobase-plugin-manage/          # nb pm enable/disable/list
    ├── nocobase-publish-manage/         # backup/restore + migration
    ├── nocobase-plugin-development/     # write a NocoBase plugin
    ├── nocobase-dsl-reconciler/         # opt-in YAML/DSL build path
    ├── nocobase-data-analysis/          # query business data
    └── nocobase-utils/                  # evaluators, expressions, UID, etc.
```

## Cardinal rule

For any NocoBase v2 task, pick the surface that is more convenient — **CLI primary, REST API fallback**. The `overview` skill routes the user to the right specialist.

- **CLI (`nb …`)** — best when running on a terminal in the project directory: install, lifecycle, `nb pm enable`, backup/restore, migration, declarative `nb api …`.
- **REST API (`/api/…`)** — best when calling NocoBase from another service, a script, or a workflow runner. Driven by the bundled OpenAPI spec.

## Install the CLI

```bash
npm install -g @nocobase/cli@beta
nb init --ui         # browser-based first-time setup
nb start             # later runs
```

Detailed rules in `nocobase-env-manage` and `cli-recipes`.

## Environment variables

The plugin itself has **no `.mcp.json` and no runtime env vars**. The variables below are what a user sets in their own shell when calling NocoBase from the REST-API fallback path (used by `auth`, `examples`, `api-reference`, and the upstream `nocobase-data-analysis` skill).

| Variable | Required for | Purpose | Example |
|---|---|---|---|
| `NOCOBASE_URL` | REST API fallback | Base URL of the NocoBase instance | `https://app.example.com` |
| `NOCOBASE_API_KEY` | REST API — Path A (API Key) | Bearer token from `Settings → API keys` after `nb pm enable api-keys` | `eyJ…` |
| `OAUTH_ACCESS_TOKEN` | REST API — Path B (OAuth) | Token from `/api/auth:signIn?authenticator=…` (OIDC flow) | — |
| `NB_CLI_ROOT` | CLI (optional override) | nb CLI project root, defaults to `~/.nocobase/` | — |

Full setup walk-through (curl + Node.js) in `skills/auth/SKILL.md`.

## Auto-sync from upstream

A GitHub Action at `.github/workflows/sync-nocobase-skills.yml` runs every **Monday at 06:00 UTC** (and on-demand via `workflow_dispatch`). It:

1. Clones [`nocobase/skills`](https://github.com/nocobase/skills) at `main`.
2. `rsync`s only directories matching `nocobase-*` into `plugins/nocobase-dev/skills/`.
3. Opens a PR titled `chore(nocobase-dev): sync upstream skills @ <sha>` if anything changed.

To trigger manually:

```bash
gh workflow run sync-nocobase-skills.yml
# or pin a specific upstream ref / tag:
gh workflow run sync-nocobase-skills.yml -f upstream_ref=v1.0.18
```

To sync locally without CI:

```bash
./scripts/sync-nocobase-skills.sh
```

The script only ever writes to `skills/nocobase-*/`; hand-maintained skills are never touched.

## Skill index

| Skill | Source | Trigger |
|---|---|---|
| `overview` | hand-maintained | "How do I do X in NocoBase v2?" |
| `auth` | hand-maintained | "Authenticate to NocoBase", "create API key" |
| `cli-recipes` | hand-maintained | "Install nb", "run NocoBase", "nb commands" |
| `api-reference` | hand-maintained, reference-only | (loaded on demand by the model) |
| `examples` | hand-maintained | "Show me an end-to-end example" |
| `nocobase-env-manage` | upstream | bootstrap, install, lifecycle |
| `nocobase-data-modeling` | upstream | collections, fields, relations |
| `nocobase-ui-builder` | upstream | pages, blocks, popups (default UI entry) |
| `nocobase-workflow-manage` | upstream | workflows, triggers, executions |
| `nocobase-acl-manage` | upstream | roles, permissions |
| `nocobase-plugin-manage` | upstream | `nb pm` operations |
| `nocobase-publish-manage` | upstream | backup, restore, migration |
| `nocobase-plugin-development` | upstream | write a NocoBase plugin |
| `nocobase-dsl-reconciler` | upstream | YAML-DSL build path (opt-in) |
| `nocobase-data-analysis` | upstream | query business data |
| `nocobase-utils` | upstream | evaluators, expressions, UID |

## Sources

- Upstream skills: [`nocobase/skills`](https://github.com/nocobase/skills) (auto-synced weekly).
- OpenAPI: NocoBase v2.1.0-beta.29 (`references/openapi/nocobase.json`).
- Official docs: <https://docs.nocobase.com>, <https://docs.nocobase.com/ai/quick-start>.

## Versioning

`2.0.0` — replaces the legacy custom `nocobase-dev` (v1.5.0); promotes `nocobase-2-dev` content, refreshes OpenAPI to v2.1.0-beta.29 (272 endpoints, +21 vs prior), adds the upstream auto-sync workflow.
