---
description: Scaffold a new Microsoft Teams bot, tab, AI agent, or Graph app with the Teams Developer CLI
argument-hint: <project-name> [template?]
allowed-tools: ["Bash", "Read", "Write", "Edit", "Skill"]
---

# /teams-dev:scaffold

Bootstraps a new Microsoft Teams application in the current working directory using `@microsoft/teams.cli`. Args:

- `$ARG1` — project folder name (required), e.g. `quote-agent`
- `$ARG2` — template (optional, default `echo`). Allowed: `echo`, `ai`, `graph`, `tab`.

## Steps

1. Invoke `Skill: setup` to confirm Node 18+ and a Teams developer account.
2. If `teams --version` fails, run `npm i -g @microsoft/teams.cli@preview`.
3. Run `teams project new typescript "$ARG1" --template "${ARG2:-echo}"`.
4. Cd into the new directory and `npm install`.
5. Open `src/index.ts`, `appPackage/manifest.json`, and `.env` to confirm scaffolding.
6. Read `Skill: getting-started` for next steps (run `npm run dev`, set up a devtunnel, sideload into Teams).

## Notes

- Template `echo` is the simplest message-echo bot; pick it unless the user asked otherwise.
- Template `ai` wires up `@microsoft/teams.ai` with a `ChatPrompt` + `OpenAIChatModel` — needs `OPENAI_API_KEY` in `.env`.
- Template `graph` wires up `api.graph` calls with user-token auth — needs SSO setup; route through `Skill: authentication` before testing.
- Template `tab` scaffolds a static-hosted React tab — pair with `Skill: tabs` for client-side SDK usage.
- Do not commit `.env` or `appPackage/manifest.json` rewrites that contain real `botId` values.
