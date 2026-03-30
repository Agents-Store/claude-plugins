---
name: wrap-up
description: >
  Use this skill when the user says "wrap up", "end session", "done for today",
  "session review", "what should go into the template", "template improvements",
  "save template learnings", "review what we did for the template", or at the end
  of a work session to review what discoveries should be pushed up to parent templates.
disable-model-invocation: true
---

# End-of-Session Template Wrap-Up

Review the current session, identify improvements that should be pushed to parent templates, and apply or record them.

## Phase 1: Session Review

Analyze the current conversation and list:

1. **Template files modified** — Skills, commands, rules, CLAUDE.md, docs, configs that were created or changed during this session
2. **Workarounds discovered** — Manual fixes that should be documented in the template (gotchas, edge cases, missing env vars)
3. **New skills/commands created** — Generic enough to benefit all projects using this stack
4. **Missing environment variables** — Vars that had to be added during the session
5. **Documentation gaps** — Architecture, code style, or API conventions that were unclear
6. **Safety rules discovered** — Patterns that should be prevented in all projects
7. **Dependency additions** — Libraries added that should be available by default
8. **Configuration fixes** — Settings, Docker configs, build configs that needed tweaking

Present as:

```
## Session Review

**Current project:** {project-name} (Level {N})
**Parent templates:** {Level 1 parent} → {Level 0 parent}

### Template Improvements Found

#### Push to Level 0 (all stacks)
✅ {description of universal improvement}

#### Push to Level 1 (this stack only)
✅ {description of stack-specific improvement}

#### Project-only (skip)
⏭️ {description of project-specific change — not for template}
```

## Phase 2: Categorize Findings

For each finding, classify:

- **Target level:** Level 0 (universal) / Level 1 (stack-specific) / project-only (skip)
- **Category:** skill, command, agent, rule, CLAUDE.md, .env.example, docs, config, script, dependency
- **Priority:** Must-have (blocks future projects) / Nice-to-have (convenience improvement)

### Classification Rules

Push to **Level 0** if:
- It benefits ALL stacks regardless of technology (process skills, safety rules, generic commands)
- It's a fix to a core template file (sync script, generic docs structure)

Push to **Level 1** if:
- It depends on specific technologies (Next.js patterns, Directus SDK usage)
- It's a stack-specific gotcha or workaround
- It adds stack-specific environment variables or dependencies

Keep **project-only** if:
- It contains client resource IDs, names, or credentials
- It's domain-specific business logic
- It's a one-off customization

When unsure, use the `template-architect` agent to decide.

## Phase 3: User Decision

Present the categorized findings and ask:

> "Found {N} template improvements ({M} for Level 0, {K} for Level 1). Should I:
> (a) Apply fixes to parent templates and commit
> (b) Create GitHub Issues on parent repos
> (c) Just record in this project's LEARNINGS.md
> (d) Skip"

### For option (a) — Fix and commit:
Delegate to the `feedback` skill for each item. Read the feedback skill at `${CLAUDE_PLUGIN_ROOT}/skills/feedback/SKILL.md`.

When fixing multiple items in the same parent template, apply all fixes before committing — create one commit per parent template with a summary message, not one commit per fix.

### For option (b) — GitHub Issues:
Create ONE grouped issue per parent template:

```bash
gh issue create \
  --repo "stackmakers-ai/$PARENT_NAME" \
  --title "Template improvements from session $(date +%Y-%m-%d)" \
  --label "template-feedback" \
  --body "$GROUPED_FINDINGS_MARKDOWN"
```

### For option (c) — Record only:
Append to the current project's `LEARNINGS.md` with a `TEMPLATE FEEDBACK` marker:

```markdown
## [DATE] — TEMPLATE FEEDBACK: Session wrap-up

**Target:** {parent-template-name} (Level {N})
**Findings:**
1. {description} — {category} — {priority}
2. ...

**Status:** Recorded, not yet applied to parent template.
```

## Phase 4: Suggest New Skills

If the session revealed missing capabilities in the template:

> "During this session you manually created a '{skill-name}' workflow. Should I add this as a skill to {parent-template-name}?"

If the user agrees, delegate to the `feedback` skill with the skill creation details.

## Phase 5: Summary

```
Session wrap-up complete:
  - Applied {N} fixes to {parent-name} (committed)
  - Created {N} GitHub Issues
  - Recorded {N} items in LEARNINGS.md
  - Suggested {N} new skills

Child projects that should merge from updated templates:
  - {list}
```
