---
description: Guided discovery session to understand goals, users, tasks, and success criteria for OpenClaw workspace customization
allowed-tools: ["Read", "Write", "Edit", "Bash", "Glob", "Grep"]
argument-hint: "[new|existing]"
---

# Workspace Interview

Conduct a guided discovery session to understand what the OpenClaw workspace needs to achieve. CWD is the instance root (`~/.openclaw-{name}/`).

**Note**: The interview conversation can be in the user's preferred language. However, all generated workspace files and the workspace brief MUST be written in English.

## Process

### Step 1: Check current state
Before interviewing, scan the workspace to understand what already exists:
```bash
for f in AGENTS.md SOUL.md USER.md IDENTITY.md TOOLS.md HEARTBEAT.md MEMORY.md; do
  [ -f "./workspace/$f" ] && echo "EXISTS: $f ($(wc -w < "./workspace/$f") words)" || echo "MISSING: $f"
done
```

Also check `./openclaw.json` for existing channel and model configuration.

### Step 2: Interview — 7 question areas

Ask these questions conversationally, not as a rigid form. Adapt based on answers. Ask 2-3 at a time, not all at once.

**Area 1: Goals & Purpose**
- What is this OpenClaw agent for? (personal assistant, team tool, customer-facing, internal ops?)
- What's the single most important thing it should do well?
- What would success look like in 30 days?

**Area 2: Users**
- Who will interact with this agent? (one person, a team, clients?)
- What are their roles? (developer, manager, lawyer, etc.)
- What languages do they communicate in?
- What timezone(s)?

**Area 3: Regular Tasks**
- What tasks are assigned to the agent most often?
- Are there recurring/scheduled tasks?
- How complex are typical requests? (simple Q&A, multi-step workflows, research?)

**Area 4: Channels**
- Which platforms will the agent use? (Telegram, Discord, WhatsApp, web, iMessage?)
- Are there group chats? How should the agent behave in them?
- Should the agent be proactive (initiate messages) or reactive only?

**Area 5: Tools & Skills**
- What tools/skills does the agent need? (search, code, email, calendar, home automation?)
- Are there domain-specific tools? (legal databases, analytics platforms, CRM?)
- Any tools that should be prioritized or avoided?

**Area 6: Success Criteria**
- How will you know the agent is doing well?
- What are the must-not-fail scenarios?
- What are the red lines? (things the agent must never do)

**Area 7: Pain Points**
- If you already have a workspace: what's not working?
- What does the agent get wrong most often?
- What do you wish it would do differently?

### Step 3: Compile brief

After gathering all answers, create a structured brief **in English**:

```markdown
# Workspace Configuration Brief

## Instance Purpose
[Summary of goals and primary function]

## Users
| Name | Role | Language | Timezone | Permissions |
|------|------|----------|----------|-------------|
| ... | ... | ... | ... | ... |

## Primary Tasks
1. [Most important task]
2. [Second priority]
3. [Third priority]

## Channels
- [Channel 1]: [configuration needs]
- [Channel 2]: [configuration needs]

## Tools & Skills
- Priority: [tools to emphasize]
- Avoid: [tools to restrict or not use]

## Success Criteria
- [Metric 1]
- [Metric 2]

## Red Lines
- [Must never do 1]
- [Must never do 2]

## Pain Points (if existing workspace)
- [Issue 1]
- [Issue 2]

## Recommended Scenario Template
Based on this profile, closest match: [legal-firm / dev-team / personal-assistant / marketing-agency / customer-support / content-creator]
```

### Step 4: Present brief and next steps

Show the compiled brief to the user and suggest next steps:

1. Save brief to workspace as `./workspace/docs/workspace-brief.md`
2. Run `/workspace-optimize all` to generate all workspace files based on this brief
3. Or optimize specific files: `/workspace-optimize soul`, `/workspace-optimize agents`, etc.
4. Run `/config-validate` to check openclaw.json
5. After all edits: fix Docker permissions

Ask for approval before saving.
