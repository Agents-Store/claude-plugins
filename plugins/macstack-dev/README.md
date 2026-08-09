# macstack-dev

Technology plugin (dev) for the **MACSTACK** framework. Creates and maintains
`macstack.json` — the standardized JSON file that lives in the root of a Claude
project and is at once the business spec (goals, results), the technical spec
(software, entities, interfaces, workflows, agents) and the meta-config from which
the project's working files are scaffolded.

## What it does

1. **Init in existing projects** — audits the codebase (manifests, docker-compose,
   `.mcp.json`, DB schemas) and produces a validated `macstack.json`, asking the user
   only the business gaps (goals, results, client).
2. **Generate from scratch** — designs a stack result-first from a business request:
   goals → results → processes → triggers/workflows → software selection
   (prototype reuse first, Open Source first, Agentic IT Ready first).
3. **Discover context** — finds Claude plugins in the Agents Store marketplace
   (github.com/agents-store/claude-plugins) and stack prototypes in
   github.com/orgs/stackmakers-ai; fills `context.plugins` and `prototype`.
4. **Scaffold project files** in the MANDATORY source order:
   **prototype → stack plugins → dev plugins** → generated files. Idempotent.
5. **Wire Infisical env** — creates `.infisical.json`, pulls `.env.prod`/`.env.dev`,
   ensures every key from `resources.accesses` exists, installs the secrets
   scripts (`setup.sh`, `secrets-push.sh`, `env-audit.sh`) and commands.
6. **Install best practices** — the proven `.claude/rules/` set (safety,
   secrets-env-sync, commit-after-task, search-first, external-api-docs,
   project-conventions, macstack-sync) and core commands.
7. **Lint** — JSON Schema (bundled) + referential-integrity rules (masters, triggers,
   instances, cross-stack refs, agent delegation).

## Skills

| Skill | Purpose |
|---|---|
| `setup` | Orientation, schema/registry location, tooling check, CLAUDE.md wiring |
| `init-project` | macstack.json for an existing codebase |
| `generate-stack` | Result-first stack design from a request |
| `discover-context` | Agents Store plugins + stackmakers-ai prototypes |
| `scaffold-project` | Project files in prototype → stack → dev order |
| `infisical-env` | .infisical.json, env pulling, secrets scripts & commands |
| `best-practices` | Rules and core commands installation |
| `lint` | Schema + integrity validation |
| `feedback` | Report a problem and fix it at the source: plugin skills / the schema repo (macstacks/macstack) / the registry (macstacks/registry), with mirror sync |
| `examples` | Full-file examples and end-to-end scenarios |
| `troubleshoot` | Common failure modes |

## Commands

`/macstack-dev:init` · `/macstack-dev:generate` · `/macstack-dev:scaffold` ·
`/macstack-dev:lint` · `/macstack-dev:sync` · `/macstack-dev:feedback`

## Agent

`macstack-architect` — designs macstack.json result-first (goals/results decomposition,
software selection, prototype recommendation).

## Prerequisites

- `python3` with `jsonschema` (full validation; degrades to structural checks),
  `jq`, `gh` (GitHub prototype/marketplace discovery), `infisical` CLI (env wiring).
- No MCP server required — the plugin is file- and GitHub-driven.

## Canonical references

The standard is hosted on GitHub (GitHub-first; the bundled copies below are offline
fallbacks):

- **Standard** (schema, examples, reference linter): https://github.com/macstacks/macstack
- **Registry** (categories, software passports, entity/trigger/agent templates): https://github.com/macstacks/registry
- Bundled fallbacks: `skills/lint/references/macstack.schema.json`,
  `skills/lint/references/software-categories.json`
