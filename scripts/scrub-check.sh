#!/usr/bin/env bash
# Publication gate — refuse to ship deployment-specific data in a public plugin,
# and refuse to ship one that is not built the way the conventions say it is.
#
#   ./scripts/scrub-check.sh                     whole repository
#   ./scripts/scrub-check.sh plugins/<name>      one plugin
#   ./scripts/scrub-check.sh --strict <path>     force the strict ruleset
#   ./scripts/scrub-check.sh --format json       machine-readable output
#   ./scripts/scrub-check.sh --no-lint <path>    scrub only, skip the structure lint
#
# Exit: 0 clean · 1 hard fail (blocks the merge) · 2 warnings only.
#
# Two passes run behind this one entry point:
#   scrub_check.py   deployment data in the tree — rules written as shapes,
#                    never as literal values from any real deployment, because a
#                    gate that hardcodes the strings it hunts becomes the leak it
#                    was meant to stop. Exceptions: scripts/scrub-allow.txt.
#   plugin_lint.py   structure — the eight-block dry-run plan with an executable
#                    ROLLBACK on every mutating command, one skill name across
#                    SKILL.md / directory / evals.json, and plugin.json version
#                    equal to the marketplace.json entry. No baseline: fixed, not
#                    excused.
#
# NOTE: both passes read the WORKING TREE only. A value that already reached git
# history is not caught here and cannot be fixed by editing a file — it has to be
# revoked at the source. See CLAUDE.md, "Publication Gate".
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "scrub-check: python3 is required" >&2
  exit 1
fi

run_lint=1
args=()
want_json=0
prev=""
for arg in "$@"; do
  case "$arg" in
    --no-lint)
      run_lint=0
      ;;
    --format=json)
      args+=("$arg")
      want_json=1
      ;;
    *)
      args+=("$arg")
      if [ "${prev}" = "--format" ] && [ "$arg" = "json" ]; then
        want_json=1
      fi
      ;;
  esac
  prev="$arg"
done

worst() {  # 1 (fail) beats 2 (warn) beats 0 (clean)
  if [ "$1" -eq 1 ] || [ "$2" -eq 1 ]; then echo 1
  elif [ "$1" -eq 2 ] || [ "$2" -eq 2 ]; then echo 2
  else echo 0; fi
}

if [ "$run_lint" -eq 0 ]; then
  exec python3 "${here}/scrub_check.py" "${args[@]+"${args[@]}"}"
fi

if [ "$want_json" -eq 1 ]; then
  scrub_out="$(mktemp)"; lint_out="$(mktemp)"
  trap 'rm -f "${scrub_out}" "${lint_out}"' EXIT
  set +e
  python3 "${here}/scrub_check.py" "${args[@]+"${args[@]}"}" >"${scrub_out}"; scrub_status=$?
  python3 "${here}/plugin_lint.py"  "${args[@]+"${args[@]}"}" >"${lint_out}";  lint_status=$?
  set -e
  python3 - "${scrub_out}" "${lint_out}" <<'PY'
import json, sys
scrub = json.load(open(sys.argv[1]))
lint = json.load(open(sys.argv[2]))
print(json.dumps({"scrub": scrub, "lint": lint}, indent=2))
PY
  exit "$(worst "${scrub_status}" "${lint_status}")"
fi

set +e
python3 "${here}/scrub_check.py" "${args[@]+"${args[@]}"}"; scrub_status=$?
python3 "${here}/plugin_lint.py"  "${args[@]+"${args[@]}"}"; lint_status=$?
set -e
exit "$(worst "${scrub_status}" "${lint_status}")"
