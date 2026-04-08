---
description: Manage custom properties on Plane work items (severity, customer impact, etc.)
argument-hint: <action> <project> [args...]
---

# Property

Define and manage custom properties on work items. Properties are typed fields beyond the built-ins (state, priority, points). Examples: severity, customer impact, environment, root cause.

## Arguments

Format: `<action> <project> [args...]`

- `action`: `list` | `create` | `update` | `delete` | `get`
- `project`: project name or identifier
- For `create`: `--name`, `--type <text|number|select|multi-select|date|boolean|user|url>`, `--required`, `--type-id <work_item_type_id>` (scope to a specific work item type), `--options "a,b,c"` (for select)
- For `update`: same flags

Parse from `"$ARGUMENTS"`.

## Process

1. **Bootstrap connector** — consult `connector-bootstrap`. Probe for `list_work_item_properties`, `create_work_item_property`, `update_work_item_property`, `delete_work_item_property`, `retrieve_work_item_property`.
2. **Resolve project** → `project_id`. If `--type-id` not given, resolve work item type by name.
3. **Route**:
   - `list` → render: name | data type | scope (type) | required? | option count
   - `create` → for `select`/`multi-select`, parse options. Call `create_work_item_property`.
   - `update` → resolve by name. **Changing data type breaks existing values** — warn loudly.
   - `delete` → confirm. Existing values are dropped.
   - `get` → details + sample of items that have this property set.
4. **Confirm** — re-list.

## Property design rules

- **Use a property when**: data is structured, queryable, and reportable (severity, environment, customer).
- **Use a label when**: data is freeform tagging, optional, no values needed (`needs-design`, `flaky`).
- **Use a work item type when**: the workflow itself differs (Bug vs Spike).

Three buckets, three tools — don't mix. See `labels-states-properties` skill.

## Examples

```
/property list "TaskFlow"
/property create "TaskFlow" --name severity --type select --options "S0,S1,S2,S3" --required
/property create "TaskFlow" --name "customer impact" --type number
/property create "TaskFlow" --name environment --type select --options "prod,staging,dev"
/property update "TaskFlow" severity --required false
/property delete "TaskFlow" "old field"
```
