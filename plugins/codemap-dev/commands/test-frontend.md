---
description: Test a running app's frontend — navigate pages, check UI, find errors, generate report
argument-hint: [url] — e.g. localhost:3000, http://localhost:8080/admin
allowed-tools: [Read, Grep, Glob, Write, Bash, Agent, Skill]
---

# Frontend Testing

Test the frontend of a running application via Playwright MCP. Target: $ARGUMENTS

## Instructions

1. Read the primary skill:
   - `${CLAUDE_PLUGIN_ROOT}/skills/frontend-test/SKILL.md` — frontend testing methodology and report format

2. Parse `$ARGUMENTS` for the target URL:
   - If a URL is provided (e.g., `localhost:3000`, `http://localhost:8080/admin`) → pass it to the agent
   - If no argument → the agent will attempt to detect the dev server from project config (package.json, docker-compose, etc.), or ask the user

3. Launch the **frontend-tester** agent with the target URL and any additional context from the user's message (e.g., specific pages to test, credentials for auth, areas of concern).

The agent navigates the app via Playwright MCP, explores pages, tests interactions, checks console/network errors, takes screenshots, and generates a structured report at `docs/codemap/FRONTEND.md`.
