#!/usr/bin/env bash
# Sync the skills that come from czlonkowski/n8n-skills (MIT) into
# plugins/n8n-dev/skills.
#
# n8n-dev is a hybrid: every upstream skill directory is vendored verbatim,
# EXCEPT the hand-written ones listed in LOCAL below. Those six are never
# touched, so the native-MCP, REST, CLI, setup, troubleshooting and example
# skills survive every sync. Add a new hand-written skill to LOCAL BEFORE the
# next sync, or it will be reported as an orphan (it is never deleted).
#
# Vendored directories are mirrored with `rsync --delete`: edit them upstream,
# never here. A local fix to a vendored skill is recorded in LEARNINGS.md as
# "pending upstream" and lands via the next sync.
#
# Env (optional):
#   UPSTREAM_REF   — git ref to sync from (default: the latest v* tag)
#   UPSTREAM_REPO  — repo URL (default: https://github.com/czlonkowski/n8n-skills.git)
#
# Outputs the upstream commit SHA on stdout so CI can use it in the PR body.
# All progress logs go to stderr.

set -euo pipefail

UPSTREAM_REPO="${UPSTREAM_REPO:-https://github.com/czlonkowski/n8n-skills.git}"

# Hand-written skills of this plugin. Never overwritten.
LOCAL="n8n-native-mcp api-reference cli-recipes setup troubleshoot examples"

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLUGIN_DIR="${REPO_ROOT}/plugins/n8n-dev"
TARGET_SKILLS="${PLUGIN_DIR}/skills"

if [[ ! -d "${TARGET_SKILLS}" ]]; then
  echo "error: ${TARGET_SKILLS} does not exist" >&2
  exit 1
fi

# Newest v* tag. sed (not head) reads the whole listing, so git never meets a
# closed pipe; the peeled `^{}` lines of annotated tags are stripped.
latest_tag() {
  git ls-remote --tags --sort=-v:refname "${UPSTREAM_REPO}" 'v*' \
    | sed -n '1{s#.*refs/tags/##;s#\^{}$##;p}'
}

UPSTREAM_REF="${UPSTREAM_REF:-$(latest_tag)}"
if [[ -z "${UPSTREAM_REF}" ]]; then
  echo "error: upstream has no v* tag and UPSTREAM_REF is not set" >&2
  exit 1
fi

TMP="$(mktemp -d)"
trap 'rm -rf "${TMP}"' EXIT

echo "→ cloning ${UPSTREAM_REPO}@${UPSTREAM_REF} into ${TMP}/upstream" >&2
git clone --depth 1 --branch "${UPSTREAM_REF}" "${UPSTREAM_REPO}" "${TMP}/upstream" >&2

UPSTREAM_SHA="$(git -C "${TMP}/upstream" rev-parse HEAD)"
SRC="${TMP}/upstream/skills"

if [[ ! -d "${SRC}" ]]; then
  echo "error: upstream has no skills/ directory" >&2
  exit 1
fi

is_local() {
  case " ${LOCAL} " in *" $1 "*) return 0 ;; esac
  return 1
}

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
  name="$(basename "${upstream_skill}")"
  if is_local "${name}"; then
    echo "  - skip (local, never overwritten): ${name}" >&2
    continue
  fi
  [[ -f "${upstream_skill}SKILL.md" ]] || { echo "  - skip (no SKILL.md): ${name}" >&2; continue; }
  echo "  • ${name}" >&2
  rsync -a --delete "${upstream_skill}" "${TARGET_SKILLS}/${name}/"

  # The skill-name lint wants frontmatter `name` == directory name. Upstream
  # keeps them equal; if that ever drifts, normalise it here and say so.
  fm_name="$(frontmatter_name "${TARGET_SKILLS}/${name}/SKILL.md")"
  if [[ "${fm_name}" != "${name}" ]]; then
    echo "  ! ${name}: frontmatter name is '${fm_name}' — normalised to the directory name" >&2
    sed -i "0,/^name:.*/s//name: ${name}/" "${TARGET_SKILLS}/${name}/SKILL.md"
  fi
  synced=$((synced + 1))
done
echo "→ ${synced} upstream skills synced" >&2

# Directories that are neither local nor upstream: report, never delete.
for local_skill in "${TARGET_SKILLS}"/*/; do
  name="$(basename "${local_skill}")"
  is_local "${name}" && continue
  [[ -d "${SRC}/${name}" ]] && continue
  echo "warning: ${name} is neither in LOCAL nor upstream — renamed or removed upstream? Review by hand." >&2
done

# MIT requires the licence text to travel with the copied skills.
if [[ -f "${TMP}/upstream/LICENSE" ]]; then
  cp "${TMP}/upstream/LICENSE" "${PLUGIN_DIR}/LICENSE-n8n-skills"
else
  echo "warning: upstream has no LICENSE file" >&2
fi

echo "${UPSTREAM_SHA}"
