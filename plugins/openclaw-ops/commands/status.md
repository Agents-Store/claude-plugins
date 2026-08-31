---
description: Daily fleet picture — one row per instance, with HEALTH and LIVENESS as two independent verdicts
argument-hint: "[selector] [--deep] [--json]"
allowed-tools: ["Bash", "Read", "Skill"]
---

# Fleet status

Read-only, always: no mutation, no restart, and never `models status --probe`, which needs a stopped
gateway and is a mutation wearing the word status. Parse `[selector] [--deep] [--json]` from
"$ARGUMENTS"; an empty selector means every managed instance. Selector grammar lives in `fleet-model`.

## Fast path — seconds, the one you run daily
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/fleet.py" resolve "<selector>" --table
```
Columns `NAME STATE PROFILE ROLE MANAGED PORT VERSION HEALTH LOG-AGE NOTE`. Here HEALTH is the
container's own verdict and LOG-AGE is the only liveness evidence available cheaply. A green HEALTH
beside a LOG-AGE of days is the zombie signature — that pair is the reason to run `--deep`, not a
rendering artefact to explain away.

## Deep path — `--deep`
```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/healthcheck.py" "<selector>" --table --snapshot
```
Several in-container reads per instance, so run it on purpose, not by reflex. `--snapshot` persists the
run (mode 0600) so the next one can show a delta. Exit codes: 0 clean · 5 at least one error finding ·
6 warnings only · 1/2/3/4 runtime, config, refused selector, empty selector.

## Reading the two verdicts
They are computed from disjoint evidence, and **the disagreement is the result**: HEALTH is what the
instance says about itself, LIVENESS what an outside observer sees it do. Which signal answers what, and
what each one is blind to, is the "Health is not liveness" table in the `fleet-diagnostics` skill.

`HEALTH ok` + `LIVENESS stale` is `fleet.liveness.zombie`. `HEALTH degraded` + `LIVENESS active` is a
subsystem down under a gateway still working — usually auth or memory. Both green with a `warn` finding
still means someone has to read the finding.

## Under every finding, print the repair line
The battery emits `{id, severity, instance, evidence}`, severity being one of `critical` `high`
`warn` `info` — the same four names the findings catalog uses. Print each non-info finding as one
line and put the ready-to-run funnel call directly beneath it:

```
/openclaw-ops:repair <instance> --issue <finding-id>
```

The id is the one the battery emitted. That funnel is the only repair entry point, and an id with no row
in `fleet-diagnostics/references/findings-catalog.md` is not repairable yet — it needs a catalog row with
its documentation citation first. Do not improvise a fix here, and never append `--yes` to a line you
just printed.

## `--json`
Pass `--json` straight through to whichever script ran and hand back the envelope unedited — it is
already scrubbed, and re-serialising it by hand is how a value leaks back in. Fields are the instance
record from `fleet-model`; findings carry the delta-stable `finding_id` (`<instance>/<id>`).

## When the table is not the answer
Symptom without an id → skill `fleet-diagnostics`. Whole-fleet sweep with priorities → `/openclaw-ops:audit`.
One instance's raw log → `/openclaw-ops:logs <name>`. Version drift across rows → skill `instance-upgrade`.
