---
description: The only repair funnel — dispatch one catalog finding id through its eight-block plan, apply on a later turn, verify
argument-hint: "<selector> --issue <finding-id> [--all-findings] [--yes]"
allowed-tools: ["Bash", "Read", "Edit", "Skill"]
---

# OpenClaw repair

Parse `<selector>`, `--issue <finding-id>`, `[--all-findings]`, `[--yes]` from "$ARGUMENTS".

Every fix enters here: a repair exists only as a row in `findings-catalog.md` carrying an id, severity,
detection, fix, verification and risk class. An unknown symptom gets a catalog entry — with its
documentation citation — first, and a fix second.

## Process

1. **Resolve the id to a row** — `Skill` `fleet-diagnostics`, then `references/findings-catalog.md`. Id
   forms: `fleet.*` catalog ids · upstream `checkId`s (`fs.*`, `gateway.*`, `tools.exec.*`, `plugins.*`,
   `security.exposure.*`) verbatim from the live `--json` · `<instance>/<check-id>`. **No row → stop.**

2. **Resolve the targets as a mutation**:
   ```bash
   python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fleet.py" resolve "<selector>" --mutation --table
   ```
   Exit 3 refuses an empty selector, `all`, an alien instance or `manage:false`, with the reason per
   name; a legacy layout is refused too (red line `legacy-instance-mutation`).

3. **Load the skill that owns the family** — auth → `provider-auth`; config and model chain →
   `config-surgery`; memory → `memory-ops`; secrets → `secrets-infisical`; shared assets → `shared-assets`;
   exposure → `security-audit`. Upgrades belong to `/openclaw-ops:update`, never here.

4. **Re-detect before repairing** — run the row's detect step now through
   `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ocexec.py" <instance> --json -- <args>`. A finding that no longer reproduces is resolved, not repaired.

5. **Build the plan** at the row's risk class (`gate.make_plan`) with all eight blocks —
   **TARGET · PRECHECK · CHANGE · BACKUP · IMPACT · VALIDATE · ROLLBACK · APPLY** (plus
   **IRREVERSIBLE · CONFIRM** for R3/R4). Block contents belong to their owners: the eight-block contract
   to `fleet-model`, the deletion count and the `.bak`-ring snapshot rule to `config-surgery`. ROLLBACK is
   executable, prose does not validate, and anything replacing an executable artefact pins first (`gate.pin`):
   `cp <snapshot-path> <config-path> && python3 "${CLAUDE_PLUGIN_ROOT}/scripts/ocexec.py" <instance> --yes --plan-id <plan-id> -- gateway restart`.

6. **Show the plan and stop.** Mint its id (`scripts/lib/gate.py plan mint repair <instance> --risk <R>`)
   and print it with the plan: the applying `ocexec.py` call passes it as `--plan-id`, the door checks it
   against the registry and **burns it** — one plan, one mutation, so a rollback needs its own id.
   `--yes` belongs to a later turn; R4 also needs the typed phrase from `gate.confirm_phrase`.

7. **Apply, then verify** with the row's verify command — one whose result differs before and after;
   "looks fine now" is not one. Re-run detect: it must come back empty, and zero-retry families
   (`gate.retry_policy`) stop on the **first** failure.

## `--all-findings`

Batch over every open finding. Broken → attempted-repair, so the policy is **continue-and-report**
(`gate.batch_policy`): one row per instance and finding — `repaired` / `failed` / `refused` — and the
batch finishes. R3/R4 rows leave for their own plan; a healthy-instance batch is fail-fast behind the canary.

## Never

Improvise a fix for an id with no row · pass `--accept-capabilities`, printed for a human · run the automatic repair
flags of lint or security audit by default (red line `doctor-fix-or-security-fix`) · restart a zombie instead of triaging it.
