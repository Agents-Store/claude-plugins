# google-workspace-dev

One Claude Code plugin for **all of Google Workspace** — Gmail, Drive, Calendar, Sheets, Docs, Chat, Meet, Tasks, Slides, Forms, Keep, People, Classroom, Apps Script, Admin Reports, Events, and Model Armor.

It is a **faithful mirror of the official [`googleworkspace/cli`](https://github.com/googleworkspace/cli) Agent Skills**, vendored into this plugin and **auto-synced weekly** from upstream. Every skill drives the `gws` CLI, which builds its command surface dynamically from Google's Discovery Service — so when Google adds an API, the skills follow.

> **Not an officially supported Google product.** This plugin repackages the upstream open-source skills (Apache-2.0) for the Agents Store marketplace.

## What you get

| Category | Prefix | Count* | What it is |
|----------|--------|--------|------------|
| Service skills | `gws-*` | ~44 | One skill per Workspace API + hand-crafted helper commands (`+send`, `+triage`, `+agenda`, `+upload`, `+meeting-prep`, …) |
| Personas | `persona-*` | 10 | Role lenses: exec-assistant, sales-ops, hr-coordinator, it-admin, project-manager, researcher, team-lead, … |
| Recipes | `recipe-*` | ~41 | Ready-made multi-step workflows (create a presentation, events from a sheet, label & archive emails, …) |
| Setup (custom) | — | 1 | `google-workspace-setup` — install `gws`, OAuth, scopes, troubleshooting |
| Examples (custom) | — | 1 | `examples` — worked end-to-end scenarios chaining several skills |

\* Counts track upstream and drift over time. See [`SKILLS_INDEX.md`](SKILLS_INDEX.md) for the full, current catalog.

## Prerequisites

This plugin is **knowledge, not a binary** — the skills tell Claude how to call the `gws` CLI, which you must install and authenticate once:

```bash
npm install -g @googleworkspace/cli   # or a binary from GitHub Releases / brew
gws auth login -s drive,gmail,calendar,sheets
gws drive files list --params '{"pageSize": 5}'   # verify
```

If anything fails, the **`google-workspace-setup`** skill walks through install, OAuth (including the easy-to-miss "test user" step), scope limits, and the common `Access blocked` / `403 accessNotConfigured` / `redirect_uri_mismatch` errors.

There is **no MCP server** — it is a CLI tool invoked via Bash, so the plugin is pure file-based knowledge.

## Usage

Just ask in natural language — Claude loads the right skill:

- *"Triage my inbox and turn the important emails into tasks."* → `gws-gmail`, `gws-workflow`
- *"Create a Q2 budget spreadsheet and share it with the team."* → `gws-sheets`, `gws-drive`
- *"Prep me for my next meeting."* → `gws-workflow +meeting-prep`
- *"Set up the Google Workspace CLI."* → `google-workspace-setup`
- *"Show me an example of building a report from a sheet."* → `examples`

## How the weekly auto-sync works

| Piece | Location |
|-------|----------|
| Sync script | [`scripts/sync-google-workspace-skills.sh`](../../scripts/sync-google-workspace-skills.sh) |
| GitHub workflow | [`.github/workflows/sync-google-workspace-skills.yml`](../../.github/workflows/sync-google-workspace-skills.yml) |

Every **Monday 06:30 UTC** (and on manual `workflow_dispatch`) the workflow clones upstream, mirrors the `gws-*`/`persona-*`/`recipe-*` directories (adds new, prunes removed), refreshes `SKILLS_INDEX.md`, and — if anything changed — opens a PR labelled `upstream-sync` for review. Custom skills (`google-workspace-setup`, `examples`) and all root metadata are never touched.

> GitHub Actions only runs workflows from the repository root, so the workflow and script live at the repo root, not inside this plugin folder.

Run a sync locally any time:

```bash
./scripts/sync-google-workspace-skills.sh          # latest main
UPSTREAM_REF=v0.22.5 ./scripts/sync-google-workspace-skills.sh   # pin a tag
```

## Attribution & license

- **Vendored skills** (`skills/gws-*`, `skills/persona-*`, `skills/recipe-*`), `LICENSE`, and `SKILLS_INDEX.md` come from [`googleworkspace/cli`](https://github.com/googleworkspace/cli), licensed under **Apache-2.0** (see [`LICENSE`](LICENSE)). Copyright remains with the upstream authors.
- **Custom skills** (`google-workspace-setup`, `examples`), packaging, and the sync tooling are by AGENTS.STORE.

If you find the upstream project useful, ⭐ [star it](https://github.com/googleworkspace/cli) and file issues/feature requests [upstream](https://github.com/googleworkspace/cli/issues).
