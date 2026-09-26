---
description: Scan a project's source code and produce a stack audit with technology layers, architecture recommendations, and template/stack.json generation suggestions
argument-hint: "Path to project directory (defaults to current directory)"
---

# Audit Project Stack

Scan a project's source code, classify technologies into Logic/Interface/Data layers, and generate template and stack.json recommendations.

## Instructions

1. Read the audit-stack skill at `${CLAUDE_PLUGIN_ROOT}/skills/audit-stack/SKILL.md` — it contains the full 5-phase workflow
2. Read both reference files before starting the scan:
   - `${CLAUDE_PLUGIN_ROOT}/skills/audit-stack/references/technology-signatures.md`
   - `${CLAUDE_PLUGIN_ROOT}/skills/audit-stack/references/layer-classification.md`
3. Determine the target project directory: use `$ARGUMENTS` if provided, otherwise use the current working directory
4. Execute all 5 phases in order:
   - **Phase 1:** Source Code Scan — detect all technologies from package manifests, config files, docker-compose, imports, directory structure
   - **Phase 2:** Layer Classification — classify each technology into Logic / Interface / Data
   - **Phase 3:** Technology Research — use the best available search tools (Firecrawl > Exa > Perplexity > Jina > Context7 > WebSearch) to research each technology's ecosystem
   - **Phase 4:** Architecture Recommendation — consolidation opportunities, layer gaps, modern alternatives, integration patterns
   - **Phase 5:** Template Recommendation — determine level, generate draft stack.json, identify required plugins, output creation command
5. Present the complete 3-part report: Stack Audit, Architecture Recommendation, Template Recommendation

## Target project

$ARGUMENTS
