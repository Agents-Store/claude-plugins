# LEARNINGS.md — dataforseo-dev

## 2026-10 — rewritten for dataforseo-mcp-server v3 (4 tools); v2 per-endpoint tools are gone

**Problem:** `.mcp.json` ran `dataforseo-mcp-server@latest`. Since 3.0.0 (2026-08-11) that is a full rewrite: the 76 per-endpoint tools of v2 were replaced by four (`docs_list_sections`, `docs_index`, `docs_search`, `api_request`). Every tool call in the plugin (about 105 references across 20 files) failed with "tool not found", and `@latest` would have moved the surface silently again.
**Fix:** Rewrote the plugin around the docs-first cycle. `.mcp.json` now pins `@3`. Every call is an `api_request` with a REST path and a body. The eight `mcp-patterns/references/*-tools.md` files became one table, `endpoint-paths.md` (task, path, minimal body). Commands list `api_request` and `docs_search` in `allowed-tools`; the agent lists the four tools explicitly instead of a wildcard. Added a `cost-awareness` skill: no `api_request` without a budget the user agreed, balance check through the free `GET /v3/appendix/user_data`.
**Root cause:** The plugin followed an unpinned `@latest` of a package that shipped a breaking major.
**Severity:** Critical

## 2026-10 — api-reference, setup, ai-optimization: wrong paths, bodies and prerequisites

**Problem:** Four paths did not exist: the AI Optimization endpoints had been filed under Content Analysis and the bulk keyword difficulty path lacked the `google` segment. Several bodies were wrong against the current docs: Labs `domain_intersection` takes `target1` and `target2` (the `targets` object is the Backlinks form), LLM Responses takes `user_prompt` and `model_name` (not `keyword` and `model`), `search_scope` is an array with its own value set per entity kind, and `search_intent` has no language field. The SERP locations lookup was shown as a POST. Setup said Node 20 and an account email and password.
**Fix:** Corrected every path against the DataForSEO v3 documentation index and every body against the endpoint pages. Node 22 or newer. Credentials are the API login and the generated API password (not the account password); `DATAFORSEO_USERNAME` stays in `.mcp.json` as an alias of `DATAFORSEO_LOGIN`, and both names are documented. The skills now cover Merchant, App Data and Business Data, the LLM Scraper, LLM Responses and the other LLM Mentions endpoints, and the `.ai` / `noAiMode` response modes.
**Root cause:** The REST paths and bodies were written from the v2 tool wrappers, not from the endpoint pages, and never re-checked against the docs index.
**Severity:** Major

## Open

- `DATAFORSEO_USERNAME` expansion in `.mcp.json` and a server start under `@3` are checked by the owner, not by the gate.
- The docs page for `/v3/on_page/lighthouse/live/json` returns 404 upstream although the docs index lists the path; field names come from the Lighthouse task page.
