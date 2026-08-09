# LEARNINGS — macstack-dev

Accumulated feedback and fixes. Format per entry: date, type, Problem / Fix /
Root cause / Severity.

## 2026-08-09 — initial release notes

- **Schema source of truth**: the bundled `macstack.schema.json` is a copy of the
  standard (VK-OPS `docs/macstack/`, branch `feat/macstack-json`). When the standard
  moves to its own repo/Software Directory, update the bundled copy AND this note.
- **Infisical CLI gotcha** (baked into infisical-env skill): the CLI keeps one ACTIVE
  instance; `--domain` is ignored on authenticated reads — always
  `infisical login --domain=…` before pulling from a different self-hosted instance.
- **Env rendering**: values must be written as `KEY='value'` (single quotes, POSIX
  escape for embedded quotes) or multiline PEM/JWT values break `source .env`.
- **Scaffold order is the product**: prototype → stack plugins → dev plugins. Every
  violation observed in testing produced files that contradicted the architecture.

## 2026-08-09 — first real init-project run (macstack-website-directus-nextjs)

- **Finding / Fix**: the audited project's `.mcp.json` contained HARDCODED credentials
  (an xc-mcp-token and a Figma API key). init-project's audit table already reads
  `.mcp.json` — added an explicit rule: flag any literal token/key found there as a
  SECURITY open_question (rotate + move to `${VAR}`). Root cause: real projects drift;
  the audit must treat `.mcp.json` as a secrets-scan surface, not just an MCP inventory.
  Severity: high.
- **Finding**: deep `grep` over `src/` can hang minutes on cloud-synced folders (iCloud
  file materialization). Fix baked into practice: derive entities from schemas/types
  with a timeout; on timeout record collection names as open_questions instead of
  blocking. Severity: medium.
- **Validation**: generated macstack.json passed schema + all integrity rules on the
  first run; legacy stack.json mapped cleanly (layers→software, plugins→context.plugins,
  parent→prototype candidate + open_question).

## 2026-08-09 — the standard moved to GitHub (v1.1.0)

- The canonical home is now **github.com/macstacks/macstack** (schema, examples,
  scripts/lint.py) + **github.com/macstacks/registry** (categories, software
  passports, entity/trigger/agent templates). All skills are GitHub-first with the
  bundled copies as offline fallbacks; the bundled schema's `$id` points at the raw
  URL. When the schema changes upstream, refresh the bundled copies in
  `skills/lint/references/` in the same PR.

## 2026-08-09 — v1.2.0: feedback loop + dual-source env

- **feedback skill/command added** (mirrors plugin-creator's loop, extended with
  routing): plugin problems → plugin skills; schema problems → macstacks/macstack
  (+ MANDATORY mirror sync: the bundled schema copy here and any project mirrors);
  registry problems → macstacks/registry. A fix applied to a mirror gets silently
  overwritten — always fix at the source, then sync mirrors in the same session.
- **infisical-env now collects variables from TWO sources**: macstack.json
  resources.accesses (architecture) ∪ the env tokens required by the project's
  enabled Claude plugins (settings.json enabledPlugins → stack plugin .mcp.json
  ${VAR} + .env.example + settings.local.json env block). .env.prod/.env.dev are
  always created; required-but-empty keys stay visible as KEY='' with a FILL ME
  comment. Cross-check keeps macstack.json the superset registry of tokens.
