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
