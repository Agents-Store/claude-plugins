# Learnings

Capture non-obvious discoveries, gotchas, and pattern refinements that surface while working with this stack. Add entries as you go — future-you will thank you.

## 2026-09-30 — Trigger.dev MCP authenticates with TRIGGER_ACCESS_TOKEN, not TRIGGER_SECRET_KEY

**Context**: checking every credential of the test workspace against the Trigger.dev docs
**What happened**: `.mcp.json` fed `TRIGGER_SECRET_KEY` to the MCP server as `TRIGGER_ACCESS_TOKEN`. An environment key (`tr_dev_…`) gets 401 from the account-level tools (`whoami`, `list_projects`), so the README told people to put a PAT into `TRIGGER_SECRET_KEY` — which then no longer matched the name the SDK and the docs give that variable.
**Root cause**: one variable was made to carry two different credentials.
**Fix**: the MCP server reads `TRIGGER_ACCESS_TOKEN` (a PAT); `TRIGGER_SECRET_KEY` is only the environment key again. README, `.env.example` and `init-project` list both. Major bump — an existing project must add `TRIGGER_ACCESS_TOKEN` or the MCP server starts unauthenticated.
**Lesson**: a PAT and an environment key are different credentials; give each its documented name.

## Format

```
## YYYY-MM-DD — Short title

**Context**: what you were trying to do
**What happened**: the unexpected behavior or error
**Root cause**: what was actually going on
**Fix**: what you did
**Lesson**: the generalizable takeaway
```
