---
name: full-feature
description: This skill should be used when the user asks to "build a complete feature", "add an end-to-end feature to the app", "implement CRUD with UI in Next.js + Payload", "create a feature from collection to page", or needs the standard cross-layer recipe for the nextjs-payloadcms stack.
---

# Full Feature — End-to-End Recipe

Build every feature by walking the same nine steps through the stack's layers, in order. Each step lands in a fixed location (see `architecture`), so features stay uniform and reviewable. Use `template.md` in this skill's directory as the fill-in checklist for a concrete feature.

## The Nine Steps

```
1. Collection (schema)  →  2. Access  →  3. Hooks  →  4. Types  →  5. Jobs
→  6. Actions  →  7. Queries  →  8. UI  →  9. Tests + Migration
```

### 1. Collection — `src/collections/<feature>.ts`

Define the data model as a `CollectionConfig`: fields, relationships, admin list config (`useAsTitle`, `defaultColumns`, `listSearchableFields`). Enable `versions: { drafts: true }` only for content that needs a draft/publish cycle. Register in `payload.config.ts`.

### 2. Access — reuse `src/access/roles.ts`

Attach `access: { create, read, update, delete }` using the shared role helpers and scoping factories (`companyScopedAccess()`, `ownByEmployeeRelation()`). Add field-level access for sensitive fields. New rule shapes go into the shared module, not inline — every collection must be able to reuse them.

### 3. Hooks — `src/hooks/<feature>.ts`

Derived fields and invariants in `beforeChange` (throw `APIError` on violations); side effects in `afterChange`; anything slow queued as a job. Extract state machines and calculations into pure helpers next to the hook file.

### 4. Types — regenerate

`pnpm generate:types` after every schema change. Downstream steps import the generated interfaces; nothing hand-writes document shapes.

### 5. Jobs — `src/jobs/<task>.ts` (only if the feature has async work)

`TaskConfig` with typed input/output; register under `jobs.tasks`. Queue from the hook or action with IDs as input. Confirm a runner drains the queue you chose (`background-job`).

### 6. Actions — `src/actions/<feature>.ts`

One `'use server'` file per domain: authenticate via `getSession()`, validate with friendly messages, mutate with `overrideAccess: false, user`, `revalidatePath` on success, return `{ ok, error }` — never throw for expected failures.

### 7. Queries — `src/lib/queries/<feature>.ts`

Read helpers `(payload, args) => DTO[]` with explicit `depth`/`select`/`sort`. Pages never call `payload.find` inline.

### 8. UI — `src/app/(frontend)/<route>/page.tsx`

RSC page: session check → query helper → render. Forms are client components submitting to the action via `useActionState`. Role-gate whole sections in the segment `layout.tsx`.

### 9. Tests + Migration

- Unit tests colocated with pure helpers (state machine, calculations).
- Integration test colocated with the collection: boot `getPayload`, exercise access + hooks through the Local API (create as different roles, assert filters and rejections).
- `pnpm payload migrate:create <feature>` once the schema is final; commit the migration.

## Definition of Done

- [ ] Collection registered; admin list usable (title, columns, search)
- [ ] Access rules reuse shared helpers; sensitive fields gated
- [ ] Invariants throw in hooks (not only checked in actions)
- [ ] `payload-types.ts` regenerated; no hand-written doc types
- [ ] Slow side effects run as jobs with a configured runner
- [ ] Actions: auth check, `overrideAccess: false`, revalidate, `{ ok, error }` result
- [ ] Reads go through `lib/queries` DTO helpers
- [ ] Cached content pages revalidated by an `afterChange` hook
- [ ] Unit + integration tests pass; migration committed

Worked scenarios applying this recipe live in the `examples` skill.
