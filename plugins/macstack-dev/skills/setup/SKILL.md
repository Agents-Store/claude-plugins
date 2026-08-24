---
name: setup
description: This skill should be used when the user asks "what is macstack.json", "set up macstack", "check macstack setup", "verify macstack.json", "explain the macstack standard", or before any other macstack-dev skill runs in a project for the first time. Explains the standard, locates the schema and category registry, and verifies tooling.
---

# MACSTACK Setup & Orientation

macstack.json is the standardized JSON file of the MACSTACK framework (Multi-Agent
Composable Stacks). It lives in **`macstack/` in the project root**, alongside the
working documents (`macstack/macstack.json`) — a bare root `./macstack.json` is a
supported legacy location. It is at once: the business spec (goals, results), the
technical spec (software, entities, interfaces, workflows) and the meta-config from
which project files are scaffolded. `CLAUDE.md` references it — never duplicates it.

## Canonical resources (GitHub-first, bundled fallback)

The standard is hosted on GitHub — always prefer the live copies (they may be newer
than the bundled ones); fall back to the bundled copies offline:

| Resource | Live (canonical) | Bundled fallback |
|---|---|---|
| JSON Schema | `https://raw.githubusercontent.com/macstacks/macstack/main/schema/macstack.schema.json` | `${CLAUDE_PLUGIN_ROOT}/skills/lint/references/macstack.schema.json` |
| Category registry | `https://raw.githubusercontent.com/macstacks/registry/main/software-categories.json` | `${CLAUDE_PLUGIN_ROOT}/skills/lint/references/software-categories.json` |
| Reusable blocks (software passports, entity/trigger/agent templates) | `https://github.com/macstacks/registry` (`software/`, `entities/`, `triggers/`, `agents/`) | — |
| Full examples + reference linter | `https://github.com/macstacks/macstack` (`examples/`, `scripts/lint.py`) | — |

Every macstack.json should start with `"$schema":
"https://raw.githubusercontent.com/macstacks/macstack/main/schema/macstack.schema.json"`
— editors then autocomplete and validate live.

Read the schema's top-level `description` first — it encodes the section order
(result-first): goals → results → processes → triggers → workflows → software →
entities → interfaces → connections → agents → context → resources.

## Core concepts (30 seconds)

- **Result-first**: every stack starts from goals/results in money terms; a process
  without a result is "coding for coding's sake".
- **prototype**: a parent macstack.json (GitHub repo `github:owner/repo` or a local
  absolute path). The child extends/overrides it — merge by `id`.
- **stacks**: organization composition — one `root` stack + `substacks`.
  Cross-stack refs use `<stack-id>:<element-id>`.
- **software[]**: every piece of software with mandatory `category` (registry) and
  `type` (ready_made | constructor | framework | library | custom), strict layers
  (data | logic | interface | infrastructure), `instances[]` with URLs.
- **agents**: `stack_agents` (orchestrate the whole stack, read `.claude/`, may modify
  the stack) and `managed_agents` (model + instructions + tools; invoked via
  interface / workflow / trigger / api).
- **Secrets are NAMES only**: `resources.accesses[]` lists env keys (with `required`
  flag); values live in Infisical.

## The `macstack/` folder

The standard also defines a folder of working documents next to macstack.json:

```
macstack/
├── macstack.json           the spec — canonical location
├── README.md               folder contract   [generated]
├── USER-CASES.md           [client] cases per role, versioned
├── TEST-CASES.md           how each acceptance bullet is verified, auto | manual
├── TASKS.md                milestones and tasks — what will be done, in what order
├── BUSINESS-LOGIC.md       [client] invariants and logic in plain words
├── OPEN-QUESTIONS.md       §A owed by the client · §B deferred by us
├── CHANGELOG.md            [client] what reached the people who use it, newest first
├── DECISIONS.md            decision registry (D14, D15 …) → files in decisions/
├── log.md                  append-only journal: intake · merge · work · release
├── inbox/                  IMMUTABLE client material · README.md = manifest
├── deltas/                 proposals, not edits
├── decisions/              rulings, each with cost-if-wrong
└── reviews/                <slug>-conformance.md + its -business.md twin
```

`docs/` stays the ENGINEERING folder (architecture.md, api-conventions.md,
code-style.md, runbooks) — it never moves into `macstack/`.

## Verification steps

1. **Tooling**: `python3 -c "import jsonschema"` (fallback: structural checks only),
   `jq --version`, `gh --version` (needed for discover-context and GitHub prototypes).
2. **Project state**: resolve macstack.json in this order:
   1. `macstack/macstack.json` — canonical.
   2. `./macstack.json` — legacy; works, but say so and offer `docs-migrate`.
   3. Search upward to the git root (monorepo / nested project).
   - Both 1 and 2 present → **ERROR, never a silent choice** — two specs mean two
     truths; report both paths and stop. The remedy is `docs-migrate`, which
     relocates the legacy root file into the folder (or `git rm`s it once the moved
     copy is verified). Never guess which one is canonical.
   - Found → validate it (`lint` skill) and report the stage (`lifecycle.stage`).
   - Not found → offer `init-project` (existing codebase) or `generate-stack` (from
     scratch).
   - Also check whether `macstack/` and its working documents (USER-CASES.md,
     TEST-CASES.md, TASKS.md, BUSINESS-LOGIC.md, OPEN-QUESTIONS.md, CHANGELOG.md,
     DECISIONS.md, log.md) exist. If not,
     offer `project-docs` to create the folder.
3. **CLAUDE.md link**: check that CLAUDE.md contains a "Stack Specification" section
   pointing to macstack.json. If missing, offer to add:

```markdown
## Stack Specification
The business and technical specification of this project is **`macstack.json`**
(MACSTACK standard, canonical at `macstack/macstack.json`). Read it first: goals →
results → processes → workflows → software → entities → interfaces. The working
documents (cases, decisions, open questions) are described in `macstack/README.md`.
Never write code that contradicts macstack.json — update the specification first.
```

## Skill routing

| Task | Skill |
|---|---|
| macstack.json for an existing project | `init-project` |
| New stack from scratch from a request | `generate-stack` |
| Find plugins/prototypes | `discover-context` |
| Create the project's working files | `scaffold-project` |
| .infisical.json + .env.prod/.env.dev | `infisical-env` |
| Project rules and commands | `best-practices` |
| Validation | `lint` |
| Create/seed the `macstack/` folder | `project-docs` |
| Merge new client material into the folder | `docs-merge` |
| Turn the acceptance bullets into checks | `test-cases` |
| Plan work, or reconcile with the tracker | `tasks` |
| Record what was built, or cut a release | `changelog` |
| "Where are we and what next" | `status` |
| Relocate an existing `docs/` into the new layout | `docs-migrate` |
