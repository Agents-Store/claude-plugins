# LEARNINGS.md — postgresql-external-dev

## 2026-04-14 — relations: One relation type per table pair

**Problem:** When designing a schema with both a direct FK column (`workflows.software_instance_id` -> `software_instances.id`) and a M2M junction table (`nc_m2m_workflows_software_instances`) between the same two tables, NocoDB and NocoBase auto-detect both relations independently, creating duplicate link columns in the UI.
**Fix:** Added "One Relation Per Table Pair" section to `relations/SKILL.md` with rule: use either a direct FK or a M2M junction between any two tables, never both. Added it as the first item in the Relation Checklist.
**Root cause:** The skill documented FK and M2M patterns separately without warning about combining them on the same table pair.
**Severity:** Major

**Update 2026-10-03:** upstream NocoDB later fixed the related duplicate-link bugs (issue 13788 in 2026.05.2, issue 13349 in 2026.06.0). The rule remains as best practice but is now marked historical in `relations/SKILL.md`; the symptom needs a re-test on 2026.09.x.

## 2026-10-03 — create-tables, column-types, troubleshoot, modify-schema: what the platforms really accept

**Problem:** The skills banned several PostgreSQL types outright (ARRAY, native ENUM, geometric types, UUID primary keys, jsonb) as unsupported, and said auto-increment integers were the only keys NocoDB accepts. They never said that the NocoBase external PostgreSQL connector is a commercial plugin, nor that schema changes need a Meta Sync (NocoDB) or a data source refresh (NocoBase). The field names used for date/time and JSON columns did not match the mapping table in the NocoBase docs.
**Fix:** Reframed as "safe default" versus "accepted with caveats", per platform, with sources: NocoBase external-database docs (license, field type mapping, Record unique key, refresh) and NocoDB `PgUi.ts`, native enum support (release 2026.04.5), the Primary Key docs and the Sync with Data Source docs. Added the license note, PostgreSQL version matrix, tables without a primary key, a sync step after every DDL and a backup-and-confirm step before drops. NocoBase Field column now uses the docs' mapping (`date`, `dateOnly`, `time`, `json`, `uuid`, `array`).
**Root cause:** The first version turned one working schema into prohibitions without checking them against upstream. The wider-type claims here come from docs and source reading, not from a live database run.
**Severity:** Major

## 2026-10-03 — postgres-mcp-tools, postgrest-api: PostgreSQL MCP and PostgREST knowledge moved in from `stack-composable-stack-v1`; two Task 27 review items

**Problem:** The only reference for the PostgreSQL MCP tools and the PostgREST API lived in the stack plugin (`stack-composable-stack-v1/skills/postgresql-api`), so anyone using `postgresql-external-dev` alone had no way to run or inspect the database it designs. The text also carried errors: "27 tools" and "Supabase Toolbox v0.31.0" (the server is MCP Toolbox for Databases, 29 tools), a fixed "PostgREST v14.8", upsert written as an `on_conflict` request header (it is a query parameter — the header is ignored and a conflict on another unique column returns 409), `return=none` listed as a value, and `{{ $env.… }}` in an n8n expression (blocked by default since n8n 2.0). Two review items from Task 27 were open: the drop-FK and drop-junction sections of `modify-schema` did not point at the backup-and-confirm rules, and the NocoDB licence cell said the external PostgreSQL source "needs no extra plugin" as if no edition or plan question existed.
**Fix:** Variant A of the stack split (decision 2026-09-06, D5): new skills `postgres-mcp-tools` (all 29 tools, bare `mcp__<server>__<tool>` names because this plugin ships no `.mcp.json`) and `postgrest-api`. The PostgREST recipes were run against PostgREST 16.3 on PostgreSQL 17 (throwaway containers, destroyed afterwards): `?on_conflict=` with `Prefer: resolution=merge-duplicates,return=representation`; `return=representation|minimal|headers-only`; `return=none` is ignored; `missing=default` needs `?columns=`; `max-affected` is enforced only with `handling=strict` (without it a filterless DELETE removed every row); `tx=rollback` is ignored unless the server allows it; anonymous 401 versus authenticated 403. `modify-schema` gained "(see Before You Drop Anything)" under Drop FK Constraint and Drop Junction Table; the NocoDB licence wording in `create-tables` and `compatible-platforms` is now "no separate plugin; check your NocoDB edition/plan".
**Root cause:** The stack plugin carried a single-tool reference because it was written before the technology plugins existed; nothing re-ran its curl recipes against a server after PostgREST changed.
**Severity:** Major
