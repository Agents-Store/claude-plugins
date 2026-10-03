# n8n-dev

n8n workflow automation development plugin for Agents Store. Comprehensive knowledge base for building, debugging, and managing n8n workflows and n8n Agents. Targets **n8n 2.x** (checked against 2.41).

## Skills (21)

### Vendored from czlonkowski/n8n-skills (15)

Mirrored verbatim from [`czlonkowski/n8n-skills`](https://github.com/czlonkowski/n8n-skills) (MIT) by `scripts/sync-n8n-skills.sh`. Do not edit them here.

| Skill | Description |
|-------|-------------|
| **using-n8n-mcp-skills** | Upstream router: which skill owns which task, working knowledge of the `n8n-mcp` tools |
| **n8n-mcp-tools-expert** | External MCP tools guide — node search, validation, workflow CRUD, templates, credentials, audit |
| **n8n-workflow-patterns** | Proven architectural patterns (webhook, HTTP API, database, AI agent, scheduled) |
| **n8n-node-configuration** | Operation-aware node configuration with property dependencies |
| **n8n-validation-expert** | Validation error interpretation and fixing |
| **n8n-expression-syntax** | Expression patterns, `{{}}` syntax, `$json` / `$('Node')` references |
| **n8n-code-javascript** | JavaScript Code node — `$input`, `$helpers`, error patterns |
| **n8n-code-python** | Python Code node on the native runner — `_items` / `_item`, imports blocked by default |
| **n8n-code-tool** | The AI-agent-callable Custom Code Tool |
| **n8n-agents** | AI Agent node design, tools, memory, structured output, RAG, persisted n8n Agents |
| **n8n-error-handling** | Error outputs, error workflows, retries, response shapes |
| **n8n-subworkflows** | Reusable sub-workflows, Execute Workflow, workflows as agent tools |
| **n8n-binary-and-data** | Files, images and binary data, including the agent-tool boundary |
| **n8n-multi-instance** | Targeting one of several n8n instances safely |
| **n8n-self-hosting** | Deploying and operating self-hosted n8n (Docker Compose, single and queue mode) |

### Local (6)

Hand-written for this plugin; the sync never touches them.

| Skill | Description |
|-------|-------------|
| **n8n-native-mcp** | Native (instance-level) MCP guide — SDK workflows, atomic edits, tests, publishing, first-class Agents |
| **api-reference** | REST API reference — 60 operations in the bundled spec plus the 2.x publish routes, curl examples |
| **cli-recipes** | Server CLI (publish, export/import, license, users) and the remote `@n8n/cli` |
| **setup** | MCP connection configuration and verification |
| **troubleshoot** | Common errors, diagnostics, and solutions |
| **examples** | End-to-end scenario walkthroughs |

## Agent

**n8n-developer** — Specialist agent for workflow building, debugging, and n8n operations. It inherits all tools, including the configured n8n MCP servers.

## Vendored vs local

| | Vendored (15) | Local (6) |
|---|---|---|
| Directories | every upstream skill directory except the six on the right | `n8n-native-mcp`, `api-reference`, `cli-recipes`, `setup`, `troubleshoot`, `examples` |
| Source of truth | `czlonkowski/n8n-skills` | this repository |
| Changed by | `scripts/sync-n8n-skills.sh` only (`rsync --delete`) | hand |
| A fix goes to | upstream; until it lands it is recorded as "pending upstream" in `LEARNINGS.md` | the skill itself |

The sync keeps the local list in one place (`LOCAL` at the top of the script). A new hand-written skill must be added there **before** the next sync; a directory that is neither local nor upstream is reported as a warning and never deleted.

```bash
./scripts/sync-n8n-skills.sh                       # latest upstream v* tag
UPSTREAM_REF=v1.35.0 ./scripts/sync-n8n-skills.sh   # pin a tag
```

The script prints the upstream commit SHA on stdout, copies the upstream licence to `LICENSE-n8n-skills`, and a weekly workflow (`.github/workflows/sync-n8n-skills.yml`, Monday 07:00 UTC, or on demand) opens a PR when anything changed. After a sync run `./scripts/scrub-check.sh plugins/n8n-dev`: a finding inside a vendored file gets a baseline line in its own pull request, never an edit of the vendored file.

## Prerequisites

This plugin provides knowledge only — no MCP servers are bundled. Configure n8n MCP servers at the project level:

### Environment Variables

| Variable | Used By | Purpose |
|----------|---------|---------|
| `N8N_API_URL` | External MCP | n8n instance URL — root or ending in `/api/v1` |
| `N8N_API_KEY` | External MCP | Public API key (Settings → n8n API) |
| `N8N_MCP_ACCESS_TOKEN` | External MCP (optional) | Instance-level MCP access token; unlocks `n8n_test_workflow` `prepare` / `pinned` / `direct`, `n8n_manage_agents`, `n8n_explore_node_resources`, native version history, data-table column actions. A separate secret from `N8N_API_KEY` |
| `N8N_NATIVE_MCP_URL` | Native MCP | Full MCP endpoint URL (`…/mcp-server/http`), from Settings → Instance-level MCP → Connect |
| `N8N_MCP_TOKEN` | Native MCP | MCP access token, from Settings → Instance-level MCP → Connect → API key tab |

The instance must have MCP enabled (**Settings → Instance-level MCP → Enable MCP access**, owner or admin, n8n 2.2+; the builder tools need 2.13+). Each workflow a client may run or edit must also be switched on as **Available in MCP**. OAuth is the recommended sign-in: `claude mcp add --transport http n8n-native-mcp https://<n8n-host>/mcp-server/http`, then `/mcp` (keep the name `n8n-native-mcp` so the tool names in the skills resolve).

### MCP Servers

**External MCP** (recommended for development; `npx n8n-mcp` pulls the latest release — pin it as `n8n-mcp@<version>` for a reproducible setup):
```json
{
  "n8n-mcp-external": {
    "command": "npx",
    "args": ["n8n-mcp"],
    "env": {
      "MCP_MODE": "stdio",
      "N8N_API_URL": "${N8N_API_URL}",
      "N8N_API_KEY": "${N8N_API_KEY}",
      "N8N_MCP_ACCESS_TOKEN": "${N8N_MCP_ACCESS_TOKEN:-}"
    }
  }
}
```

**Native MCP** (for SDK workflows, tests, publishing and Agents):
```json
{
  "n8n-native-mcp": {
    "type": "http",
    "url": "${N8N_NATIVE_MCP_URL}",
    "headers": {
      "Authorization": "Bearer ${N8N_MCP_TOKEN}"
    }
  }
}
```

## Official n8n resources

- [`n8n-io/skills`](https://github.com/n8n-io/skills) — the official skill pack for the instance-level MCP server
- n8n docs MCP server: `claude mcp add --transport http n8n-docs https://docs.n8n.io/~gitbook/mcp`
- [`@n8n/cli`](https://docs.n8n.io/connect/n8n-cli) — remote command-line client over the Public API

## Credits

The vendored skills are from [n8n-skills](https://github.com/czlonkowski/n8n-skills) by Romuald Czlonkowski (MIT License, see [`LICENSE-n8n-skills`](LICENSE-n8n-skills)). The local skills, the agent and the sync tooling are by Agents Store.
