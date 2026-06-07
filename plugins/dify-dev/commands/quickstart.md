---
description: Guided Dify API connect — find your app API key, set the base URL, send a first test call, verify the response
allowed-tools: ["Read", "Bash", "Skill", "AskUserQuestion"]
argument-hint: "[base-url]"
---

# Dify API Quickstart

Walk the user from zero to a verified first API call against their Dify app.

## Argument

- `$ARGUMENTS` — optional base URL (e.g. `https://api.dify.ai/v1` or `https://dify.example.com/v1`).
  If empty, ask whether they're on Dify Cloud or self-hosted.

## Process

### Step 1 — Base URL
Confirm the base URL. Cloud is `https://api.dify.ai/v1`; self-hosted is `https://{host}/v1`
(must end in `/v1`). If `$ARGUMENTS` was given, validate it ends with `/v1`.

### Step 2 — API key
Explain where to get the key, then ask the user to provide it (or to export it as an env var
so it isn't pasted into history):
- **App key** (`app-…`): Dify Studio → your app → **API Access** → **API Key**. Used for chat/completion/workflow.
- **Knowledge key** (`dataset-…`): Dify → **Knowledge** → **API**. Used for the Datasets API.

Recommend: `export DIFY_API_KEY=app-XXXX` and `export DIFY_BASE_URL=...`.

### Step 3 — Identify the app
Invoke the `setup` skill for context, then run `GET /info` and `GET /parameters` to learn the
app `mode` and required `inputs`:

```bash
curl -s "$DIFY_BASE_URL/info"       --header "Authorization: Bearer $DIFY_API_KEY"
curl -s "$DIFY_BASE_URL/parameters" --header "Authorization: Bearer $DIFY_API_KEY"
```

Report the app type (`chat`/`agent-chat`/`advanced-chat`/`workflow`/`completion`) and any
required input variables.

### Step 4 — First test call
Pick the call that matches the app `mode` and run it (use a stable `user`, e.g. `quickstart-user`):

- chat / agent / advanced-chat:
  ```bash
  curl -s -X POST "$DIFY_BASE_URL/chat-messages" \
    --header "Authorization: Bearer $DIFY_API_KEY" \
    --header 'Content-Type: application/json' \
    --data '{ "query": "Hello from quickstart", "inputs": {}, "response_mode": "blocking", "user": "quickstart-user" }'
  ```
- workflow: `POST /workflows/run` with the `inputs` from Step 3.
- completion: `POST /completion-messages` with the app's `inputs`.

### Step 5 — Verify & explain
- Success → show the `answer`/`outputs` and the captured `conversation_id`/`workflow_run_id`,
  and point to next skills (`chat-completion`, `workflows`, `conversations`, `knowledge-base`).
- Failure → route to the `troubleshoot` skill and map the status/`code` to a fix (401 key,
  404 user/base-url, 400 inputs, timeout → use streaming).

## Rules

- Never echo the full API key back; refer to it via the env var.
- Use only documented endpoints. All examples are curl.
- Prefer running the calls with the Bash tool only if the user has provided/exported a key;
  otherwise print the commands for them to run.
