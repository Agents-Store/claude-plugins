#!/usr/bin/env bash
# Sync the official nocobase/skills repo into plugins/nocobase-dev/skills/nocobase-*.
#
# Only touches directories that start with `nocobase-` — custom REST-API skills
# (overview, auth, cli-recipes, api-reference, examples) are never overwritten.
#
# Env (optional):
#   UPSTREAM_REF   — git ref to sync from (default: main)
#   UPSTREAM_REPO  — repo URL (default: https://github.com/nocobase/skills.git)
#
# Outputs the upstream commit SHA on stdout so CI can use it in the PR body.

set -euo pipefail

UPSTREAM_REPO="${UPSTREAM_REPO:-https://github.com/nocobase/skills.git}"
UPSTREAM_REF="${UPSTREAM_REF:-main}"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_SKILLS="${REPO_ROOT}/plugins/nocobase-dev/skills"

if [[ ! -d "${TARGET_SKILLS}" ]]; then
  echo "error: ${TARGET_SKILLS} does not exist" >&2
  exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

echo "→ cloning ${UPSTREAM_REPO}@${UPSTREAM_REF} into ${TMP}/upstream" >&2
git clone --depth 1 --branch "${UPSTREAM_REF}" "${UPSTREAM_REPO}" "${TMP}/upstream" >&2

UPSTREAM_SHA="$(git -C "${TMP}/upstream" rev-parse HEAD)"

if [[ ! -d "${TMP}/upstream/skills" ]]; then
  echo "error: upstream has no skills/ directory" >&2
  exit 1
fi

echo "→ syncing nocobase-* skills" >&2
shopt -s nullglob
for upstream_skill in "${TMP}/upstream/skills"/nocobase-*/; do
  name="$(basename "${upstream_skill}")"
  echo "  • ${name}" >&2
  rsync -a --delete "${upstream_skill}" "${TARGET_SKILLS}/${name}/"
done

# Surface upstream skills that do NOT start with nocobase- so a human can decide.
extras="$(find "${TMP}/upstream/skills" -mindepth 1 -maxdepth 1 -type d ! -name 'nocobase-*' -exec basename {} \; 2>/dev/null || true)"
if [[ -n "${extras}" ]]; then
  echo "warning: upstream has non-nocobase-* skill directories — not synced:" >&2
  echo "${extras}" | sed 's/^/  - /' >&2
fi

echo "${UPSTREAM_SHA}"
