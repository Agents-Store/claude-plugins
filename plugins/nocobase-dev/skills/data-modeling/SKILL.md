---
name: data-modeling
description: |
  NocoBase schema-design playbook — pick the right collection type (general, tree, file, calendar, view, sql, inherit), choose field types and interfaces, design relations (o2m, m2o, m2m, o2o, mbm), select model archetypes for common domains, and verify the applied schema matches intent. Use when:
  - "design a NocoBase schema"
  - "model entities in NocoBase"
  - "which NocoBase collection type should I use"
  - "NocoBase tree collection vs general"
  - "NocoBase view collection from SQL"
  - "NocoBase inheritance pattern"
  - "what field type should I pick"
  - "NocoBase relation design"
  - "many-to-many NocoBase"
  - "belongsTo vs hasMany"
  - "NocoBase schema for CRM / orders / appointments / categories"
  - "NocoBase model packs"
  - "pick collection type"
  - "apply schema and verify"
---

# NocoBase Data Modeling

Design-level guidance for NocoBase collections, fields, and relations. This skill answers *which* to use and *why*; for the operational CRUD calls (create/update/delete collections and fields) use `collections-and-fields` instead.

## When to use this skill

Use when planning a schema, not when executing it:

- "Design a schema for {domain}" → start with `references/decision-matrix.md`
- "Which collection type fits {use case}" → `references/collection-types/index.md`
- "Which relation type between A and B" → `references/relations/index.md`
- "Common model for orders / categories / contracts / appointments" → `references/model-packs/index.md`
- "What can {field type} do" → `references/fields/index.md`
- "Verify the applied schema matches intent" → `references/verification-playbook.md`

## Design workflow

1. **Decide** — open `references/decision-matrix.md` first. It routes by intent (business records, reporting, trees, files, reservations, inheritance, external data).
2. **Model** — for each entity, pick a collection type from `references/collection-types/{general, tree, file, calendar, view, sql, inherit}.md`. Each doc lists the invariants, required options, and caveats.
3. **Field out** — for each attribute, pick a field type from `references/fields/{scalar, choices, datetime, media-and-structured, system-and-advanced, advanced-plugin-fields}.md`. Plugin-provided fields (formula, sequence, encryption, code, map, sort) live under `references/fields/plugins/`.
4. **Relate** — design cross-collection relations from `references/relations/{m2o, o2m, m2m, o2o, mbm}.md`. `mbm` = many-to-many via bridge. One relation per collection pair; never duplicate.
5. **Archetype check** — scan `references/model-packs/` for a pre-built pattern that matches (orders, person-students, contracts-files, calendar-appointments, sql-view-analytics, tree-categories). Reuse the archetype rather than reinventing.
6. **Apply** — call `collections_apply` or `fields_apply` (declarative-apply family). Fallback: `nocobase-ctl data-modeling collections apply --body @spec.json`. Final fallback: HTTP `POST /api/collections:create`.
7. **Verify** — run `references/verification-playbook.md` after every mutation. Confirm the applied meta matches intent — don't trust a 200 response alone.

## Transport

All mutation is via the declarative-apply family first:

- `collections_apply` — upsert a collection + its fields in one call
- `fields_apply` — upsert fields inside an existing collection
- `collections_list_meta` — read-side introspection for verification

Fallback to `nocobase-ctl` CLI or HTTP `POST /api/collections:create`, `POST /api/collections:apply`, `POST /api/fields:apply`. See `mcp-patterns` for the full fallback chain and `collections-and-fields` for operational examples.

## Hard rules (from upstream)

1. **Field truth comes from live collection metadata.** Never guess field lists; always introspect with `collections_list_meta` or `collections_get` before writing `collections_apply` or `fields_apply`.
2. **One relation per table pair.** If a `belongsTo` from `orders` to `customers` exists, do not add another `hasMany` relation with the same pair in the opposite direction — reuse the inverse binding.
3. **`view` and `sql` collections are read-only.** They do not support `create`/`update`/`destroy` on records, and field changes must be re-applied via `collections_apply` (no in-place field edits).
4. **`inherit` requires an `inherits` option** listing parent collection names. Never mix `inherits` with `sources` (inheritance vs data-source-scoped).
5. **Plugin-provided fields require the owning plugin enabled.** `formula`, `sequence`, `encryption`, `code`, `map`, `sort` — check plugin-provided-capabilities.md before adding them.

## Reference index

| Topic | File |
|-------|------|
| Where to start (decision routing) | `references/decision-matrix.md` |
| Collection types overview | `references/collection-types/index.md` |
| · general (most common) | `references/collection-types/general.md` |
| · tree | `references/collection-types/tree.md` |
| · file | `references/collection-types/file.md` |
| · calendar | `references/collection-types/calendar.md` |
| · view (read-only) | `references/collection-types/view.md` |
| · sql (read-only) | `references/collection-types/sql.md` |
| · inherit | `references/collection-types/inherit.md` |
| Field types overview | `references/fields/index.md` |
| · scalar (string, int, decimal, etc.) | `references/fields/scalar.md` |
| · choices (select, radio, multi) | `references/fields/choices.md` |
| · datetime | `references/fields/datetime.md` |
| · media + structured | `references/fields/media-and-structured.md` |
| · system + advanced | `references/fields/system-and-advanced.md` |
| · advanced plugin-provided | `references/fields/advanced-plugin-fields.md` |
| · plugins: formula | `references/fields/plugins/formula.md` |
| · plugins: sequence | `references/fields/plugins/sequence.md` |
| · plugins: encryption | `references/fields/plugins/encryption.md` |
| · plugins: code | `references/fields/plugins/code.md` |
| · plugins: map | `references/fields/plugins/map-fields.md` |
| · plugins: sort | `references/fields/plugins/sort.md` |
| Relations overview | `references/relations/index.md` |
| · many-to-one | `references/relations/m2o.md` |
| · one-to-many | `references/relations/o2m.md` |
| · many-to-many | `references/relations/m2m.md` |
| · many-to-many via bridge | `references/relations/mbm.md` |
| · one-to-one | `references/relations/o2o.md` |
| Field capability matrix | `references/field-capabilities.md` |
| Relation field matrix | `references/relation-fields.md` |
| Plugin capabilities | `references/plugin-provided-capabilities.md` |
| Model archetypes index | `references/model-packs/index.md` |
| · orders pack | `references/model-packs/orders.md` |
| · person / students pack | `references/model-packs/person-students.md` |
| · contracts + files pack | `references/model-packs/contracts-files.md` |
| · calendar appointments pack | `references/model-packs/calendar-appointments.md` |
| · SQL view analytics pack | `references/model-packs/sql-view-analytics.md` |
| · tree categories pack | `references/model-packs/tree-categories.md` |
| MCP mutation sequences | `references/mcp-mutation-sequences.md` |
| Verification playbook (post-mutation) | `references/verification-playbook.md` |

## See also

- `collections-and-fields` — operational CRUD calls, field CRUD, pagination, association queries
- `data-sources` — multi-database schema scoping
- `mcp-patterns` — transport and tool catalog
- `api-patterns/references/utils/` — filter syntax, formulajs, mathjs, UID helpers
