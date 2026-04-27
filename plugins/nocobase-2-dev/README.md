# nocobase-2-dev

Development plugin for **NocoBase v2** — every realistic management and development scenario covered through the **REST API** or the **`nb` CLI**, whichever is more convenient for the task at hand.

## What's inside

```
nocobase-2-dev/
├── .claude-plugin/plugin.json
├── README.md
├── LEARNINGS.md
├── references/
│   └── openapi/
│       └── nocobase.json                # full OpenAPI 3.0.3 spec, 251 endpoints, v2.1.0-beta.21
└── skills/
    ├── overview/                        # cardinal API-or-CLI rule + skill router
    ├── auth/                            # API Key bearer + OAuth IdP setup
    ├── api-reference/                   # HTTP API map (reference-only, points to OpenAPI)
    ├── cli-recipes/                     # nb CLI install + lifecycle + recipes
    ├── examples/                        # end-to-end scenarios mixing API + CLI
    │
    │   # 11 official upstream skills (verbatim from skills-main):
    ├── nocobase-env-manage/             # bootstrap and lifecycle via `nb`
    ├── nocobase-data-modeling/          # collections, fields, relations, db views
    ├── nocobase-ui-builder/              # default UI authoring entry point
    ├── nocobase-workflow-manage/        # workflows, nodes, executions
    ├── nocobase-acl-manage/             # roles, permissions, role mode
    ├── nocobase-plugin-manage/          # `nb pm` enable/disable/list
    ├── nocobase-publish-manage/         # backup/restore + migration
    ├── nocobase-plugin-development/     # write a NocoBase plugin
    ├── nocobase-dsl-reconciler/         # opt-in YAML/DSL build path
    ├── nocobase-data-analysis/          # query business data
    └── nocobase-utils/                  # evaluators, expressions, UID, etc.
```

## Cardinal rule

For any NocoBase v2 task you can choose **REST API** or **CLI** — pick whichever is more convenient. Don't mix them when one suffices. The `overview` skill routes you to the right place.

## Install the CLI

```bash
npm install -g @nocobase/cli@beta
```

The 11 upstream skills assume the `nb` binary is on your `PATH`. The `cli-recipes` and `nocobase-env-manage` skills cover bootstrap (`nb init --ui`), lifecycle (`nb start`, `nb stop`, `nb upgrade`), plugin manager (`nb pm enable|disable|list`), publish (`nb backup`, `nb restore`, `nb migration`), and the declarative `nb api …` surface.

## Authentication

Two paths, both producing a `Authorization: Bearer <token>` header that satisfies the OpenAPI `api-key` security scheme.

### API Key

```bash
# 1. Enable the API Keys plugin
nb pm enable api-keys

# 2. In NocoBase admin: Settings → API keys → Create
#    Copy the token.

# 3. Authorise requests
curl -H "Authorization: Bearer ${NOCOBASE_API_KEY}" \
     "${NOCOBASE_URL}/api/collections:list"
```

### OAuth (IdP: OAuth)

```bash
# 1. Enable the IdP: OAuth plugin
nb pm enable @nocobase/plugin-oidc-client

# 2. Configure the OAuth provider in admin UI (Settings → Authentication).
# 3. Run the standard authorisation-code flow → exchange code for access token.
# 4. Use the token the same way:
curl -H "Authorization: Bearer ${OAUTH_ACCESS_TOKEN}" \
     "${NOCOBASE_URL}/api/users:list"
```

Full curl + Node.js samples live in `skills/auth/SKILL.md`.

## Skill index

| Skill | Trigger | Source |
|---|---|---|
| `overview` | "How do I do X in NocoBase v2?" | new |
| `auth` | "Authenticate to NocoBase", "create API key" | new |
| `api-reference` | reference-only (loaded on demand) | new |
| `cli-recipes` | "Install nb", "nb commands", "run NocoBase" | new |
| `examples` | "Show me an end-to-end example" | new |
| `nocobase-env-manage` | bootstrap, install, lifecycle | upstream |
| `nocobase-data-modeling` | collections, fields, relations | upstream |
| `nocobase-ui-builder` | pages, blocks, popups (default UI entry) | upstream |
| `nocobase-workflow-manage` | workflows, triggers, executions | upstream |
| `nocobase-acl-manage` | roles, permissions | upstream |
| `nocobase-plugin-manage` | `nb pm` operations | upstream |
| `nocobase-publish-manage` | backup, restore, migration | upstream |
| `nocobase-plugin-development` | write a NocoBase plugin | upstream |
| `nocobase-dsl-reconciler` | YAML-DSL build path (opt-in) | upstream |
| `nocobase-data-analysis` | query business data | upstream |
| `nocobase-utils` | evaluators, expressions, UID | upstream |

## Sources

- Upstream skills: [`nocobase/skills`](https://github.com/nocobase/skills) (`skills-main`).
- OpenAPI: NocoBase v2.1.0-beta.21 (`references/openapi/nocobase.json`).
- Official docs: <https://docs.nocobase.com>.

## Versioning

`1.0.0` — initial release; bundles upstream skills verbatim and the OpenAPI spec frozen at v2.1.0-beta.21.
