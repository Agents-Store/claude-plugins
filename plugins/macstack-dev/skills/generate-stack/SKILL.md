---
name: generate-stack
description: This skill should be used when the user asks to "generate macstack.json from scratch", "спроектируй стек под задачу", "design a stack for…", "подбери программы и архитектуру", or describes a business need without an existing codebase. Designs goals, results, processes, workflows, software and architecture result-first and produces a validated macstack.json.
---

# Generate macstack.json From Scratch (Result-First)

Design a complete stack from a user request. The order is NON-NEGOTIABLE: money first,
software last. Never start from "какие технологии взять" — start from "какой результат
приносит деньги".

## Step 1 — Goals & Results (деньги)

From the user's request extract and confirm:

1. **goals[]** — 1–3 бизнес-цели с горизонтом и метрикой («$20k MRR к Q2»,
   «сократить цикл согласования в 5 раз»).
2. **results[]** — измеримые активы, реализующие цели. Каждый: `class`
   (revenue_asset | client_revenue | pipeline_asset | cost_saving), `metric`
   {unit, target, cadence}, `problem` (какую проблему закрывает), `goal` ref.
   Формулировки — бизнес-исходы, не технологии.

If the user gave only a vague need ("хочу бота"), ask the result question explicitly:
«Какой измеримый результат бот должен продюсить и сколько это стоит в месяц?»

## Step 2 — Processes → Triggers → Workflows

3. **processes[]** — какие бизнес-процессы производят результаты; `type`
   (development | operations | provisioning), `automation_mode`
   (workflow — детерминированно | agent — агент решает сам | hybrid), tasks с
   HITL-гейтами (`human {role, gate}`) там, где человек обязателен.
4. **triggers[]** — отдельная коллекция: что запускает автоматизацию
   (schedule / webhook / db_event / form / manual), в каком software живёт.
5. **workflows[]** — детерминированные реализации: engine, `triggers` refs,
   invocation (mcp/api/cli/webhook/trigger), naming `[Domain] - [Action] - [Trigger]`.

## Step 3 — Software selection (подбор программ)

Select software per layer using these rules, in priority order:

1. **Prototype first**: check `discover-context` for a stackmakers-ai prototype that
   already covers the need (composable workspace, directus-nextjs site, agents
   stack…). Reuse beats assembly: set `prototype` and inherit its software.
2. **Open Source first, Agentic Ready first**: prefer tools with MCP + API + CLI
   (rating full/good): postgresql, nocodb, nocobase, n8n, trigger-dev, directus,
   qdrant, minio. A stack without MCP is "just software".
3. **Стандартные связки** (проверенные): universal workspace = postgresql + nocodb +
   n8n (+trigger-dev); web app = directus + nextjs (+trigger-dev); headless
   agents stack = postgresql + qdrant + n8n/trigger-dev; BPMS = nocobase.
4. **Custom code — только для уникального**: то, чего нет готового; `type: "custom"`,
   category `custom-scripts`.

For every software fill the taxonomy: `category` (bundled registry), `type`,
`form`, `license`, `layers` (strict: data | logic | interface | infrastructure,
multi-layer allowed), `hosting`, `value` (зачем в стеке — одна из 4 ценностей),
`agentic {mcp, api, cli, rating}`, `instances[]`.

## Step 4 — The rest of the file

- **entities[]** — сущности с attributes, stores и ОБЯЗАТЕЛЬНЫМ master; внешние
  системы клиента = software с `hosting: "external"`.
- **interfaces[]** — human и agent-facing; `path` относительный (полный URL = url
  инстанса + path); уведомления = `type: "channel"`.
- **connections** — MCP/API/CLI разводка (из неё потом генерится `.mcp.json`).
- **agents** — stack_agents (worker минимум; orchestrator если нужен мессенджер-фронт)
  + managed_agents (model + instructions + tools + invocations).
- **context.plugins** — из `discover-context`: technology `{tool}-{dev|ops|provision}`
  + stack-плагин архитектуры.
- **resources.accesses** — ВСЕ env-ключи с `required` флагом (источник для
  `infisical-env`).
- **profile** — type (composable | application | agents), stack_level, patterns.
- **commercial** — оффер и Cost of Ownership (open-source first экономику показывать
  явно).
- **lifecycle** — `stage: "define"`, open_questions, needs_from_client.

## Step 5 — Validate & present

Run `lint`. Present the file result-first: сначала goals/results таблицей, затем
процессы, затем стек. Ask the user to confirm the RESULTS before any scaffolding —
«система проектируется от результата» значит, что менять результат после сборки дорого.

Use the `macstack-architect` agent for the design when the request spans many
domains or the software choice is ambiguous.

<example>
user: "Нужен стек для агентства: принимать заявки с сайта, вести клиентов, слать отчёты"
→ goals: inbound-канал; results: qualified-leads (pipeline_asset, 30/mo), weekly-report (cost_saving)
→ processes: lead-capture (workflow), reporting (workflow), crm-upkeep (hybrid)
→ prototype: github:stackmakers-ai/project-composable-stack-v1 (workspace) — сайт отдельным substack
→ software: postgresql+nocodb+n8n+trigger-dev; entities: client (master postgresql), lead, report
→ lint → показать результаты → подтвердить → scaffold-project
</example>
