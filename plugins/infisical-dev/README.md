# infisical-dev

Complete **Infisical CLI** coverage for Claude Code — a Technology (dev) plugin for the Agents Store marketplace. Knowledge-only: no MCP server, no credentials. Everything runs through the `infisical` binary on your machine, against Infisical Cloud (US/EU) or a self-hosted instance.

## What it covers

The Infisical CLI retrieves, modifies, exports, and **injects secrets into any process** as environment variables — plus scans code for leaked secrets, runs the Infisical Agent, and keeps several login profiles for multi-organization work. This plugin gives Claude accurate, task-oriented knowledge of that surface, checked against CLI 0.43.138.

## Skills

| Skill | Use it for |
|-------|------------|
| `setup` | Install the CLI, authenticate, point at self-hosted/EU (`INFISICAL_DOMAIN`), keep named login profiles, and verify it works |
| `cli-recipes` | Everyday workflows: `init`, `run`, `secrets` (CRUD + folders), `export`, dynamic-secret leases |
| `secret-scanning` | `infisical scan`, git-history/staged scans, pre-commit hooks, custom rules, baselines, `.infisicalignore` |
| `ci-cd-auth` | Machine-identity auth (Universal Auth, Kubernetes, AWS/GCP/Azure, OIDC), Docker & pipeline injection, `bootstrap` |
| `cli-reference` | Full command / flag / environment-variable reference, including `agent`, `gateway`, `relay`, `proxy`, `pam`, `kmip`, `cert-manager` and `agent-vault` (manual-load only) |
| `troubleshoot` | Keyring/login failures, self-hosted/domain issues, token scope errors, missing secrets |

## Agent

`infisical-developer` — an Infisical CLI specialist that wires `infisical run` into dev/build workflows, sets up CI/CD machine-identity auth, configures secret scanning, and debugs CLI errors.

## Prerequisites

- The [Infisical CLI](https://infisical.com/docs/cli/overview) installed (the `setup` skill walks through every platform)
- An Infisical account/project (Cloud or self-hosted) and either an interactive login or a machine identity for automation

No plugin configuration is required — the CLI manages its own authentication via `infisical login`, `INFISICAL_TOKEN`, and `.infisical.json`.

## Quick start

```bash
brew install infisical/get-cli/infisical   # or see the setup skill for your OS
infisical login
cd your-project && infisical init
infisical run -- npm run dev               # secrets injected as env vars
```

## Notes

- **Official vendor skills:** Infisical publishes its own AI skills in [`Infisical/ai-skills`](https://github.com/Infisical/ai-skills) (MIT, install with `/plugin marketplace add Infisical/ai-skills`; 17 skills covering the SDKs, API, Terraform, Kubernetes operator, PKI, KMS, PAM, SSO and more). This plugin is the CLI-recipes layer and does not duplicate them — reach for the vendor skills for platform topics beyond the `infisical` binary.
- **Hosted docs MCP:** Infisical runs a documentation MCP server at `https://infisical.com/docs/mcp` (no authentication; it searches and reads the docs). Add it with `claude mcp add --transport http infisical-docs https://infisical.com/docs/mcp`.
- An official Infisical **MCP server** (`@infisical/mcp`, stdio via `npx`) also exists for tool-call access to secrets — it is separate from the CLI. This plugin is intentionally CLI-focused.
- Built from the official docs at https://infisical.com/docs/cli/overview

---

Made by **AGENTS.STORE**.
