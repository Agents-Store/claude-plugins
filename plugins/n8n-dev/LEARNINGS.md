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
