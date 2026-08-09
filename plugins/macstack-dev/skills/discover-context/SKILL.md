---
name: discover-context
description: This skill should be used when the user asks to "find plugins for this stack", "найди контекст для проекта", "какие плагины поставить", "find a prototype", "подбери прототип", or when init-project/generate-stack need context.plugins and prototype candidates. Searches Agents Store plugins and stackmakers-ai prototypes on GitHub.
---

# Discover Context: Plugins & Prototypes

Find the context a project needs: Claude-плагины в Agents Store и репозитории-прототипы
в stackmakers-ai. Результат — заполненные `context.plugins` и `prototype` в macstack.json.

## Source 1 — Agents Store plugins

Registry: `https://github.com/agents-store/claude-plugins` (public marketplace).
The machine-readable index is `.claude-plugin/marketplace.json` in the repo root:

```bash
# Полный список плагинов маркетплейса (name, description, keywords, category)
curl -s https://raw.githubusercontent.com/agents-store/claude-plugins/main/.claude-plugin/marketplace.json \
  | jq -r '.plugins[] | "\(.name)\t\(.description)"'
# Или через gh (если приватный доступ настроен):
gh api repos/agents-store/claude-plugins/contents/.claude-plugin/marketplace.json \
  -q .content | base64 -d | jq '.plugins[].name'
```

Matching rule — derive plugin names from macstack.json `software[]`:

- Каждому software ищи `{tool}-dev` (разработка), `{tool}-ops` (эксплуатация данных),
  `{tool}-provision` (схема/роли/сетап). Пример: directus → `directus-dev`.
- Для связки слоёв ищи stack-плагин `stack-{name}-{process}` (например
  `stack-directus-nextjs-trigger-dev`, `stack-composable-stack-v1`) — он несёт
  `.mcp.json`, `.env.example` и integration-скиллы.
- Не нашёл плагин — зафиксируй gap в `lifecycle.open_questions` («нет плагина X —
  создать через plugin-creator»), НЕ выдумывай имя в context.plugins.

Fill `context.plugins`: `{technology: [...], process: [...], stack: [...]}` and
`context.marketplaces: ["agents-store-claude-plugins"]`.

## Source 2 — stackmakers-ai prototypes

Registry: `https://github.com/orgs/stackmakers-ai/repositories`.

```bash
gh api "orgs/stackmakers-ai/repos?per_page=100" -q '.[] | .name + "\t" + (.description // "")'
```

Naming convention of prototypes:

| Паттерн | Что это |
|---|---|
| `project-template` | универсальная база (Level 0) |
| `project-{stack}` | шаблон стека: project-composable-stack-v1, project-directus-nextjs, project-directus-nextjs-trigger-dev, project-flask-sqlalchemy | 
| `demo-{stack}` | демо с сид-данными |
| `{client}-{stack}` | клиентские проекты (примеры реальных сборок) |
| `*-workspace-*` | Agents Workspace (root-стек кандидат) |

Selection rule: pick the prototype whose stack matches the chosen software layers;
prefer `project-*` templates over client repos. Set in macstack.json:
`"prototype": "github:stackmakers-ai/<repo>"`. A local clone also works:
`"prototype": "/Users/<me>/STACKS/<repo>"` — оба формата валидны.

Check whether the prototype repo has its own `macstack.json` (new standard) —
inherit via merge-by-id; if it only has legacy `stack.json`, treat it as a scaffold
source only and note it in open_questions.

## Output

Report a compact table: software → найденные dev/ops/provision плагины → stack-плагин →
выбранный prototype (+альтернативы). Then update macstack.json (`context.plugins`,
`prototype`) and validate with `lint`.

<example>
user: "Подбери контекст для стека directus+nextjs+trigger-dev"
→ marketplace.json: directus-dev ✓, nextjs-dev ✓, nextjs-provision ✓, trigger-dev ✓, seo-dev ✓,
  stack-directus-nextjs-trigger-dev ✓
→ prototypes: project-directus-nextjs-trigger-dev (шаблон) — выбран; демо: demo-directus-nextjs
→ macstack.json: prototype + context.plugins заполнены, lint OK
</example>
