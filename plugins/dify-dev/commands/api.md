---
description: Look up a Dify API endpoint — HTTP method, path, parameters, response shape, and a ready curl example
allowed-tools: ["Read", "Skill"]
argument-hint: "[endpoint-or-keyword]"
---

# Dify API Lookup

Look up one or more Dify API endpoints and return a precise, copy-paste-ready answer.

## Argument

- `$ARGUMENTS` — an endpoint path or a keyword. Examples: `chat-messages`, `run a workflow`,
  `upload file`, `retrieve`, `delete conversation`, `annotation reply`, `text-to-audio`,
  `create dataset`. If empty, list the endpoint groups and ask which one.

## Process

1. **Map the query to a skill** using this routing:
   - chat / message / completion / stop / suggested / feedback → `chat-completion`
   - workflow / run / logs / node events → `workflows`
   - conversation / history / variables → `conversations`
   - file / upload / audio / speech / tts / stt → `files-audio`
   - annotation → `annotations`
   - dataset / knowledge base / document / segment / chunk / retrieve / RAG → `knowledge-base`
   - auth / base url / user field / parameters / info / meta / site → `setup`
   - error / 401 / 404 / 429 / timeout / rate limit → `troubleshoot`

2. **Invoke the matching skill** with the Skill tool to load the authoritative reference, then
   (for the knowledge-base group) read the relevant file under
   `skills/knowledge-base/references/` for full parameter tables.

3. **Answer with**, for each matched endpoint:
   - **HTTP method + path** (relative to base URL `https://api.dify.ai/v1` or `https://{host}/v1`)
   - **Auth**: app key (`app-…`) or Knowledge key (`dataset-…`)
   - **Key parameters** (required vs optional, with the `user` field noted)
   - **Response shape** (concise JSON sketch)
   - **A ready curl example** with placeholder values

4. If the query is ambiguous or matches several endpoints, list the candidates briefly and
   show the most likely one in full.

## Rules

- Use only endpoints and shapes documented in this plugin's skills — never invent paths.
- All examples are **curl**. Show both the Cloud base URL and note the self-hosted variant
  when relevant.
- Keep it tight: method/path, params, response, one curl example. No filler.
