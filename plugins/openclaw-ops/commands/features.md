---
description: Read the release notes across a version range and report which newly added config keys and commands this fleet could adopt — per instance, with a recommendation, a risk class and a reason. Nothing is switched on.
argument-hint: "<selector> [--from <version>]"
allowed-tools: ["Bash", "Read", "Write", "Skill", "WebFetch", "WebSearch"]
---

# Features across a version range

Parse `<selector> [--from <version>]` from "$ARGUMENTS". Scripts live in
`${CLAUDE_PLUGIN_ROOT}/scripts/` and are named bare below. Read-only on the fleet: the only thing
written is the decision journal. Load the `instance-upgrade` and `docs-research` skills first —
this command carries the procedure, they carry the knowledge.

## Process

1. **Targets and range.** `fleet.py resolve "<selector>" --table`, then
   `versions.py "<selector>" --json`. `--from` defaults to the **lowest** installed version in the
   selection; the upper bound is the accepted target from the soak gate, else the highest installed
   version. Every version string you print must be an echo from that output or from a fetched
   release page — never from memory.
2. **Fetch the notes** for each release in the range (`docs-research` fetch ladder; quote the URL
   per entry). A release whose notes could not be fetched is listed as `unreviewed`, never inferred
   from its version number.
3. **Keep only decidable entries** — a release note earns a row only if it adds a **config key** or a
   **command, subcommand or flag**. Fixes, internals and performance work are not decisions and are
   dropped. This is the whole filter; without it the table is a changelog nobody reads.
4. **Free second source:** `ocexec.py <inst> --json -- doctor --lint` after an upgrade usually names
   the deprecated form of something that has a newer one. Fold those findings in as candidates.
5. **Classify each entry against the real config**, per instance, reading it with
   `ocexec.py <inst> --json -- config get <path>` (R0):
   - `already-on` — the key exists and is set
   - `available-off` — supported by this version, absent from the config
   - `not-applicable` — the feature addresses something this instance does not do; say what
   - `unsupported-here` — the instance is older than the release that added it; the row is an
     upgrade argument, not a config change
6. **Render the table:** `FEATURE | ADDS | INSTANCE | STATE | RECOMMEND | RISK | SOURCE`. Risk is a
   class from `gate.RISK_CLASSES`, not an adjective. `SOURCE` is the URL.
7. **Journal the decisions** in `<state-root>/openclaw-ops/features/decisions.json` (mode 0600,
   beside the health snapshots; `policy.snapshot_dir` moves the root). Read it **before** step 6 —
   anything already declined is rendered as `declined <date>` and is not re-proposed — and append to
   it after the operator answers: one record per feature with id, version, decision
   (`adopted` / `declined` / `deferred`), date and a one-line reason. The next upgrade must not
   re-litigate what was already settled.

## Rules

- **Nothing is enabled here.** A row recommended for adoption is handed on: a finding id goes to
  `/openclaw-ops:repair <inst> --issue <id>`, anything else to the `config-surgery` skill in its own
  turn with its own plan and its own `--yes`.
- **No live source, no recommendation.** With neither the network nor the CLI reachable, report the
  observed config state and stop (`docs-research` unverified-knowledge mode).
- Model ids and version numbers appear only as echoes from the box or the fetched page.
- Never pass `--fix`; never run anything above R0 from this command.

## Example

```
/openclaw-ops:features managed
/openclaw-ops:features @reference --from <version-installed-before-the-last-upgrade>
```
