# nocobase-dev

Development plugin for **NocoBase v2** — every realistic management and development scenario covered through the **`nb` CLI** (primary surface) or the **REST API** (fallback when CLI is unavailable or inconvenient).

This plugin **auto-syncs** with [`nocobase/skills`](https://github.com/nocobase/skills) weekly. The 20 upstream skills (prefixed `nocobase-*` under `skills/`) are sync-managed — do not edit them by hand. The 5 unprefixed skills (`overview`, `auth`, `cli-recipes`, `api-reference`, `examples`) are hand-maintained custom additions: the router, authentication, the `nb` CLI recipes and the REST-API path. Last sync: upstream `686de87` (`v2.0.58`, 2026-09-04); command forms were checked against `@nocobase/cli` 2.2.20.

## What's inside

```
nocobase-dev/
├── .claude-plugin/plugin.json
├── README.md
├── LEARNINGS.md
├── references/
│   └── openapi/
│       └── nocobase.json                # OpenAPI 3.0.3 snapshot, NocoBase v2.1.0-beta.29, 272 endpoints (refresh from a >= 2.2.x stand pending)
└── skills/
    │   # Hand-maintained (no nocobase- prefix):
    ├── overview/                        # cardinal CLI-or-API rule + skill router
    ├── auth/                            # nb env auth, sign-in, API Key bearer, IdP: OAuth, Auth: OIDC
    ├── cli-recipes/                     # nb CLI install + env + lifecycle + recipes
    ├── api-reference/                   # REST API map, points to bundled OpenAPI
    ├── examples/                        # end-to-end scenarios mixing CLI + API
    │
    │   # Sync-managed mirror of nocobase/skills (DO NOT EDIT — auto-overwritten):
    ├── nocobase-portal-manage/          # PRIMARY ENTRY for every UI authoring request (Portal dispatcher)
    ├── nocobase-ui-builder/             # no-code Portal UI authoring (entered via portal-manage)
    ├── nocobase-ai-builder/             # AI Portal source-code applications
    ├── nocobase-prototype-repro/        # rebuild an app from an HTML/image/link prototype
    ├── nocobase-env-manage/             # bootstrap and lifecycle via nb
    ├── nocobase-data-modeling/          # collections, fields, relations, db views
    ├── nocobase-workflow-manage/        # workflows, nodes, executions
    ├── nocobase-acl-manage/             # roles, permissions, role mode, Portal access
    ├── nocobase-plugin-manage/          # nb plugin list/enable/disable
    ├── nocobase-publish-manage/         # backup/restore + migration
    ├── nocobase-plugin-development/     # write a NocoBase plugin
    ├── nocobase-ai-manager/             # LLM providers, services, models
    ├── nocobase-ai-employee/            # AI employee lifecycle
    ├── nocobase-ai-knowledge-base-manager/  # knowledge bases, vector databases
    ├── nocobase-file-manager/           # storage engines, file collections
    ├── nocobase-notification-manage/    # in-app and email notification channels
    ├── nocobase-revision/               # restorable revisions of a built app
    ├── nocobase-dsl-reconciler/         # opt-in YAML/DSL build path
    ├── nocobase-data-analysis/          # query business data
    └── nocobase-utils/                  # evaluators, expressions, UID, etc.
```

## Cardinal rule

For any NocoBase v2 task, pick the surface that is more convenient — **CLI primary, REST API fallback**. The `overview` skill routes the user to the right specialist.

- **CLI (`nb …`)** — best when running on a terminal with an `nb` env configured: install, lifecycle (`nb app …`), `nb plugin enable`, `nb backup create|restore`, migrations (`nb api migration …`), declarative `nb api …`.
- **REST API (`/api/…`)** — best when calling NocoBase from another service, a script, or a workflow runner. Driven by the bundled OpenAPI spec.

## Install the CLI

```bash
npm install -g @nocobase/cli     # stable channel (`latest`); Node.js >= 22, Yarn 1.x
nb init --ui                     # browser-based first-time setup (install a new app or connect an existing one)
nb app start                     # later runs
```

Connecting an agent to an existing NocoBase needs NocoBase **2.1.0 or newer**. The stable channel is the plugin's default; `@nocobase/cli@alpha` is only needed for `nb portal` (Portal lifecycle), which the stable and beta channels do not contain — `docs.nocobase.com` currently installs `@alpha` for that reason. Detailed rules in `nocobase-env-manage` and `cli-recipes`.

## Environment variables

The plugin itself has **no `.mcp.json` and no runtime env vars**. With the CLI you do not need any: `nb env add` / `nb env auth` store the endpoint and credential (see `skills/auth`). The variables below are for curl/Node scripts and the `nocobase-dsl-reconciler` scripts — they match the names used by the upstream `nocobase/skills` (see `nocobase-dsl-reconciler` for the canonical reference). Use the **same names** in your `.env` so that hand-maintained and upstream skills resolve to one truth.

| Variable | Required? | Purpose | Example |
|---|---|---|---|
| `NB_URL` | **always** | Base URL of the NocoBase instance | `https://app.example.com` or `http://localhost:14000` |
| `NB_USER` | yes, unless `NB_TOKEN` set | Admin email created during `nb init --ui` | `admin@example.com` |
| `NB_PASSWORD` | yes, unless `NB_TOKEN` set | Admin password from `nb init --ui` | `admin123` |
| `NB_TOKEN` | optional | Long-lived bearer token (skips `auth:signIn`). Created in `Settings → API keys` (the built-in API keys plugin is enabled by default). | `eyJhbGciOi…` |
| `NOCOBASE_API_TOKEN` | optional | Synonym for `NB_TOKEN` — upstream auth helper reads either. | — |
| `PG_DSN` | rarely | Direct Postgres connection — only used by `nocobase-dsl-reconciler` data-copy scripts | `postgres://user:pass@host:5432/nocobase` |

**Two valid setups:**

```bash
# Setup A — login flow (recommended, matches upstream quick-start)
NB_URL=https://app.example.com
NB_USER=admin@example.com
NB_PASSWORD=<password>

# Setup B — pre-issued token (skips signIn each call)
NB_URL=https://app.example.com
NB_TOKEN=eyJhbGciOi...
```

Full setup walk-through (CLI envs, curl + Node.js, the `auth:signIn` flow, OAuth through IdP: OAuth, and the separate Auth: OIDC SSO plugin) in `skills/auth/SKILL.md`.

## MCP

The plugin does not ship an MCP configuration — an endpoint is per instance. NocoBase itself has a built-in MCP server (`@nocobase/plugin-mcp-server`) at `https://<host>:<port>/api/mcp` (sub-applications: `/api/__app/<app_name>/mcp`), authenticated with an API key or OAuth. Add it to your own MCP client; details in `skills/overview` and `skills/auth`.

## Auto-sync from upstream

A GitHub Action at `.github/workflows/sync-nocobase-skills.yml` runs every **Monday at 06:00 UTC** (and on-demand via `workflow_dispatch`). It:

1. Clones [`nocobase/skills`](https://github.com/nocobase/skills) at `main`.
2. `rsync`s only directories matching `nocobase-*` into `plugins/nocobase-dev/skills/`.
3. Opens a PR titled `chore(nocobase-dev): sync upstream skills @ <sha>` if anything changed.

To trigger manually:

```bash
gh workflow run sync-nocobase-skills.yml
# or pin a specific upstream ref / tag:
gh workflow run sync-nocobase-skills.yml -f upstream_ref=v2.0.58
```

To sync locally without CI:

```bash
./scripts/sync-nocobase-skills.sh
```

The script only ever writes to `skills/nocobase-*/`; hand-maintained skills are never touched. A sync can bring in text the publication gate rejects (upstream sample paths, test addresses): never edit the synced files — add a value-pinned baseline line to `scripts/scrub-allow.txt` in a pull request that changes nothing else.

## Skill index

| Skill | Source | Trigger |
|---|---|---|
| `overview` | hand-maintained | "How do I do X in NocoBase v2?" |
| `auth` | hand-maintained | "Authenticate to NocoBase", "create API key" |
| `cli-recipes` | hand-maintained | "Install nb", "run NocoBase", "nb commands" |
| `api-reference` | hand-maintained, reference-only | (loaded on demand by the model) |
| `examples` | hand-maintained | "Show me an end-to-end example" |
| `nocobase-portal-manage` | upstream | any UI authoring request — the primary entry; Portal lifecycle (`nb portal`, alpha CLI) |
| `nocobase-ui-builder` | upstream | pages, blocks, popups — internal continuation after `portal-manage` |
| `nocobase-ai-builder` | upstream | AI Portal source-code applications |
| `nocobase-prototype-repro` | upstream | rebuild from a prototype (HTML, image, link) |
| `nocobase-env-manage` | upstream | bootstrap, install, lifecycle, CLI and skills maintenance |
| `nocobase-data-modeling` | upstream | collections, fields, relations |
| `nocobase-workflow-manage` | upstream | workflows, triggers, executions |
| `nocobase-acl-manage` | upstream | roles, permissions |
| `nocobase-plugin-manage` | upstream | `nb plugin` operations |
| `nocobase-publish-manage` | upstream | backup, restore, migration |
| `nocobase-plugin-development` | upstream | write a NocoBase plugin |
| `nocobase-ai-manager` | upstream | LLM providers, services, models |
| `nocobase-ai-employee` | upstream | AI employees |
| `nocobase-ai-knowledge-base-manager` | upstream | knowledge bases, vector databases |
| `nocobase-file-manager` | upstream | file storage, file collections |
| `nocobase-notification-manage` | upstream | notification channels and logs |
| `nocobase-revision` | upstream | restorable revisions |
| `nocobase-dsl-reconciler` | upstream | YAML-DSL build path (opt-in) |
| `nocobase-data-analysis` | upstream | query business data |
| `nocobase-utils` | upstream | evaluators, expressions, UID |

## Sources

- Upstream skills: [`nocobase/skills`](https://github.com/nocobase/skills) (auto-synced weekly).
- OpenAPI: NocoBase v2.1.0-beta.29 snapshot (`references/openapi/nocobase.json`); NocoBase stable is 2.2.x, so the live app's schema (`nb api --help`, `swagger:getUrls`) is authoritative.
- CLI reference: <https://docs.nocobase.com/api/cli/index.md>; MCP: <https://docs.nocobase.com/ai/mcp>.
- Official docs: <https://docs.nocobase.com>, <https://docs.nocobase.com/ai/quick-start>.

## Versioning

`2.1.0` — re-syncs the vendored skills from upstream (12 → 20 `nocobase-*` skills, `v2.0.58`), and rewrites the hand-maintained files for `nb` 2.2: canonical `nb app|env|plugin|backup` forms, `nb api` generated groups, `POST /workflows:execute`, stable `@nocobase/cli` channel, Node.js >= 22, IdP: OAuth versus Auth: OIDC, the built-in `/api/mcp`, and a 20-skill router with `nocobase-portal-manage` as the UI entry. The bundled OpenAPI is still the 2.1.0-beta.29 snapshot (refresh pending).

`2.0.0` — replaces the legacy custom `nocobase-dev` (v1.5.0); promotes `nocobase-2-dev` content, refreshes OpenAPI to v2.1.0-beta.29 (272 endpoints, +21 vs prior), adds the upstream auto-sync workflow.
