#!/usr/bin/env bash
# Sync the official googleworkspace/cli Agent Skills into
# plugins/google-workspace-dev/skills/{gws,persona,recipe}-*.
#
# This is a TRUE MIRROR of the upstream `skills/` directory for the three
# upstream-owned prefixes:
#   - gws-*      (one skill per Workspace API + helper commands)
#   - persona-*  (role-based personas)
#   - recipe-*   (curated multi-step workflows)
#
# Skills that do NOT match those prefixes are NEVER touched, so the custom
# Agents Store skills (google-workspace-setup, examples) survive every sync.
# Upstream additions are copied, upstream removals are deleted locally.
#
# Env (optional):
#   UPSTREAM_REF   — git ref to sync from (default: main)
#   UPSTREAM_REPO  — repo URL (default: https://github.com/googleworkspace/cli.git)
#
# Outputs the upstream commit SHA on stdout so CI can use it in the PR body.
# All progress logs go to stderr.

set -euo pipefail

UPSTREAM_REPO="${UPSTREAM_REPO:-https://github.com/googleworkspace/cli.git}"
UPSTREAM_REF="${UPSTREAM_REF:-main}"

# Upstream-owned skill prefixes. Anything else under skills/ is custom.
PREFIXES=(gws- persona- recipe-)

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_DIR="${REPO_ROOT}/plugins/google-workspace-dev"
TARGET_SKILLS="${PLUGIN_DIR}/skills"

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

# Helper: does $1 start with any of the upstream-owned prefixes?
is_vendored() {
  local name="$1" p
  for p in "${PREFIXES[@]}"; do
    [[ "${name}" == "${p}"* ]] && return 0
  done
  return 1
}

shopt -s nullglob

# 1. Copy/update every upstream skill that matches a vendored prefix.
echo "→ syncing upstream skills (${PREFIXES[*]})" >&2
synced=0
for upstream_skill in "${TMP}/upstream/skills"/*/; do
  name="$(basename "${upstream_skill}")"
  is_vendored "${name}" || continue
  echo "  • ${name}" >&2
  rsync -a --delete "${upstream_skill}" "${TARGET_SKILLS}/${name}/"
  synced=$((synced + 1))
done
echo "→ ${synced} upstream skills synced" >&2

# 2. Delete local vendored skills that no longer exist upstream (true mirror).
echo "→ pruning vendored skills removed upstream" >&2
pruned=0
for local_skill in "${TARGET_SKILLS}"/*/; do
  name="$(basename "${local_skill}")"
  is_vendored "${name}" || continue          # never prune custom skills
  if [[ ! -d "${TMP}/upstream/skills/${name}" ]]; then
    echo "  ✗ ${name} (gone upstream)" >&2
    rm -rf "${local_skill}"
    pruned=$((pruned + 1))
  fi
done
echo "→ ${pruned} stale vendored skills pruned" >&2

# 3. Refresh the upstream skills index for reference, if present.
if [[ -f "${TMP}/upstream/docs/skills.md" ]]; then
  cp "${TMP}/upstream/docs/skills.md" "${PLUGIN_DIR}/SKILLS_INDEX.md"
  echo "→ refreshed SKILLS_INDEX.md" >&2
fi

echo "${UPSTREAM_SHA}"
