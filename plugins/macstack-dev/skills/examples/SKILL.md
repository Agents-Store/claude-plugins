---
name: examples
description: This skill should be used when the user asks for "macstack examples", "покажи пример macstack.json", "полный пример стека", "how does a full macstack.json look", or needs an end-to-end scenario walkthrough for this plugin's skills.
---

# MACSTACK Examples & Scenarios

## Reference files

Canonical full examples live in the standard's repo (`docs/macstack/examples/` on the
`feat/macstack-json` branch of the VK-OPS repo / будущий репо стандарта):

- **nova-root** — root workspace организации (composable v1): substacks-реестр,
  иерархия агентов openclaw→claude-code, мастер-сущность client.
- **nova-website** — Application/Web substack: cross-stack мастер лида
  (`master: "nova-root:postgresql"`), 5 типов триггеров, managed-агент via workflow.
- **nova-support-bot** — headless Agents Stack: без prototype, RAG (PG master +
  Qdrant cache), managed-агент via workflow/api.
- **meg-bpms** — клиентский BPMS: ACL до поля, state-поля процессов, внешний мастер
  BAS (`hosting: "external"`).

## Scenario A — существующий проект без macstack.json

```
/macstack-dev:init
→ setup (проверка тулинга) → init-project (аудит кода → черновик + вопросы)
→ lint → CLAUDE.md секция → infisical-env (если есть ключи) → best-practices
```

## Scenario B — новый стек с нуля

```
/macstack-dev:generate "агентство: заявки с сайта, ведение клиентов, отчёты"
→ generate-stack (goals→results→processes→software, result-first)
→ discover-context (плагины + prototype) → lint → подтверждение результатов юзером
→ /macstack-dev:scaffold → prototype → stack-плагины → dev-плагины → файлы
→ infisical-env → best-practices → lint → коммит
```

## Scenario C — организация root + substacks

```
1. generate-stack для root (Agents Workspace, composable) — stacks.role: root
2. generate-stack для сайта — stacks.role: substack + root ref;
   entities.lead.master = "<root-id>:postgresql" (cross-stack)
3. scaffold каждого; в root substacks[] регистрируются оба
```

## Scenario D — обновление живого стека

```
Добавили Qdrant для semantic search:
1. macstack.json: software += qdrant (databases/ready_made/data, agentic full),
   instances, connections.mcp += qdrant-mcp, resources.accesses += QDRANT_URL,
   workflows += wf-embed + trg-nightly
2. /macstack-dev:lint → /macstack-dev:scaffold (доращивает идемпотентно)
3. infisical-env: ключ в Infisical → /secrets-sync
4. Коммит по правилу macstack-sync (спека и код в одном коммите)
```
