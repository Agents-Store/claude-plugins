# openclaw-ops — Learnings

Accumulated fixes and discoveries for the OpenClaw fleet-operations plugin. Newest first.

> **This file is committed, and it is filled in from real operating sessions — which makes it the most
> likely leak in the plugin.** Everything else here was written to be public; this file is written while
> looking at a live fleet. Scrub before every commit.
>
> Never write down: instance, host or server names · domains, public IPs or host ports · absolute paths
> carrying a real name segment · UUIDs, project ids, workspace ids or policy ids · client, company or
> person names, email addresses · any secret **value**, in any form, including a "harmless" prefix,
> suffix or masked variant · log or command output pasted without redaction.
>
> Write instead: placeholders (`<instance>`, `<data-root>`, `<compose-root>`, `<domain>`) or invented
> stand-ins (`alpha`, `sandbox`, `example.com`, `203.0.113.10`) · key **names** with a fingerprint
> (a synthetic `fp:0000aaaa`, never a real digest prefix), presence and expiry · a version literal only
> inside an `<!-- example-only -->` block,
> never in a recommendation. Container-internal paths and the gateway's internal port are documented
> upstream and are fine.
>
> A finding is reproducible from its mechanism. If an entry only makes sense with the real name in it,
> the entry is describing an incident, not a learning — rewrite it as the mechanism.

<!-- Format:
## [YYYY-MM-DD] — [skill-name]: Brief description
**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
-->

## [2026-08-31] — fleet-diagnostics: the battery and the catalog were two different id spaces

**Problem:** `healthcheck.py` and `report.py` emitted ids such as `liveness.zombie`,
`auth.credentials.expired` and `config.empty`, while the whole documentation layer — the findings
catalog, the skills, both agents and `/openclaw-ops:repair` — knew only `fleet.liveness.zombie`,
`fleet.auth.expired` and `fleet.config.empty`. The intersection of the two sets was **empty**, so the
audit -> report -> repair loop broke at every single finding: the report printed a repair line, and the
funnel answered "no row" to all of them.
**Fix:** one space, the catalog's. Every id the battery emits was renamed to the exact catalog key, the
21 emitted symptoms the catalog did not yet declare got rows (container, endpoint, rollup, liveness
evidence, orphaned schedules, clock skew, unknown version), lint findings now pass through with their
upstream `checkId` **verbatim** instead of under a local `lint.` prefix, and the inclusion is proved
mechanically by `scripts/catalog-check.py` — it fails if the battery can emit an id no row declares.
**Root cause:** the catalog was written as documentation of a contract, and nothing read both sides at
once. A contract with four consumers and no consumer that checks it is a naming convention.
**Severity:** Critical

## [2026-08-31] — fleet-diagnostics: a critical finding disappeared from the report in silence

**Problem:** the catalog declared `critical` > `high` > `warn` > `info` and said `report.py` reads that
column; `report.py` knew `(info, warn, error)`. It grouped findings by iterating its own tuple, so a
`critical` finding matched no group and was **dropped from the rendered document with no message at
all** — and the exit code, which keyed on a `counts["error"]` that no longer existed, came back 0. The
most severe class of finding was the one class guaranteed to be invisible.
**Fix:** one vocabulary everywhere — catalog, `healthcheck.py`, `report.py`, `--severity-min`, the exit
codes (5 = at least one `critical` or `high`, 6 = `warn` only), the auditor agent and the commands. Every
read of a severity goes through a guarded `severity_rank()` that raises a named error listing the
vocabulary, instead of a tuple index whose miss is a silent skip.
**Root cause:** the same value was defined twice, in a document and in a tuple, and the failure mode of
disagreement was omission rather than an error — the one failure mode nobody sees.
**Severity:** Major

## [2026-08-31] — fleet-diagnostics: a defensive `.get()` turned a schema gap into a TypeError

**Problem:** the fleet table read `inst.get("liveness") + (" **diverges**" if …)`. The `.get()` looks
defensive and is the opposite: on a snapshot missing the field it yields `None`, and the very next
operation concatenates it, so an incomplete input died as `TypeError: unsupported operand type(s)`
pointing at a rendering expression rather than at the missing field.
**Fix:** `require(mapping, key, where)` names the instance, the field and the schema, and says to re-run
`healthcheck.py --snapshot`. It is raised as a `SchemaError`, caught once at the command boundary, and
reported as a runtime error instead of a traceback.
**Root cause:** `.get()` was used as error handling when it is only a default, and no default was
supplied.
**Severity:** Minor

## [2026-08-31] — instance-upgrade: the update channel had two names, one of which failed validation

**Problem:** the config schema accepted `stable`, and both the `versions.py` docstring and the
`/openclaw-ops:update` argument hint offered the operator `latest`. `latest` is the **dist-tag** the
`stable` channel resolves through, not a channel name — so an operator who copied it into
`policy.update_channel` wrote a config that fails schema validation.
**Fix:** the channel vocabulary is exactly the schema enum (`stable`, `extended-stable`, `beta`, `dev`)
in all three places, `--channel` enforces it as a choice list, and the channel-to-dist-tag mapping is
stated where the operator meets it: in the flag's help, in the table's comment and in the report line
that already prints `channel X -> dist-tag Y`.
**Root cause:** a name from the layer below leaked into the operator-facing vocabulary, and the two
layers deliberately do not share spellings.
**Severity:** Minor

## [2026-08-31] — fleet-model: the text dry-run printed the command line unredacted

**Problem:** `ocexec.py --dry-run` built the resolved command line and printed it with a bare
`" ".join(cmd)`. The JSON branch went through `redact.redact_argv`, the text branch did not — and the
text branch is the documented first step of the exec command, the one a human is meant to read. Any
secret sitting in the argv (a config write, a token passed to a subcommand) went to the transcript in
full.
**Fix:** the text branch prints `redact.redact_argv(cmd)` like the JSON branch. Every refusal message
that quotes the user's own argv now goes through the same redactor (`_shown()`), including the
cold-mode "that subcommand is not safe here" line.
**Root cause:** the redactor was applied per output *format* instead of at the one place the argv
becomes text. A second formatting path was added later and simply did not know about the rule.
**Severity:** Critical

## [2026-08-31] — fleet-model: the exec door was a way around the mutation discipline

**Problem:** the door refused R3/R4, but performed R1 and R2 — restarts, config writes, and every
unrecognised verb, which the classifier defaults to R2 — on a single `--yes`, with no plan, no
snapshot and no rollback. Eight blocks were mandatory in the command layer and optional in practice,
because the escape hatch sat next to it.
**Fix:** above R0 the door now demands the plan behind the call: `--plan-id
<command>/<instance>/<utc-stamp>` minted by a plan-building command (`gate.make_plan_id`), or the
rendered plan itself via `--plan <file>`, re-validated here for all eight blocks, a BACKUP and an
executable ROLLBACK (`gate.check_plan_authorises`). An id minted for another instance is refused.
`--dry-run` is exempt: it runs nothing and is how the plan gets written.
**Root cause:** the discipline was enforced where plans are *built* rather than where mutations are
*performed*, so the one call site that could not build a plan became the one call site with no gate.
**Severity:** Major

## [2026-08-31] — fleet-model: the plan id was checked for shape, not for existence

**Problem:** the door demanded `--plan-id` above R0 and then validated it with a regular expression.
`repair/<instance>/2020-01-01T00:00:00Z`, typed by hand, passed — and passed again for every later
mutation, because nothing recorded that a plan had ever been shown or used. The barrier the previous
fix installed was disciplinary: it asked the caller to assert that a plan existed.
**Fix:** minting is now a write. `gate.make_plan_id` records the plan (id, command, instance, risk
class, a fingerprint of the plan it stands for, an expiry) under `policy.plan_dir` at mode 0600, and
`gate.check_plan_id` reads it back: issued here, inside its TTL (30 min — a plan describes state read
at PRECHECK time), this instance, this class or above, and **not already used**. The door consumes
the record when it applies, so an id cannot be carried to a second mutation. `gate.py plan
mint|check|list` exposes the registry to a shell procedure; `tests/test_gate.py` and the new
`tests/test_ocexec.py` pin all of it.
**Root cause:** a check written against the *format* of an authorisation rather than against the
thing it authorises. A well-formed string is evidence of typing, not of a plan.
**Severity:** Major

## [2026-08-31] — provider-auth: the fleet front lock existed only in prose

**Problem:** three documents required a "fleet-level front lock" for credential mutations, and no
code took one. The runtime's own serialisation lock is a file lock inside a single state directory,
so two instances refreshing the same rotating token collided exactly as documented — with the
documents describing the protection that was missing.
**Fix:** `gate.fleet_lock()` — an exclusive `O_EXCL` lock file in the state directory from the config
(`policy.lock_dir`, else the `locks` sibling of `snapshot_dir`), with a TTL so a crashed holder frees
itself, and the holder, its operation and the seconds remaining printed when it is busy. `ocexec.py`
takes it for any `models auth …` mutation; a multi-step procedure takes it once via `gate.py lock
take` and passes the token as `--lock-token`, which the door inherits instead of deadlocking against.
**Root cause:** a requirement written as a rule for the operator to follow, in a plugin whose whole
premise is that rules only hold when something enforces them.
**Severity:** Major

## [2026-08-31] — fleet-diagnostics: the gateway bearer travelled in a command line

**Problem:** the in-container endpoint battery passed the operator token as `curl -H "Authorization:
Bearer $TOK"` (and `wget --header=…`). Argument lists are readable through `/proc` by every process
in the container, so the probe published the credential it was testing.
**Fix:** the header is fed out of band — curl reads a config file from stdin (`--config -` with a
here-document), wget reads a mode-600 `WGETRC` written by a here-document and removed straight
after, node already read an environment variable. No client receives the token on argv.
**Root cause:** "the token never leaves the container" was read as the whole requirement; inside the
container it was still handed to the least private channel available.
**Severity:** Minor
