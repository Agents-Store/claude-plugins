---
description: Generate copy-paste curl scripts for a Dify operation (chat, completion, workflow, file upload, knowledge-base ingest/retrieve)
allowed-tools: ["Read", "Write", "Skill", "AskUserQuestion"]
argument-hint: "[operation]"
---

# Generate Dify curl Client

Generate a ready-to-run **curl** script for a chosen Dify operation, with placeholders for
the base URL and API key.

## Argument

- `$ARGUMENTS` — optional operation hint (e.g. `chat`, `completion`, `workflow`,
  `file upload`, `kb ingest`, `kb retrieve`). If empty, ask which operation to scaffold.

## Process

1. **Determine the operation.** If `$ARGUMENTS` is empty or ambiguous, use AskUserQuestion to
   choose among: Chat message · Completion · Run workflow · Upload file → chat · Knowledge
   base ingest · Knowledge base retrieve.

2. **Confirm a few inputs** (AskUserQuestion or sensible defaults):
   - Deployment: Cloud (`https://api.dify.ai/v1`) or self-hosted (`https://{host}/v1`)
   - Response mode where applicable: `streaming` or `blocking`
   - Whether to emit a single curl command or a small multi-step `.sh` script

3. **Load the authoritative request shape** by invoking the matching skill with the Skill
   tool (`chat-completion`, `workflows`, `files-audio`, or `knowledge-base`). Use only
   documented parameters.

4. **Generate the script** using shell variables for secrets, e.g.:
   ```bash
   #!/usr/bin/env bash
   set -euo pipefail
   BASE="${DIFY_BASE_URL:-https://api.dify.ai/v1}"
   KEY="${DIFY_API_KEY:?set DIFY_API_KEY}"   # app-… (or dataset-… for knowledge base)
   USER="${DIFY_USER:-user-123}"
   # ... curl call(s) ...
   ```
   - Use the app key (`app-…`) for Service API ops, the Knowledge key (`dataset-…`) for KB ops.
   - Always include the `user` field where the endpoint requires it.
   - Add `-N` for streaming calls and a short comment on which SSE events to expect.
   - For multi-step flows (e.g. KB ingest → poll indexing → retrieve), chain the calls and
     capture ids with `jq` where helpful.

5. **Output** the script in a fenced block. If the user asked to save it, Write it to a path
   they specify (default: `./dify-<operation>.sh`) and remind them to `chmod +x`.

## Rules

- **curl only.** No language SDKs.
- Never hardcode real keys — read from env vars and show the export commands.
- Only use endpoints/parameters documented in this plugin's skills.
