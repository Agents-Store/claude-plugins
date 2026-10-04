#!/usr/bin/env bash
# Guard: the files macstack-dev bundles are byte-identical to the canon they mirror.
#
#   ./scripts/check-macstack-canon.sh
#
# The plugin carries three copies of files that other repositories own:
#
#   plugins/macstack-dev/skills/lint/references/macstack.schema.json     <- macstacks/macstack  schema/macstack.schema.json
#   plugins/macstack-dev/skills/lint/references/coverage-areas.json      <- macstacks/registry  coverage-areas.json
#   plugins/macstack-dev/skills/lint/references/software-categories.json <- macstacks/registry  software-categories.json
#
# Nothing here changes when the canon does, so the copies drift in silence, and every
# lint rule that reads them (12.1 builds its expected docs.files keys from the schema)
# starts judging projects against a standard that has moved on. A fix applied to a
# mirror is overwritten by the next sync; the fix belongs at the source, then the copy
# here is refreshed in the same pull request. This script is what notices.
#
# Environment:
#   MACSTACK_CANON_OFFLINE=1    skip the check, exit 0 (no network, or a deliberate lag)
#   MACSTACK_CANON_REF=main     branch or tag of the canon repositories
#   MACSTACK_CANON_BASE=...     where the canon is fetched from; default is the raw
#                               GitHub host. The path under it is <org>/<repo>/<ref>/<file>,
#                               so a test points it at a file:// directory of the same shape
#   MACSTACK_MIRROR_DIR=...     the directory holding the bundled copies (tests)
#
# Exit: 0 every mirror equals its canon, or skipped · 1 a mirror differs · 2 the canon
# could not be fetched. Prints file names and sha256 digests only, never a file's content.
#
# Not part of the no-network unit tests: it needs the canon, which is a network resource.
# A mirror taken from an unmerged canon branch differs from main until that branch merges —
# that failure is expected, and the message says which side to refresh.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MIRROR_DIR="${MACSTACK_MIRROR_DIR:-$ROOT/plugins/macstack-dev/skills/lint/references}"
BASE="${MACSTACK_CANON_BASE:-https://raw.githubusercontent.com}"
REF="${MACSTACK_CANON_REF:-main}"

if [ "${MACSTACK_CANON_OFFLINE:-}" = "1" ]; then
  echo "check-macstack-canon: skipped (MACSTACK_CANON_OFFLINE=1)"
  exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
  echo "check-macstack-canon: curl is required (or set MACSTACK_CANON_OFFLINE=1)" >&2
  exit 2
fi

sha256() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    shasum -a 256 "$1" | awk '{print $1}'
  fi
}

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

# <mirror file name> <path of the canon file under <org>/<repo>/<ref>/>
LIST='macstack.schema.json macstacks/macstack/@REF@/schema/macstack.schema.json
coverage-areas.json macstacks/registry/@REF@/coverage-areas.json
software-categories.json macstacks/registry/@REF@/software-categories.json'

status=0
checked=0
while read -r name remote; do
  [ -n "$name" ] || continue
  url="$BASE/${remote//@REF@/$REF}"
  mirror="$MIRROR_DIR/$name"
  if [ ! -f "$mirror" ]; then
    echo "FAIL $name: the bundled mirror is missing at ${mirror#"$ROOT"/}" >&2
    status=1
    continue
  fi
  if ! curl -fsSL --retry 2 --max-time 30 -o "$tmp/$name" "$url" 2>"$tmp/err"; then
    echo "FAIL $name: could not fetch the canon from $url (set MACSTACK_CANON_OFFLINE=1 to skip)" >&2
    [ "$status" -eq 1 ] || status=2
    continue
  fi
  checked=$((checked + 1))
  have="$(sha256 "$mirror")"
  want="$(sha256 "$tmp/$name")"
  if [ "$have" = "$want" ]; then
    echo "ok   $name  sha256=$have"
  else
    echo "DIFF $name" >&2
    echo "     bundled  sha256=$have  (${mirror#"$ROOT"/})" >&2
    echo "     canon    sha256=$want  ($url)" >&2
    echo "     refresh the copy from the canon in the same pull request, or — if the canon" >&2
    echo "     change is not merged yet — wait for it: a fix applied only here is overwritten" >&2
    status=1
  fi
done <<EOF
$LIST
EOF

if [ "$status" -eq 0 ]; then
  echo "check-macstack-canon: $checked mirrors equal the canon ($REF)"
fi
exit "$status"
