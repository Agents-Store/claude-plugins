# tests — level 2 of the verification ladder

Dry fixtures, no server. Standard-library `unittest` only, so the suite runs
anywhere `python3` runs, with no install step and no third-party dependency.

```bash
cd plugins/openclaw-ops
python3 -m unittest discover -s tests -t tests            # everything
python3 -m unittest discover -s tests -t tests -v         # with test names
(cd tests && python3 -m unittest -v test_discovery)        # one module
python3 -m unittest discover -s tests -t tests -k plan    # one subject, by name
```

| Module | Covers |
|---|---|
| `test_discovery.py` | the layout fingerprint (template / legacy / alien — the legacy auth-key mount is optional, not a marker), paths read out of the mount table, the state ladder (ok / degraded / down / alien), and the rule that one broken instance never shortens the inventory |
| `test_redact.py` | input with keys, output with none of their values; fingerprints stable and distinguishing; the env reader returning names and never values |
| `test_gate.py` | all eight dry-run blocks; a prose or missing ROLLBACK refused; R1+ refused without `--yes`; R3 without a taken backup; R4 without the typed phrase; the batch mode chosen by direction; the plan-id registry — an invented id refused, an issued one accepted once, then burned |
| `test_ocexec.py` | the single door: risk markers that name commands that exist (and are R3/R4 by effect), cold mode admitting `doctor`, the dry run redacted in both branches, the fleet lock on the auth family, a mutation refused without an issued plan id, an alien or unmanaged instance refused, hot/cold chosen from the instance's own state, and no bearer token on any argument list |
| `test_healthcheck.py` | the severity vocabulary where upstream words enter it: the mapped spellings, and an unmapped one raising instead of becoming `info`; the lint invocation (pinned threshold, `--all`) and a failed lint run raising its own finding instead of passing |
| `test_ocjson.py` | the exit-code contracts — only where upstream documents them, `doctor --lint` exit 2 a failure, `security audit` deliberately without one — the `level` field of the post-upgrade envelope, and that only stdout is parsed while stderr stays diagnosis |
| `test_versions.py` | the release line read from the patch number, `beta` as the newer of two tags, `dev` as git with no target, and the `bridge-required` verdict for an installation older than the cut-off |
| `test_catalog_check.py` | the battery and the findings catalog sharing one id space, with path-shaped upstream ids recognised as pass-through |
| `test_report.py` | the canonical render, the delta against the previous snapshot, and a severity outside the vocabulary aborting loudly instead of vanishing |

`_support.py` puts `scripts/` and `scripts/lib/` on the path — the same way the
commands load them — and resolves `fixtures/`. Every fixture is synthetic; see
`fixtures/README.md`.
