# macstack-dev

Technology plugin (dev) for the MACSTACK framework. Keeps the `macstack/` folder of a
Claude project: `macstack.json` — the standardized business + technical stack
specification — and the documents it is written from.

The problem it exists for: a client says what they want in their own words, an agent
needs a machine spec to build from, and somebody has to notice when the two stop
agreeing. This plugin owns the path between them in both directions.

## The loop

```
client material  ->  inbox/        immutable, exactly as sent
                     delta         contradictions and additions, a proposal
                     rulings       the owner decides, cost-if-wrong written now
                     client/*.md   the six documents a client reads and corrects
                     macstack.json its business half, written from those documents
                     generated/    the same content, machine-readable, id for id
                     ledger.jsonl  one row per edit, keyed by the id that changed
                     TASKS.md      what will be done, with acceptance
                     code
                     CHANGELOG.md  what reached the people who use it
                  -> review package -> the client answers -> ledger -> inbox/
```

## Commands

| Command | What it does |
|---|---|
| `/macstack-dev:start` | Spec from a codebase, from a business request, or migrate an older layout; then the folder, the env, the rules, the scaffold |
| `/macstack-dev:intake` | Client material in — delta, gates, rulings, apply, log |
| `/macstack-dev:plan` | Requirements nobody scheduled become tasks; tracker reconcile |
| `/macstack-dev:update` | Close the loop after work: spec, generated documents, test cases, journal, changelog |
| `/macstack-dev:check` | Lint and dashboard · `--docs` documents only · `--code` audit the implementation |
| `/macstack-dev:review` | Build the client review package, HTML or artifact; read the answers back |
| `/macstack-dev:feedback` | Fix a problem in the plugin, the schema or the registry — at the source |

## The six client documents

Each answers one question, and none answers another's.

- **`client/OVERVIEW.md`** — what the product is, its goals, who it is for, the
  high-level processes, the invariants, what it refuses to do, the glossary.
- **`client/USER-CASES.md`** — what a person must be able to get, per role, each case
  with a priority, its own UX requirements and an addressable acceptance list.
- **`client/UX-UI.md`** — navigation, empty/loading/error states, responsive behaviour,
  accessibility and tone once; then per screen what is on it, what can be done, and
  what must **not** be visible there.
- **`client/AUTOMATION.md`** — the trigger → task → workflow → role model. A trigger
  declares its `type` (the mechanism) and its `source` (interface · backend ·
  integration · schedule · manual), because the client asks the second question.
- **`client/HANDBOOK.md`** — how a person actually uses the platform.
- **`client/OPEN-QUESTIONS.md`** — §A owed by the client, §B deferred by the team with
  the trigger that ends the deferral.

Around them: `generated/` (REQUIREMENTS, ARCHITECTURE, TEST-CASES, INDEX — never
edited by hand), `inbox/` (immutable), and `history/`: `ledger.jsonl`, `TASKS.md`,
`DECISIONS.md`, `CHANGELOG.md`, `handoffs/`, `archive/`. Six entries in the root of
`macstack/` and six in `history/`, and both counts are a constraint — a folder nobody
can hold in their head is a folder where a duplicate hides.

## How a document is shaped

A client document is markdown and nothing else: headings, bullet lists, prose. No YAML
blocks, no tables, no change-log section. The only machine markup is an HTML comment,
which the reader never sees.

```markdown
<!-- macstack:ref=cases[id=C-04] -->
### C-04 · Отметить занятие

- **Кто:** `coach`
- **Насколько важно:** критично
- **Экраны:** `coach-today`

Тренер отмечает проведённое занятие в тот же день...

**Готово, если**
- отметка сохраняется с точным временем;
- вторая отметка на том же занятии невозможна.
```

The pointer above the heading says where this entity lives in `macstack.json`. Machine
fields are ordinary bullets, read through a label table the contract owns — so
`- **Кто:**` and `- **Who:**` are the same field, and a client can edit either without
knowing that.

Ids and keys are ASCII and never translated; headings, labels and prose follow
`docs.language`. That is what lets one parser read a Russian document and a German one.

Why it matters, measured on a live project: 75% of a document is prose no model
represents. So the writer is a line patcher, not a renderer — changing one field
rewrites one line, and the rest survives because nobody touched it. A tool that rebuilds
a client's document from a model destroys three quarters of it, and that is arithmetic,
not a risk.

## Skills

| Skill | What it holds |
|---|---|
| `documents` | The folder standard AND the document shape: layout, path resolution, invariants, ownership, the pointer bindings, rendering, migration |
| `spec-authoring` | `macstack.json` itself — audit path, design path, discovery, examples |
| `scaffold-project` | Project files, in the mandatory prototype → stack plugins → dev plugins order |
| `intake` | Client material → delta → gates → rulings → apply → log |
| `planning` | Milestones, tasks, backlog, the tracker reconcile, and finding unplanned work |
| `sync` | The spec against the client documents, and against the code |
| `test-cases` | One test per acceptance bullet, derived from cases, triggers and screens |
| `conformance` | Audit the implementation against the documents; the dated review pair |
| `journal` | `history/ledger.jsonl` — one row per edit, comment and audit verdict — and its curated client-facing `CHANGELOG.md` |
| `client-package` | The client package — HTML and published page — with each statement's own history, and reading the answers back into the ledger |
| `lint` | Schema, referential integrity, the folder (39 rules, 12.0–12.38), and the status dashboard |
| `infisical-env` | `.env` wiring from `resources.accesses` |
| `best-practices` | Project rules and commands |
| `setup` | Orientation, tooling, path resolution, the CLAUDE.md and AGENTS.md blocks |
| `troubleshoot` | Symptom → cause → fix |
| `feedback` | Route a fix to the plugin, the schema or the registry |

Agent: `macstack-architect`, for a spec spanning many domains or an ambiguous software
choice.

## Prerequisites

`python3` (plus `jsonschema` for full schema validation), `jq`, `gh`, and the
`infisical` CLI if the project uses it. No MCP server required.

## Canonical references

GitHub first, bundled copy as the offline fallback:

- schema — `macstacks/macstack`, mirrored in `skills/lint/references/`
- registry — `macstacks/registry` (software categories, coverage areas)
- the folder's own structure — `skills/documents/references/doc-contracts.json`, read
  by both the writer (`documents`) and the checker (`lint`), so the two cannot drift

When the schema changes it changes in all three places at once. Verify a push with
`gh api repos/macstacks/macstack/contents/<path>?ref=main` — a plain `curl` against the
CDN right after a push serves the previous revision and prints an entirely false diff.
