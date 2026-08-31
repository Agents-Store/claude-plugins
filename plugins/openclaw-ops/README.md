# openclaw-ops

Day-two operations for a **fleet of self-hosted OpenClaw gateways** running as Docker Compose projects
on one host. Inventory, health versus liveness, provider-credential triage, config surgery, secret
delivery, memory and embeddings, shared skills and plugins, version drift and upgrades, security
exposure, and cloning the reference instance.

The plugin knows the **shape** of this deployment class and the **procedures**. It never ships your
fleet's names, paths, ports or versions: instances are discovered from live Docker state on every run,
and the handful of decisions discovery cannot make live in an operator-owned config file outside this
repository.

**Technology-level plugin: no MCP server, no required environment variables, no stored credentials.**
Everything is file-based knowledge plus stdlib Python scripts. One optional variable exists —
`OPENCLAW_OPS_CONFIG`, the first rung of the config ladder — as an escape hatch for pointing a run at a
specific fleet config; unset, the ladder resolves the file on its own.

Replaces `openclaw-configurator` for fleet operations; that plugin remains, deprecated, for
single-instance workspace and persona content.

## Execution model

Claude Code runs **on the host that serves the gateways**. There is no SSH layer, no API, no agent
inside the container.

| | |
|---|---|
| Discovery | `docker compose ls --all` → projects by prefix → gateway container by label → `docker inspect` for mounts, published port, health, restart count. Paths come from the live mount table, never from constants |
| The one door | every OpenClaw CLI call goes through `scripts/ocexec.py`. A hand-written `docker exec` bypasses redaction, the risk classification, the standing bans, and the `-T` that `--json` depends on |
| hot mode | `compose exec -T` into the gateway through the secret-injection wrapper — the normal path; secrets never leave the container |
| cold mode | a one-off container over the state directory, only while the instance is **down**, only for the subcommands that are safe on a broken instance |
| Metrics and tokens | scraped from **inside** the container, so the operator bearer never crosses the host boundary |

## Requirements

| | |
|---|---|
| Where it runs | a shell on the host itself, with permission on the Docker socket |
| Docker | Engine with Compose v2 (`docker compose`), projects discoverable via `compose ls --all` |
| Python | `python3`, **stdlib only** — no `jq`, no Node, nothing to install |
| Network | optional, and only for release channels and documentation lookups. With no network the plugin still discovers, diagnoses and reports; it withholds recommendations instead of answering from memory |
| Write access | one config file, mode 0600, outside this repository |

## Operating workflow

### Step 0 — first contact with the host

```
/openclaw-ops:init [--detect-only]
```

Preflights the host (OS, Docker binary, daemon, socket permission — each fatal alone), detects every
compose project matching the prefix, and shows the inventory including the rows you do not manage. Then
one question covering exactly what detection cannot infer: the reference instance, the canary, what
stays unmanaged, and the update policy. Step 5 writes one file, mode 0600.

Nothing found is a diagnosis, not a dead end: zero compose projects means the wrong machine, projects
that do not match means re-run with `--prefix`, everything `alien` means a deployment class this plugin
does not model and will not touch.

Run `--detect-only` first if you want to look before anything is written.

### Step 1 — the daily picture

```
/openclaw-ops:status
```

One row per instance: `NAME STATE PROFILE ROLE MANAGED PORT VERSION HEALTH LOG-AGE NOTE`. Seconds, no
in-container calls.

**Read HEALTH and LOG-AGE as two independent verdicts.** Green health beside a log that has not moved
for days is the zombie signature — the disagreement is the result, not a rendering artefact. That pair
is what makes Step 2 worth its cost.

### Step 2 — the deep battery, on purpose

```
/openclaw-ops:status --deep
```

Several in-container reads per instance, so never by reflex. HEALTH (container state, the three
endpoints, delivery queues, credential status, memory subsystem) and LIVENESS (log age, last timer fire,
last index write) are computed from **disjoint** evidence. Snapshots persist so the next run shows a
delta: what is new, what has been sitting there for six weeks, what you fixed and it stayed fixed.

Every non-info finding prints with its ready-to-run repair line underneath.

### Step 3 — the full sweep

```
/openclaw-ops:audit [selector] [--focus auth|versions|memory|cron|secrets|security|shared|all]
```

Runs the auditor agent: every axis, read-only, cross-checked against the findings catalog, the
upstream-issues catalog and live documentation, returning one prioritised report. The agent has no
`Write` or `Edit` — it cannot change anything even by accident.

For one instance that is deeply broken, the incident-responder agent goes the other way: iterative log
reading, hypotheses against evidence, one finding id and one targeted action.

### Step 4 — name the finding

A symptom is not repairable; a finding id is. The `fleet-diagnostics` skill turns "something is wrong"
into an id from its catalog — every id carries severity, detection, fix, verification and mutation
class. A symptom with no row gets a catalog row **with its documentation citation** first, and a repair
second. That is what stops a fix from being improvised on production.

### Step 5 — repair, through the one funnel

```
/openclaw-ops:repair <selector> --issue <finding-id>          # plan
/openclaw-ops:repair <selector> --issue <finding-id> --yes    # a LATER turn
```

Resolve the id to its row, resolve the targets **as a mutation** (an empty selector, `all`, an alien,
unmanaged or legacy instance are refused by name), re-run the detection so a finding that no longer
reproduces is reported resolved rather than repaired, then print the eight-block plan. `--yes` applies —
never in the turn the plan was first shown.

### Step 6 — credentials before anything else

```
/openclaw-ops:auth [selector] [--status] [--print-login]
```

The most expensive failure class here, and invisible until every schedule on the fleet fails at once.
Classifies each profile — healthy, expiring, expired, emptied, absent, orphaned runtime, shadowed — from
metadata and fingerprints, never by exercising the credential. Interactive logins are **printed for a
human to run**, not executed. Credential repair is a precondition of upgrading, not a follow-up.

### Step 7 — upgrade

```
/openclaw-ops:update <selector> [--to <version>] [--channel …]
```

R4 on every instance, every time: the state schema migrates in place, and a failed migration does not
undo itself. The command resolves the channel through registry dist-tags (the only mechanical fact about
where a channel points), enforces the soak window, pins an **immutable** identifier, captures a
pre-upgrade baseline so only *new* findings block, takes the three-layer backup — and **rejects** an
upgrade whose backup has not passed verification rather than warning about it.

Afterwards, three checks that are easy to skip and expensive to miss: delivery queues behind a green
rollup, duplicated schedule entries, and a migration that silently rewrote the primary model.

```
/openclaw-ops:features <selector> [--from <version>]
```

Reads the release notes across a range and reports, per instance, which newly added config keys and
commands this fleet could adopt, with a recommendation and a risk class. **Nothing is switched on.**

### Step 8 — the rest, in the order the fleet usually needs it

```
/openclaw-ops:shared-sync [selector]     # deduplicate, promote, register, unshadow, verify on four levels
/openclaw-ops:clone <new> [--from <ref>] # isolation preflight, a genuinely free port, manual steps printed
/openclaw-ops:logs [selector]            # fan out, redacted, per-instance headers
/openclaw-ops:exec <selector> -- <args>  # the audited escape hatch
```

## Skills

| Skill | Triggers on |
|---|---|
| `fleet-model` | the foundation every other skill assumes — shape, selector grammar, exec contract, four states, dry-run convention, symptom routing table |
| `fleet-diagnostics` | a symptom, and the catalog that turns it into a finding id; the contract shared by status, audit, repair and the auditor |
| `provider-auth` | logged out, expired, emptied or shadowed credentials; one account across several instances; choosing between key, OAuth and a local CLI backend |
| `config-surgery` | reading, changing, restoring or explaining an instance config; what needs a restart; a stray backup or rejected sidecar |
| `secrets-infisical` | secret delivery through an injection wrapper; a feature silently off; plaintext env files; proving a key is delivered |
| `memory-ops` | embeddings failing authorization, paused vector search, index identity, reindexing, a state database growing without bound |
| `shared-assets` | skills and plugins shared across instances: empty mounts, duplicates, shadows, ownership refusals, install locks |
| `instance-upgrade` | version drift, channels and dist-tags, tag versus digest, soak windows, post-upgrade traps |
| `security-audit` | exposure, firewall chains that do not apply to published ports, token reuse, permissions, trust boundary |
| `instance-clone` | standing up a new instance from the reference and proving it isolated |
| `docs-research` | before any claim that could have changed — flags, keys, versions, model names; and when two sources disagree |
| `examples` | four end-to-end runs on a fictional fleet, threading commands, skills and scripts into one sequence |

## Commands

| Command | Arguments |
|---|---|
| `/openclaw-ops:init` | `[--detect-only] [--force]` |
| `/openclaw-ops:status` | `[selector] [--deep] [--json]` |
| `/openclaw-ops:audit` | `[selector] [--focus auth\|versions\|memory\|cron\|secrets\|security\|shared\|all]` |
| `/openclaw-ops:repair` | `<selector> --issue <finding-id> [--all-findings] [--yes]` |
| `/openclaw-ops:auth` | `[selector] [--provider <id>] [--status] [--print-login] [--watch]` |
| `/openclaw-ops:update` | `<selector> [--to <version>] [--channel latest\|extended-stable] [--yes]` |
| `/openclaw-ops:features` | `<selector> [--from <version>]` |
| `/openclaw-ops:shared-sync` | `[selector] [--adopt-duplicates] [--restart] [--yes]` |
| `/openclaw-ops:clone` | `<new-instance> [--from <reference>] [--port auto\|<n>] [--yes]` |
| `/openclaw-ops:logs` | `[selector] [--tail <n>] [--since <dur>] [--grep <re>] [--errors-only]` |
| `/openclaw-ops:exec` | `<selector> -- <openclaw args…> [--json] [--timeout <s>]` |

Selector grammar (owned by `fleet.py resolve`, reimplemented nowhere): empty or `managed` · `all`
(**read-only**) · `@reference` `@canary` `@<role>` · `a,b` · `web-*` · `managed,-b`. A mutation must name
its targets — empty and `all` are refused, because a selector that widens as the fleet grows turns a
one-instance fix into a fleet-wide incident.

## Agents

| Agent | Role |
|---|---|
| `openclaw-fleet-auditor` | read-only sweep across every axis → one prioritised report with a repair line per finding |
| `openclaw-incident-responder` | one broken instance, in depth: crash loop, zombie, stuck search, stalled timer |

Neither agent has `Write` or `Edit`. Procedures whose steps need human consent — upgrade, clone — are
deliberately **not** delegated: a subagent cannot receive a `--yes`, and delegating would hide the gate.

## Scripts

All Python 3, stdlib only, invoked as `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/<name>"`.

| Script | Does |
|---|---|
| `fleet.py` | `discover` · `resolve` · `config --init\|--show\|--validate\|--diff`. Cheap, runs constantly |
| `ocexec.py` | the single door into the CLI: mode choice, policy refusals, redaction, exit-code meaning |
| `healthcheck.py` | the expensive probe battery; HEALTH and LIVENESS from disjoint evidence; snapshots |
| `versions.py` | what runs, what a channel points at, and why a target is not eligible yet |
| `report.py` | one canonical document plus the delta against earlier snapshots — new, aged, resolved |
| `clone.py` | the deterministic half of cloning: name, free port, isolation preflight, materialisation |
| `catalog-check.py` | contract check: every finding id the battery can emit has a catalog row, at the severity that row states |
| `hooks/validate-openclaw-json.py` | `PostToolUse` guard: a config edited into a file the gateway would refuse to load |

## The fleet config

Operator-owned, **outside this repository**, mode 0600. Resolution ladder, first hit wins:

```
$OPENCLAW_OPS_CONFIG  →  ./.openclaw-ops.json  →  ~/.config/openclaw-ops/fleet.json  →  /etc/openclaw-ops/fleet.json
```

It holds only what discovery cannot infer. Shape (`scripts/lib/fleet.example.json`, values invented):

| Field | Meaning |
|---|---|
| `project_prefix`, `compose_root`, `data_root`, `gateway_service` | how this host names and lays things out |
| `host_fingerprint`, `host_label` | which machine the file describes |
| `reference` | what clones copy and what upgrade waves lead with |
| `policy.canary` · `update_channel` · `soak_days` · `stale_log_hours` · `snapshot_dir` · `batch_max` · `loopback_only` | the decisions autodetect cannot make |
| per instance: `manage`, `role`, `criticality`, `aliases`, `notes` | scope and blast radius |
| per instance: `secrets` | provider, identity file **path**, project id, environment, expected key count |

**Never in the file: a secret value.** Names, ids and counts only.

Two behaviours worth knowing. A `host_fingerprint` mismatch forces **read-only** — the file describes
another machine, so every path in it is a guess; re-run `init` on the new host rather than editing the
fingerprint. And `init` refuses to write inside a git work tree: an `./.openclaw-ops.json` beside a repo
is the most common way instance names, ports and host paths get committed.

With no config at all, discovery still works and mutations do not.

## Safety

**A mutation is any operation after which observable state differs from what it would have been.** The
word `status` in a command name proves nothing — the credential probe form is a mutation, because it
requires a stopped gateway.

| Class | Gate | Examples |
|---|---|---|
| R0 read | free | inspect, endpoints, lint, credential **check**, list subcommands |
| R1 read with effect | as R2 | credential **probe**, anything on the agent path, indexing |
| R2 reversible | `--yes` | restart, config edit, enabling or disabling a schedule |
| R3 partially reversible | `--yes` + a backup that **already exists** | forced reindex, session pruning, database compaction |
| R4 irreversible | `--yes` + a typed phrase | version upgrade, secret write, automatic security fix, gateway-token change |

Every mutation prints eight blocks before it runs: **TARGET · PRECHECK · CHANGE · BACKUP · IMPACT ·
VALIDATE · ROLLBACK · APPLY**, plus **IRREVERSIBLE · CONFIRM** for R3 and R4. PRECHECK shows its
failures too. CHANGE carries a deletion count, and a non-zero one in a config is a flag of its own.
ROLLBACK is an **executable command** — prose does not validate.

`--yes` is never added in the turn a command is first proposed. "The user said go ahead earlier" is not
consent for this operation. And `--yes` alone does not open the exec door either: above R0 the call
carries the plan behind it — `--plan-id`, minted by the command that showed the eight blocks, or the
rendered plan itself as `--plan <file>`. The escape hatch runs one command; it cannot build a plan, so
it does not get to skip one. The id is a **record**, not a string that looks right: minting writes it
(command, instance, risk class, plan fingerprint, expiry) and the door refuses an id that was never
issued here, has passed its short TTL, names another instance, covers a lower class — or has already
been used, because it is burned on use. One plan authorises one mutation.

Credential mutations additionally take a fleet-wide front lock (`fleet-auth`), because the runtime's
own serialisation lock lives inside a single state directory and cannot see a second instance
refreshing the same rotating token.

### Red lines — `--yes` is not enough

Upgrading without a backup that passed verification (**rejected**, not warned) · any fleet-wide mutation
· overwriting an existing secret whose fingerprint differs · rotating a gateway token · deleting a
plaintext env file before parity is proven · the automatic-fix modes of the linter and the security
audit · installing assets with an unread install lock · any mutation on a legacy-layout instance ·
writing inside a container outside a mounted volume.

### Zero retries — repeating is worse than failing

OAuth login and refresh (a retry burns a single-use token and logs out another consumer) · version
update (a half-migrated state directory) · skill and plugin install (a damaged lock removes the rest) ·
restart during a crash loop (destroys the log line holding the cause, buys a longer backoff) · secret
write. One failure means stop and inspect.

### Batches

Direction decides the rule. **Good → changed: fail fast** — a mixed fleet is described by no document
and covered by no rollback. **Broken → attempted repair: continue and report** — one failure is no
reason to leave five instances broken. Over both, the **canary barrier**: anything touching more than one
instance goes to the least critical one first and stops there for a separate confirmation.

### What this plugin never does

- Never prints a secret **value** — anywhere, including in examples. Presence, key name, class, size
  bucket, expiry and a `fp:` fingerprint answer every question a value could; a fingerprint match proves
  two values are identical without either entering the transcript, where nothing can be unprinted.
- Never accepts a key pasted into the chat. It prints the line that reads the value with echo disabled
  and verifies afterwards by fingerprint. A value already pasted is treated as leaked.
- Never reads a credential file, env file or identity file whole into context — structure-only reads,
  names and fingerprints.
- Never passes the capability-acceptance flag. Upstream deliberately made confirmation flags and
  automatic fixes unable to approve capabilities; automating that consent would destroy the mechanism.
  The line is printed for a human.
- Never hand-writes `docker exec`.
- Never mutates an `alien`, unmanaged or legacy-layout instance.
- Never mutates against a moving image tag — no recorded immutable identifier, no mutation, because a
  rollback without one is impossible.
- Never restarts to diagnose.
- Never quotes a version, flag spelling or model id from memory. Any model id entering a diff is an echo
  of that instance's own catalogue.

## Limits of testing — read this before trusting a green run

What is verified: the **mechanics**. Static checks (no absolute paths, no required environment variables, no
model-id literals outside example blocks, every mutation path carrying all eight blocks and a non-empty
executable rollback) · dry fixtures of captured, scrubbed command output covering profile detection,
state classification, diagnosis, redaction, plan rendering and batch-mode choice · a read-only pass over
a live fleet · and mutations exercised on a throwaway cloned instance, including a deliberately failed
batch to prove the fail-fast path.

What that does **not** cover, and cannot:

- **Scale and load.** A canary is one instance. Load-dependent upstream behaviour — nightly timer stalls,
  queue backlogs, database growth over months — does not reproduce in a test window. The plugin detects
  those by keeping history; it cannot rehearse them.
- **Provider-side behaviour.** Token rotation, reuse detection, billing failures and cooldowns live at
  the provider. The rules here come from documented behaviour and observed incidents, not from a
  reproducible test.
- **Upstream drift.** Subcommand spellings, flags and defaults change between versions, and an old
  instance ships old documentation. That is why the plugin derives capabilities from the running build
  and fetches before recommending — but a fixture captured today ages.
- **Your fleet's specifics.** Every name, port, path and version in the docs and examples is invented.
  Detection replaces them; nothing in this repository was written knowing your layout.
- **Anything already in git history.** The publication gate reads the **working tree only**. A host,
  address, identifier or credential that reached a commit is invisible to it, and deleting the line in a
  later commit does not remove it — the old blob is still fetchable by anyone who clones. A leak that got
  that far is handled by **revoking the value at its source** (rotate the token, retire the endpoint),
  not by editing a file. Treat a green gate as "nothing new is leaving", never as "nothing has left".

## Not in scope

Provisioning a host or a fleet from scratch · migrating a legacy-layout instance (refused with its
reason — that is its own project) · workloads other than OpenClaw, which appear in the inventory as
neighbours and are never touched · workspace and persona content, which belongs to the deprecated
`openclaw-configurator`.
