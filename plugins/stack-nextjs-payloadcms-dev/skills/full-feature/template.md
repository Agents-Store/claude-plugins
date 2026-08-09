# Feature: {{FEATURE_NAME}}

> Copy this file into the feature branch (or paste into the plan) and fill every section before coding.

## 0. Intent

- User story: As a {{ROLE}}, I want {{CAPABILITY}} so that {{OUTCOME}}.
- Entry points touched: [ ] frontend page  [ ] admin panel  [ ] external API  [ ] schedule

## 1. Collection — `src/collections/{{slug}}.ts`

- Slug: `{{slug}}` (kebab-case)
- Fields: {{field: type — purpose, one line each}}
- Relationships: {{field → relationTo, hasMany?}}
- Admin: `useAsTitle: '{{field}}'`, `defaultColumns: [...]`, `listSearchableFields: [...]`
- Options: timestamps ✅ (default) · versions/drafts? · upload? · trash (soft delete)?

## 2. Access — `src/access/roles.ts`

| Operation | Rule |
|---|---|
| create | {{e.g. authenticated}} |
| read | {{e.g. companyScopedAccess() / ownByEmployeeRelation()}} |
| update | {{e.g. hrOrAdmin}} |
| delete | {{e.g. adminOnly}} |

Field-level gates: {{sensitive field → hrOrAdminField}}

## 3. Hooks — `src/hooks/{{slug}}.ts`

- beforeChange: {{derive/validate/stamp — list rules; which throw APIError}}
- afterChange: {{side effects; which queue jobs; context guard needed?}}
- Pure helpers extracted: `src/lib/{{helper}}.ts` — {{state machine / calculation}}

## 4. Types

- [ ] `pnpm generate:types` after schema settles

## 5. Jobs — `src/jobs/{{task}}.ts` (delete section if none)

- Task slug: `{{task-slug}}` · input: `{ {{id fields}} }` · retries: {{n}}
- Trigger: {{afterChange hook / action / schedule cron `{{cron}}` queue `{{queue}}`}}
- Runner that drains `{{queue}}`: {{autoRun / worker container / vercel cron}}

## 6. Action — `src/actions/{{domain}}.ts`

- `{{name}}Action(formData)` → pre-checks: {{friendly validations}}
- Mutation: `payload.{{create|update}}({ collection: '{{slug}}', overrideAccess: false, user })`
- On success: `revalidatePath('{{route}}')`

## 7. Queries — `src/lib/queries/{{domain}}.ts`

- `{{list...}}(payload, {{args}})` → DTO `{ {{fields}} }` · depth: {{0}} · sort: `{{-createdAt}}`

## 8. UI — `src/app/(frontend)/{{route}}/`

- `page.tsx` (RSC): session → query → render
- Client components: {{form with useActionState / table / dialogs}}
- Section gating: `layout.tsx` redirect for {{roles}}

## 9. Verification

- [ ] Unit tests: {{pure helpers covered}}
- [ ] Integration test: create/read as {{role A}} vs {{role B}} — filters and rejections assert
- [ ] Migration: `pnpm payload migrate:create {{feature}}` committed
- [ ] Manual: admin panel entry + frontend flow + job executed (check `payload-jobs`)
