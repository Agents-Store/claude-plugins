#!/usr/bin/env bash
# Vendor the official Teams SDK skills (MIT, microsoft/teams-sdk) into
# plugins/teams-dev/skills/teams-sdk-*.
#
# Upstream ships one Claude Code plugin, plugins/teams-sdk, whose skills/
# directory holds the skill `teams-dev` (bot scaffolding, bot infrastructure,
# SSO setup, troubleshooting, integrating an existing server). Each upstream
# skill directory <name> is mirrored to teams-sdk-<name> so it can never
# collide with a hand-written skill of this plugin. Because the frontmatter
# `name` must equal the directory name (lint rule skill-name), `name:` is
# rewritten to the prefixed name.
#
# Vendored directories are mirrored with `rsync --delete`: edit them upstream,
# never here. A local fix to a vendored skill is recorded in LEARNINGS.md as
# "pending upstream" and lands via the next sync. Every other directory under
# plugins/teams-dev/skills (the hand-written skills) is never touched.
#
# Upstream `evals/` directories are not copied: an evals.json carries the
# upstream skill name in `skill_name` and has no use inside a plugin.
#
# Env (optional):
#   UPSTREAM_REF   — git branch or tag to sync from (default: main)
#   UPSTREAM_REPO  — repo URL (default: https://github.com/microsoft/teams-sdk.git)
#
# Outputs the upstream commit SHA on stdout so CI can use it in the PR body.
# All progress logs go to stderr.

set -euo pipefail

UPSTREAM_REPO="${UPSTREAM_REPO:-https://github.com/microsoft/teams-sdk.git}"
UPSTREAM_REF="${UPSTREAM_REF:-main}"
PREFIX="teams-sdk-"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_DIR="${REPO_ROOT}/plugins/teams-dev"
TARGET_SKILLS="${PLUGIN_DIR}/skills"

if [[ ! -d "${PLUGIN_DIR}" ]]; then
  echo "error: ${PLUGIN_DIR} does not exist" >&2
  exit 1
fi
mkdir -p "${TARGET_SKILLS}"

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

echo "→ cloning ${UPSTREAM_REPO}@${UPSTREAM_REF} into ${TMP}/upstream" >&2
git clone --depth 1 --branch "${UPSTREAM_REF}" "${UPSTREAM_REPO}" "${TMP}/upstream" >&2

UPSTREAM_SHA="$(git -C "${TMP}/upstream" rev-parse HEAD)"
SRC="${TMP}/upstream/plugins/teams-sdk/skills"

if [[ ! -d "${SRC}" ]]; then
  echo "error: upstream layout changed: ${SRC} is missing" >&2
  exit 1
fi

# The `name:` value inside the leading --- frontmatter block, quotes stripped.
frontmatter_name() {
  awk '
    NR == 1 { if ($0 != "---") exit; next }
    $0 == "---" { exit }
    /^name:/ { sub(/^name:[ \t]*/, ""); gsub(/["\047]/, ""); print; exit }
  ' "$1"
}

echo "→ syncing upstream skills" >&2
shopt -s nullglob
synced=0
for upstream_skill in "${SRC}"/*/; do
  base="$(basename "${upstream_skill}")"
  name="${PREFIX}${base}"
  [[ -f "${upstream_skill}SKILL.md" ]] || { echo "  - skip (no SKILL.md): ${base}" >&2; continue; }
  echo "  • ${base} → ${name}" >&2
  rsync -a --delete --exclude 'evals/' "${upstream_skill}" "${TARGET_SKILLS}/${name}/"

  # The skill-name lint wants frontmatter `name` == directory name.
  fm_name="$(frontmatter_name "${TARGET_SKILLS}/${name}/SKILL.md")"
  if [[ "${fm_name}" != "${name}" ]]; then
    echo "    name: '${fm_name}' → '${name}'" >&2
    sed -i "0,/^name:.*/s//name: ${name}/" "${TARGET_SKILLS}/${name}/SKILL.md"
  fi
  synced=$((synced + 1))
done
echo "→ ${synced} upstream skills synced" >&2

# Prefixed directories that upstream no longer has: report, never delete.
for local_skill in "${TARGET_SKILLS}"/"${PREFIX}"*/; do
  name="$(basename "${local_skill}")"
  [[ -d "${SRC}/${name#"${PREFIX}"}" ]] && continue
  echo "warning: ${name} has no upstream skill — renamed or removed upstream? Review by hand." >&2
done

# MIT requires the licence text to travel with the copied skills.
if [[ -f "${TMP}/upstream/LICENSE" ]]; then
  cp "${TMP}/upstream/LICENSE" "${PLUGIN_DIR}/LICENSE-teams-sdk"
else
  echo "warning: upstream has no LICENSE file" >&2
fi

echo "${UPSTREAM_SHA}"
