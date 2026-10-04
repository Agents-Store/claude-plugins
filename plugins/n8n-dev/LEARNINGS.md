# LEARNINGS.md — n8n-dev

Accumulated fixes and discoveries for the n8n-dev plugin.

## 2026-04-08 — n8n-native-mcp: @builderHint model defaults ignored

**Problem:** When creating an AI workflow with OpenAI Chat Model node, `gpt-4o` was used despite `get_node_types` returning `@builderHint Always default to latest mini model gpt-5-mini`. GPT-4o was retired in Feb 2026.
**Fix:** Added guidance in Step 4 (Write Code) to explicitly follow `@builderHint` annotations from type definitions for model selection and other defaults.
**Root cause:** The skill didn't emphasize that `@builderHint` is actionable guidance, not just documentation.
**Severity:** Major

## 2026-04-08 — n8n-native-mcp: IF node conditions.options metadata missing

**Problem:** Workflows created via native MCP `create_workflow_from_code` with IF/Switch nodes lacked `conditions.options` metadata. The workflow saved successfully but failed validation when later updated via external MCP (`n8n_update_partial_workflow`), blocking credential assignment and other edits.
**Fix:** Added "IF / Switch Node Metadata" section to Best Practices with correct `conditions.options` structure and unary operator `singleValue: true` guidance.
**Root cause:** The native MCP SDK doesn't auto-generate the metadata that n8n UI adds automatically. The skill had no guidance on this required structure.
**Severity:** Major

## 2026-04-08 — n8n-mcp-tools-expert: Credential assignment to workflow nodes undocumented

**Problem:** After creating credentials via `n8n_manage_credentials`, there was no documented pattern for assigning them to workflow nodes. The user had to discover the `updateNode` operation format by trial and error.
**Fix:** Added "Assigning Credentials to Workflow Nodes" subsection to Credential Management with a complete create → assign example using `n8n_update_partial_workflow`.
**Root cause:** The credential and workflow management sections were documented independently with no cross-reference for the most common combined workflow.
**Severity:** Minor

## 2026-09-30 — api-reference, troubleshoot, setup: `/api/v1` appended twice

**Problem:** Every curl recipe built `$N8N_API_URL/api/v1/...`, but the workspace catalogue (and `n8n-mcp` itself) stores `N8N_API_URL` with `/api/v1` already on the end, so each recipe hit `/api/v1/api/v1/...` and got 404. The native-MCP snippets had the same flaw: `${N8N_API_URL}/mcp-server/http`.
**Fix:** The skills derive `N8N_BASE` once (`${N8N_API_URL%/}`, then strip `/api/v1`) and build every path from it — root, root with `/`, and `…/api/v1` all return 200. The native-MCP snippets now read `${N8N_NATIVE_MCP_URL}`, since `.mcp.json` cannot strip a suffix.
**Root cause:** The skills were written for a root URL; `n8n-mcp` normalizes both forms, so the external MCP never exposed the mismatch.
**Severity:** Major — every documented REST call failed against the workspace's own `.env`.

## 2026-10-03 — core skills: hybrid sync with czlonkowski/n8n-skills

**Problem:** The seven core skills had been adapted by hand from n8n-skills in April and then drifted: the Python skill still described the Pyodide runtime removed in n8n 2.0 (188 hits), `$env` appeared as a normal way to pass secrets, the layout (`references/` subfolders) differed from upstream, and seven upstream skills (agents, error handling, sub-workflows, binary data, Code tool, multi-instance, self-hosting) were missing.
**Fix:** Added `scripts/sync-n8n-skills.sh` and `.github/workflows/sync-n8n-skills.yml`. Every upstream skill directory is mirrored verbatim except the six local ones (`n8n-native-mcp`, `api-reference`, `cli-recipes`, `setup`, `troubleshoot`, `examples`). First run: v1.35.0 (`19cd793`) — 15 skills, flat layout, `LICENSE-n8n-skills`. That includes the upstream router `using-n8n-mcp-skills`, which was not on the list of expected skills. The scrub findings in the verbatim files (compose service names, `REPLACE_WITH_*` placeholders in env templates, `url.host`) are baselined by value digest in their own commit, never edited in place.
**Root cause:** A hand-adapted copy cannot follow an upstream that ships a release every few weeks, and a vendored file edited locally is overwritten by the next sync.
**Severity:** Major

## 2026-10-03 — n8n-native-mcp, setup, troubleshoot, api-reference, cli-recipes, examples, agent: n8n 2.x semantics and the live native tool surface

**Problem:** The native MCP guide documented a 16-tool surface under names and schemas that no longer exist: the SDK reference tool and the execution reader were renamed in n8n 2.34, the node-suggestion tool was removed (replaced by `get_workflow_best_practices`), `get_node_types` takes `nodeId` objects (not `id`), `update_workflow` takes an atomic operation list (not SDK code), `execute_workflow` takes `executionMode` and `inputs` (not `mode` / `inputData`). The server has 54 tools; agents, data tables, version history, folders and pin-data tests were undocumented. `n8n-developer` listed `tools:` without any MCP tool, so the agent could not call the servers it documents. The CLI recipes used the deprecated `update:workflow`, the API reference the deprecated `activate`/`deactivate` routes and a 37-endpoint count that contradicted the bundled spec (60 operations), the setup skill sent users to a "Create MCP Token" screen that is now Settings > Instance-level MCP > Connect.
**Fix:** `n8n-native-mcp` rewritten against the live tool schemas (all 54 tools grouped; access and "Available in MCP" gating; first-class Agents flow; minimum n8n versions). `setup`: 28 external / 54 native tools, `N8N_MCP_ACCESS_TOKEN`, OAuth path, version table, health-check shape. `api-reference`: publish/unpublish, archive, history, `publishIfActive`, data-table columns and folders documented (the spec behind it was refreshed in the next entry). `cli-recipes`: `publish:workflow` / `unpublish:workflow`, `--published` / `--version` / `--activeState`, no `mysqldb`, the npm-install warning for n8n 3.0, `@n8n/cli`. `troubleshoot` and the example scenarios: short node-type form for `get_node`, current `typeVersion` values, model names only inside an `example-only` block, publish wording. `n8n-developer`: `tools:` removed so it inherits all tools.
**Root cause:** The skills were written against n8n 1.x / early 2.x behaviour and never re-checked against the live server.
**Severity:** Major — documented calls failed against a current instance.

## 2026-10-03 — pending upstream: items to send to czlonkowski/n8n-skills

These are defects or gaps in the **vendored** files. They are not fixed here (the next sync would overwrite a local edit). Nothing has been filed upstream yet.

- **Credential assignment worked example (carried over from the 2026-04-08 entry).** v1.35.0 shows the nested-by-type form (`updates: {credentials: {httpHeaderAuth: {id, name}}}`, `n8n-mcp-tools-expert/SKILL.md`) but not the create-then-assign sequence with `n8n_manage_credentials` followed by `n8n_update_partial_workflow` `updateNode`, nor the note that the key in `updates.credentials` must equal the credential type the node expects. Still correct for n8n 2.x.
- **`$env` documented as a normal way to pass values.** n8n 2.0 blocks `$env` in expressions and Code nodes by default (`N8N_BLOCK_ENV_ACCESS_IN_NODE=true`). `n8n-expression-syntax/SKILL.md` (the `$env` section), `EXAMPLES.md`, `COMMON_MISTAKES.md`, `n8n-workflow-patterns/webhook_processing.md` and `http_api_integration.md` still show `{{$env.…}}` as a working pattern, and `n8n-code-javascript/BUILTIN_FUNCTIONS.md` calls the block "a common production hardening". Suggest: say "blocked by default since n8n 2.0, opt-in", and use credentials or `$vars` in the examples.
- **`n8n-validation-expert/FALSE_POSITIVES.md`** uses `n8n-nodes-base.cron`; the Cron and Interval nodes are removed in n8n 3.0 — `n8n-nodes-base.scheduleTrigger`.
- **`PUBLISH_FORBIDDEN` (n8n 2.39+)** is not mentioned in `n8n-mcp-tools-expert`: editing a published workflow needs the `workflow:publish` permission (and `workflow:activate` scope), otherwise `n8n_update_partial_workflow` fails with that code and may roll back.
- **Minor:** `n8n-mcp-tools-expert` quotes "2,700+ templates" while the n8n-mcp README says 2,352 (do not hard-code), and `WORKFLOW_GUIDE.md` counts 19 diff operations while the live tool lists 21.

## 2026-10-03 — api-reference: OpenAPI spec regenerated from the n8n 2.41.6 sources

**Problem:** `references/n8n-api.json` was a v1.1.1 snapshot with 60 operations (11 tags): no publish/unpublish, archive, history, folders, evaluations, roles or data-table columns, and `activate`/`deactivate` as the only way to change the published state. The skill text had to carry a hand-written "Changes in n8n 2.x" section for everything the spec lacked.
**Fix:** Sparse checkout of `packages/cli/src/public-api` from n8n-io/n8n at tag `n8n@2.41.6`, `npx @redocly/cli bundle` on both entry files (`openapi.yml`, 57 operations; `openapi.decorator-routes.generated.yml`, 97 operations; only the two folder paths appear in both, with different methods), merge of `paths` and `components` (no schema collisions) into one document: 154 operations, 26 tags, sorted paths, upstream `servers` (relative `/api/v1` and `{url}/api/v1` with the `example.com` default), `info.x-bundled-from` records the source. The skill's tag tables are generated from it and carry each operation's `x-required-scope`. The two vendor-example rules the old file already tripped (`uuid`, `high-entropy`) are covered by the existing file-wide baseline lines; no new baseline line was needed.
**Root cause:** The old file had been taken from an older playground and never refreshed; the real spec is split over two entry files, so it looked like only one of them could be bundled.
**Severity:** Major — the documented surface did not match a current instance.

## 2026-10-03 — examples: record-driven workflow sketches moved in from `stack-composable-stack-v1`

**Problem:** The stack plugin's `background-job` skill carried three n8n workflow sketches (scheduled sync, webhook processing, error recovery) next to its Trigger.dev code. They are n8n content, but `n8n-workflow-patterns` cannot take them: it is vendored from `czlonkowski/n8n-skills` and overwritten by `scripts/sync-n8n-skills.sh`. The sketches also said "Retry Original Workflow" without a way to do it, and the stack's PostgREST text read `{{ $env.… }}` in an expression, which n8n 2.x blocks by default.
**Fix:** New local file `skills/examples/references/background-processing-patterns.md` (`examples` is one of the six local skills in the sync script's LOCAL list), linked from `examples/SKILL.md` as scenario 4. The error-recovery sketch retries through `POST /executions/{executionId}/retry` (present in the bundled 2.41.6 API reference, with `loadWorkflow`), and the credentials section says to use credentials and fixed URLs instead of `$env`. No vendored file was touched.
**Root cause:** Content about one tool lived in the stack plugin because no local, sync-safe place for n8n workflow sketches existed.
**Severity:** Minor

## 2026-10-04 — plugin-test L1: fence labels and one link fixed in vendored files (pending upstream)

**Problem:** The L1 runner (`skill-snippets`, `skill-links`) flagged 13 spots: 11 ```json fences that are not strict JSON (several `connections` fragments without braces, `// comments`, `[...]`) in `api-reference` (local) and `n8n-agents`, `n8n-error-handling`, `n8n-workflow-patterns` (vendored); the queue-mode compose fragment in `n8n-self-hosting/TASK_RUNNERS.md` that uses the `*n8n` anchor from `assets/docker-compose.queue.yml`; and the link `../../n8n-expression-syntax/SKILL.md` in `n8n-workflow-patterns/webhook_processing.md`, which pointed outside the skill tree.
**Fix:** Fences relabelled ```jsonc (label only, text untouched); a `<!-- plugin-test: skip -->` marker with a reason comment above the compose fragment; the link is now `../n8n-expression-syntax/SKILL.md`. The edits in the vendored directories are local: the next `scripts/sync-n8n-skills.sh` run overwrites them, so send them upstream (czlonkowski/n8n-skills) or re-apply them after that sync (`python3 scripts/plugin_test.py --plugin n8n-dev --check skill-snippets --check skill-links` lists what returns).
**Root cause:** The upstream skills label pseudo-JSON as ```json and use a relative link that is valid only from the skill's parent directory.
**Severity:** Minor
