---
description: Review a file, directory, or PR diff in beginner-friendly mode — structured feedback with "why" explanations
argument-hint: <file-path|directory|PR#>
---

# Beginner-Friendly Code Review

Review code with educational explanations. Target: $ARGUMENTS

## Instructions

1. Read all three codemap skills:
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-review/SKILL.md` — primary skill for review methodology
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-explain/SKILL.md` — for explaining complex code sections found during review
   - `${CLAUDE_PLUGIN_ROOT}/skills/codemap-diagram/SKILL.md` — for generating diagrams if review reveals unclear architecture

### Determine Target

2. Parse `$ARGUMENTS` to determine what to review:
   - If it's a file path → read the file
   - If it's a directory → Glob all source files, review each
   - If it's a PR number (e.g., `#15` or `15`) → run `gh pr diff $NUMBER` to get the diff
   - If no argument → ask user what to review

### Execute Review

3. Read the target code
4. Identify context: what framework, what layer (data/logic/interface), what purpose
5. Apply the 5-dimension review from codemap-review skill:
   - **Security** — vulnerabilities, exposed credentials, missing auth checks
   - **Correctness** — logic errors, missing error handling, data isolation
   - **Readability** — unclear names, deep nesting, missing context
   - **Patterns** — framework anti-patterns, inconsistency, deprecated APIs
   - **Beginner Pitfalls** — copy-paste code, over-engineering, missed edge cases
6. For complex sections found during review, use codemap-explain methodology to explain them
7. If review reveals unclear component interactions (3+), generate a mini-diagram using codemap-diagram skill

### Output

8. Start with **what's done well** — 1-2 positive observations
9. List findings using codemap-review skill's output format, grouped by file, sorted by severity:
   - CRITICAL findings first
   - WARNING findings second
   - SUGGESTION findings last
10. If a diagram was generated, include file path and preview URL
11. End with a **summary**: total findings count by severity, top priority to address
12. Keep it proportional — max 5-7 findings for a single file, more for directories/PRs