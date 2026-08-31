# fixtures — level 2 of the verification ladder

Dry snapshots. No server, no Docker daemon, no network. Every file here is
**synthetic**: the shapes are real, the contents are invented. A fixture that
carried a captured value would turn the test suite into the leak the publication
gate exists to stop, so `scrub-check.sh` runs over this directory like any other
part of the plugin.

Conventions used throughout:

| Token | Stands for |
|---|---|
| `acme-` | the fleet's compose project prefix — deliberately not the default, so a hardcoded prefix fails the tests |
| `<data-root>` | wherever the operator keeps instance state |
| `<compose-root>` | wherever the operator keeps compose projects |
| `alpha` `beta` `gamma` | instance names |

Container-side destinations (`/home/node/...`, `/opt/openclaw/...`) and the
gateway's container port are upstream's, so they appear literally.

| File | Feeds |
|---|---|
| `compose-ls.json` | `docker compose ls --format json --all` — four fleet projects (one stopped) plus a neighbour the prefix must exclude |
| `docker-inspect-gateway.json` | a template-layout gateway: every role mount, one unknown mount, a loopback publish, a restart counter |
| `docker-inspect-legacy.json` | the same product in a different shape: no state mount, published off loopback, restarting |
| `doctor-lint.json` | `doctor --lint --json` with one finding at every severity |
| `health.json` | `health --json` reporting `ok: true` while the delivery queues are not clear |
| `models-status.json` | credential states: expired, expiring, ok |
| `openclaw-config-legacy-refs.json` | a config carrying the legacy combined runtime-and-model ref |
| `auth-profiles.json` | auth profiles in oauth / api_key / token mode, one expired, two with empty tokens |
| `logs/zombie.log` | a gateway whose last log line is months old |
| `logs/crash-loop.log` | the same fatal line, over and over |
| `env-with-keys.env` | invented values in real key shapes — the redactor's input |
