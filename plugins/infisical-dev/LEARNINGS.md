# infisical-dev — Learnings

Accumulated fixes and discoveries for the Infisical CLI plugin. Newest first.

<!-- Format:
## [YYYY-MM-DD] — [skill-name]: Brief description
**Problem:** What went wrong
**Fix:** What was changed
**Root cause:** Why the original was wrong
**Severity:** Critical / Major / Minor
-->

## [2026-10-03] — cli-reference, setup, troubleshoot, ci-cd-auth, agent: `INFISICAL_DOMAIN`, `--domain` on login, vault backends
**Problem:** the plugin called the older API-URL variable the preferred way to pick an instance, said `--domain` on `login` is ignored, and listed `keychain` as a value of `infisical vault set`.
**Fix:** instance order is now `--domain`, `INFISICAL_DOMAIN` (or the older variable when it is unset), `domain` in `.infisical.json`, US Cloud. `--domain` is a global flag and the docs' own example is `infisical login --domain=https://eu.infisical.com`, so the "ignored" rows are gone; a `--domain` / `INFISICAL_DOMAIN` naming a different instance than the logged-in profile makes the command fail, and `agent` and `token renew` are called out as the two commands that do not follow the profile. `vault set` takes `file` or `auto` (checked with `infisical vault set --help`); `auto` falls back to `file` by itself, and switching drops every profile.
**Root cause:** written against CLI 0.43.9x; `domain` in `.infisical.json` landed in 0.43.92, `INFISICAL_DOMAIN` as an explicit instance choice in 0.43.130, named profiles in 0.43.134. Verified against the 0.43.138 release binary (`--help` only, nothing run against an instance).
**Severity:** Major

## [2026-10-03] — cli-reference: `infisical agent` is a command; command index was incomplete
**Problem:** the Deprecations list said `infisical kms` and `infisical agent` "are not current CLI commands".
**Fix:** `agent` exists (`infisical agent --config agent-config.yaml`; it ignores `--domain`, the instance is `infisical.address` in its config); `kms` does not. The command index now covers `agent`, `agent-vault`, `cert-manager`, `gateway`, `relay`, `proxy`, `pam`, `kmip`, `logout`, `org`, `profile`, `secrets agent-proxy` and `ssh issue-credentials|sign-key`, each with flags copied from `--help` of 0.43.138.
**Root cause:** the original reference was written when none of these existed and the "not commands" line was never re-checked against `infisical --help`.
**Severity:** Major

## [2026-10-03] — cli-reference, cli-recipes, ci-cd-auth, secret-scanning: flags that moved or are version-gated
**Problem:** `infisical secrets --plain` (listing) is deprecated in favour of `-o/--output`; `login --oidc-jwt` is deprecated for `--jwt`; `login --method` lacked `jwt-auth`; `run` lacked `--recursive` and `--watch-interval`; `export` lacked `--format dotenv-eval` and the directory form of `-o`; `export --template` was described with Sprig and a `secret` function that the Agent function set does not have; `scan` lacked `--confidence` and `--no-color`, and `--redact` read as if it cleaned reports. `run --path` was documented as "first wins" on conflicts; the docs say the last `--path` wins. `secrets delete` defaults to `--type personal`, so the recipe only removed a personal override.
**Fix:** all of the above corrected with the version that introduced each (`dotenv-eval` 0.43.98, `agent-vault` 0.43.132, profiles 0.43.134 and `profile create` 0.43.135 — it was `profile new` in 0.43.134 — `scan --confidence` 0.43.136). `--plain` stays valid on `secrets get`, `lease create` and `login`; only the first two have `-o/--output` (there is no output flag on `login`). `export` has no `--recursive` (only `run` and `secrets` do) and its `--path` is not repeatable.
**Root cause:** written against 0.43.9x help text; flag defaults and deprecations moved in 0.43.98 to 0.43.138.
**Severity:** Major

## [2026-10-03] — setup, troubleshoot: Cloudsmith repository retired, winget, named profiles
**Problem:** no mention that machines still using the Cloudsmith package repository stopped getting the CLI on 2026-09-16 (`apt-get update` then fails for the whole host); winget and named profiles were missing.
**Fix:** migration note with the removal commands and the `artifacts-cli.infisical.com` setup scripts; `winget install infisical`; a profiles section (`profile create|use|pin|bind`, `login --save-as`, `--profile`, `--org`) and troubleshoot rows for version-gated `unknown command` / `unknown flag` errors, which were reproduced with the older 0.43.91 binary.
**Root cause:** vendor change after the plugin was written.
**Severity:** Minor
