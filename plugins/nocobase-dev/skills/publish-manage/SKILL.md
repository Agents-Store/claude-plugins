---
name: publish-manage
description: |
  Risk-gated cross-environment publishing for NocoBase — backup+restore, schema migration, selective publish templates (schema_only_all, full_overwrite, etc.), precheck gates. Opt-in and **destructive by nature** — do not invoke without explicit user confirmation. Use when the user asks to:
  - "publish NocoBase to staging/production"
  - "migrate NocoBase data between environments"
  - "backup and restore NocoBase app"
  - "copy a NocoBase app to another env"
  - "promote changes to production"
  - "NocoBase publish template"
  - "schema_only_all vs full_overwrite"
disable-model-invocation: true
---

# Publish Manage

Cross-environment publishing for NocoBase apps — moving data, schema, and config between dev/staging/prod instances. This is a **high-risk surface**: every operation can destroy data if misconfigured. This skill is `disable-model-invocation: true` — it activates only when the user explicitly names a publishing task.

## Hard rules

1. **Never publish without explicit user confirmation.** Always show the planned operation (method, template, source env, target env, estimated changes) and pause for a yes/no before executing.
2. **Back up first.** Any target env must have a verified backup before a publish operation runs. If the backup fails, abort.
3. **Never run `full_overwrite` against production** without a fresh target-env backup < 15 minutes old.
4. **Know the method:** `backup_restore` (snapshot-and-apply) and `migration` (forward-only migrations) are different mental models. Mixing them in one pipeline is an incident in waiting.
5. **Dry-run when the tool supports it.** Prefer a precheck/diff step before the mutating call.
6. **Publish templates are user-configurable:** `schema_only_all`, `data_only_selected`, `full_overwrite`, plus custom. The template chooses WHAT moves; the method chooses HOW.

## Methods

### Backup + Restore
Snapshot the source env's DB and file storage, restore on the target. Overwrites target completely.

- Use when: source and target are same major version; target is disposable (e.g., staging reset from prod); you want absolute fidelity.
- Avoid when: target has user-generated content you cannot lose; envs are on different versions.

### Migration
Forward-only SQL/schema migrations applied to target. Preserves target data; adds schema changes from source.

- Use when: target has data you need to preserve (production); you want auditable schema history; envs are on different versions.
- Avoid when: you also need to move all data; schema drift is extreme (requires manual reconciliation).

## Publish templates

Selective manifests that control what parts of the app move.

| Template | What moves | Use for |
|----------|-----------|---------|
| `schema_only_all` | All collections' schemas, flow models, UI schemas, routes, menus | Dev → Staging schema sync |
| `data_only_selected` | Records for a named list of collections | Copying reference data |
| `full_overwrite` | Everything (schema + data + files) | Disposable-target reset |
| `code_plugins_only` | Enabled plugin list (no data) | Plugin state alignment |
| *custom* | User-defined manifest | Targeted cherry-picks |

## Precheck gates

Before ANY publish operation, confirm the operator has checked:

1. **Source env health:** `auth_check` + `collections_list_meta` both succeed.
2. **Target env health:** same checks on target.
3. **Target backup:** verified, timestamped, restorable — the fire-insurance.
4. **Version parity:** major versions match (for `backup_restore`) or migrations are present and tested (for `migration`).
5. **Active users on target:** if production, coordinate a maintenance window.
6. **Plugin parity:** plugins enabled on source are also available on target (or explicitly excluded from the template).
7. **External dependencies:** per-env config (SMTP, storage, data-sources) does not get overwritten accidentally.

## Reference files

- `references/intent-routing.md` — upstream routing: which user intent maps to which publish op
- `references/v1-runtime-contract.md` — runtime contract and error signatures
- `references/test-playbook.md` — verification checklist after a publish
- `references/SKILL-upstream.md` — upstream skill content verbatim

## Transport

Upstream tooling is CLI-first: `nocobase-ctl publish ...`. Not all publish operations have MCP equivalents — fall back to CLI and, if necessary, raw SQL via server access. See `references/SKILL-upstream.md` for the full command surface.

## See also

- `plugin-development` — plugin state matters: `pm list` on both envs before publishing
- `data-modeling` — schema changes you are publishing should be designed, not forced
- `auth-and-users` — per-env credentials matter; do NOT publish the user table across envs
- `system-admin` — app info, plugin list, storage config
- `troubleshoot` — recovery from partial publish failures
