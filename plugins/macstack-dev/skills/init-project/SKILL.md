---
name: init-project
description: This skill should be used when the user asks to "create macstack.json in this project", "add macstack.json", "init macstack", "опиши существующий проект в macstack.json", or an existing codebase has no macstack.json. Audits the existing project and produces a validated macstack.json draft.
---

# Init macstack.json in an Existing Project

Create macstack.json for a project that already has code. The file must describe
reality, not aspiration: audit first, write second, ask the user only what cannot be
derived.

## Step 1 — Audit the codebase (evidence, not guesses)

Scan in this order and map findings to macstack.json sections:

| Источник | Что даёт |
|---|---|
| `package.json` / `requirements.txt` / `pyproject.toml` / `composer.json` | `software[]` кандидаты (frameworks, libraries) |
| `docker-compose.yml` (services + images) | `software[]` self-hosted + `instances[]` (порты, env-имена) |
| `.mcp.json` | `connections.mcp[]` (servers, transports, `${VAR}` → url_env) |
| `.env.example` / `.env` (ИМЕНА ключей, НИКОГДА значения) | `resources.accesses[]` |
| `.claude/settings.json` enabledPlugins | `context.plugins` |
| `.infisical.json`, `.dokploy.json`, `.plane.json` | `resources.bindings` |
| Схемы БД / Directus collections / NocoBase collections / migrations | `entities[]` (attributes, master) |
| `src/trigger/`, n8n exports, Flows | `workflows[]` + `triggers[]` |
| App Router pages / админки / боты | `interfaces[]` (path относительно инстанса!) |
| README, CLAUDE.md, docs/ | описание, goals/results черновик |

Classification rules for layers: full-stack frameworks (nextjs, django) → logic +
interface; BaaS/headless CMS (directus, nocodb, supabase) → data; job runners
(trigger-dev, n8n, bullmq) → logic; Docker/CI/Terraform → infrastructure.

## Step 2 — Ask the user ONLY the business gaps

The audit yields the technical half. The business half must come from the user —
ask in ONE compact message:

1. Какие **goals** у проекта (1–3, с горизонтом)?
2. Какие **results** он должен продюсить (измеримо: $, leads/mo, hours saved)?
   Какую **problem** каждый результат закрывает?
3. Кто **клиент/организация** (`identity.client`, `identity.organization`)?
   Есть ли root-стек организации (→ `stacks.role: substack`)?
4. Какой **prototype** (шаблон-родитель), если проект делался по шаблону?

## Step 3 — Write the draft

- Fill sections in the schema's canonical order. Mark everything not confirmed by
  code or user as `"status": "planned"` and list uncertainties in
  `lifecycle.open_questions[]`.
- Every entity MUST get `master` (which software/instance owns it). If two stores
  exist and the master is unclear — that is an open question for the user, never a
  silent guess (wrong master = data corruption later).
- `software[].category` — from the bundled registry; `type` — mandatory;
  slugs kebab-case (`trigger-dev`, not `trigger.dev`; `postgresql`, not `postgres`).
- Triggers: extract cron/webhook/db-event configs into the top-level `triggers[]`
  collection; workflows reference them by id.
- Do NOT invent goals/results the user did not confirm — a spec that lies is worse
  than an incomplete one.

## Step 4 — Validate and wire

1. Run the `lint` skill (schema + referential integrity). Fix every error.
2. Add the CLAUDE.md reference section (see `setup` skill).
3. Offer next steps: `infisical-env` (if accesses exist), `best-practices`
   (rules/commands), `discover-context` (find plugins for the detected software).

<example>
user: "Добавь macstack.json в этот проект (Directus + Next.js сайт)"
→ audit: docker-compose (directus, postgres), package.json (next), .mcp.json (directus mcp),
  src/trigger absent → no trigger-dev
→ ask: goals/results/client/prototype
→ write macstack.json: software [directus(cms/constructor/data), nextjs(frontend-frameworks/framework/logic+interface)],
  entities from Directus collections with master=directus, interfaces site(path "/")+cms-admin(path "/admin")
→ lint → CLAUDE.md section → предложить infisical-env
</example>
