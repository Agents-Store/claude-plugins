---
name: examples
description: This skill should be used when the user asks for "macstack examples", "show a full macstack.json example", "how does a complete macstack.json look", "walk me through a macstack scenario", or needs an end-to-end scenario walkthrough for this plugin's skills.
---

# MACSTACK Examples & Scenarios

## Reference files

Canonical full examples live in the standard's repository
(`github.com/macstacks/macstack`, `examples/`):

- **nova-root** — an organization's root workspace (composable v1): the substacks
  registry, the openclaw→claude-code agent hierarchy, the organization's master
  `client` entity.
- **nova-website** — an Application/Web substack: a cross-stack lead master
  (`master: "nova-root:postgresql"`), 5 trigger types, a managed agent invoked via
  workflow.
- **nova-support-bot** — a headless Agents Stack: no prototype, RAG (PG master +
  Qdrant cache), a managed agent invoked via workflow/api.
- **meg-bpms** — a client BPMS: field-level ACL, status fields driving processes,
  an external master (`hosting: "external"`).

## Scenario A — an existing project without macstack.json

```
/macstack-dev:init
→ setup (tooling check) → init-project (code audit → draft + questions)
→ lint → CLAUDE.md section → infisical-env (if keys exist) → best-practices
```

## Scenario B — a new stack from scratch

```
/macstack-dev:generate "an agency: website lead intake, client management, reports"
→ generate-stack (goals→results→processes→software, result-first)
→ discover-context (plugins + prototype) → lint → user confirms the results
→ /macstack-dev:scaffold → prototype → stack plugins → dev plugins → files
→ infisical-env → best-practices → lint → commit
```

## Scenario C — an organization: root + substacks

```
1. generate-stack for the root (Agents Workspace, composable) — stacks.role: root
2. generate-stack for the website — stacks.role: substack + root ref;
   entities.lead.master = "<root-id>:postgresql" (cross-stack)
3. scaffold each; both get registered in the root's substacks[]
```

## Scenario D — updating a live stack

```
Adding Qdrant for semantic search:
1. macstack.json: software += qdrant (databases/ready_made/data, agentic full),
   instances, connections.mcp += qdrant-mcp, resources.accesses += QDRANT_URL,
   workflows += wf-embed + trg-nightly
2. /macstack-dev:lint → /macstack-dev:scaffold (grows idempotently)
3. infisical-env: add the key to Infisical → /secrets-sync
4. Commit per the macstack-sync rule (spec and code in one commit)
```

## Scenario E — the client drops a PDF

```
Client emails a PDF spec update
1. It lands in inbox/ → a manifest row in inbox/README.md
2. Read it (materialization/size check first) → drafted as a delta with
   contradictions (K-N) and additions (N-N)
3. Owner rules on each item → decisions/ + a DECISIONS.md registry row
4. USER-CASES.md bumps a version for the affected role section
5. Unresolved items become new §A rows in OPEN-QUESTIONS.md
6. The delta gets its applied banner; log.md gets a merge entry naming the source
```
