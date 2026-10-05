#!/usr/bin/env bash
# tests/plugins/session-doctor-dev/sections.test.sh — тесты новых разделов session-doctor-dev
# (doctor_events и далее). Свой фикстурный профиль Claude Code: транскрипт main + субагент.
# Поддельные токены собираются конкатенацией в рантайме — ни одного литерала-секрета в файле.
# Без сети, без записи за пределами temp. Запуск: bash tests/plugins/session-doctor-dev/sections.test.sh
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
SCRIPTS="$ROOT/plugins/session-doctor-dev/skills/audit/scripts"
SCRIPT="$SCRIPTS/session_doctor.py"

PASS=0
FAIL=0

ok()  { PASS=$((PASS + 1)); printf '  ✓ %s\n' "$1"; }
bad() { FAIL=$((FAIL + 1)); printf '  ✗ %s\n' "$1"; }

assert_contains() { case "$2" in *"$1"*) ok "$3" ;; *) bad "$3 — не найдено: $1" ;; esac; }
assert_missing()  { case "$2" in *"$1"*) bad "$3 — ложное срабатывание: $1" ;; *) ok "$3" ;; esac; }
assert_eq()       { if [ "$1" = "$2" ]; then ok "$3"; else bad "$3 — ожидалось '$1', получено '$2'"; fi; }

for bin in python3 jq; do
  command -v "$bin" >/dev/null 2>&1 || { echo "  ✗ нужен $bin"; exit 1; }
done

T="$(mktemp -d)"
trap 'rm -rf "$T"' EXIT

SID="aaaaaaaa-1111-2222-3333-444444444444"
SID2="bbbbbbbb-1111-2222-3333-444444444444"
SID3="cccccccc-1111-2222-3333-444444444444"
SID4="dddddddd-1111-2222-3333-444444444444"
SID5="eeeeeeee-1111-2222-3333-444444444444"
PROJ="$T/projects/demo"
CFG="$T/home/.claude-test"
SLUG="$(printf '%s' "$PROJ" | sed 's/[^A-Za-z0-9]/-/g')"
TR="$CFG/projects/$SLUG/$SID.jsonl"
TR2="$CFG/projects/$SLUG/$SID2.jsonl"
TR3="$CFG/projects/$SLUG/$SID3.jsonl"
TR4="$CFG/projects/$SLUG/$SID4.jsonl"
TR5="$CFG/projects/$SLUG/$SID5.jsonl"
TOKB="ghp_""$(printf 'B%.0s' {1..36})"        # secret inside a Bash stdout, runtime-built
TOKH="ghp_""$(printf 'H%.0s' {1..36})"        # secret in a request URL / userinfo, runtime-built
TOKA="ghp_""$(printf 'A%.0s' {1..36})"        # assembled at runtime, never a literal credential
TOKREJ="ey""J""$(printf 'r%.0s' {1..14})"".""$(printf 'e%.0s' {1..14})"".""$(printf 'j%.0s' {1..10})"   # JWT-shaped, rejected (401)
TOKOK="okkey_""$(printf 'K%.0s' {1..24})"     # accepted (200), sent as x-api-key
TOKVAR="cmsval_""$(printf 'V%.0s' {1..20})"   # lives only in the fixture settings env as CMS_TOKEN
TOKLIT="qqqpa"'$'"sw0rd""$(printf 'S%.0s' {1..8})""Tail9"   # LITERAL credential with a $ inside (not a variable)
TOKQ1="quoteaa""$(printf 'a%.0s' {1..8})"     # two adjacent quoted runs of ONE header value:
TOKQ2="quotebb""$(printf 'b%.0s' {1..8})"     #   'x-api-key: <Q1>'"<Q2>" — neither is a substring of the joined value
TOKW="webonly_""$(printf 'W%.0s' {1..20})"    # query secret in a WebFetch url only: scrubbed, never a row

# ── фикстуры ────────────────────────────────────────────────────────────
make_events_fixture() {
  mkdir -p "$PROJ" "$CFG/projects/$SLUG/$SID/subagents"
  cat > "$TR" <<JSONL
{"type":"user","sessionId":"$SID","cwd":"$PROJ","version":"2.1.289","timestamp":"2026-10-04T10:00:00.000Z","message":{"role":"user","content":"<command-message>model</command-message>\n<command-name>/model</command-name>"}}
{"type":"attachment","timestamp":"2026-10-04T10:00:01.000Z","attachment":{"type":"skill_listing","names":["local-skill","hooky:greet"]}}
{"type":"attachment","timestamp":"2026-10-04T10:00:02.000Z","attachment":{"type":"unknown_command_fallback","commandName":"nope:cmd"}}
{"type":"attachment","timestamp":"2026-10-04T10:00:03.000Z","attachment":{"type":"deferred_tools_delta","needsAuthMcpServers":["x"],"failedMcpServers":[{"name":"cms","errorCode":"INVALID_CONFIG","error":"bad url"}]}}
{"type":"attachment","timestamp":"2026-10-04T10:00:04.000Z","attachment":{"type":"invoked_skills","skills":[{"name":"local-skill","path":"/p/SKILL.md","content":"BODYMARK"}]}}
{"type":"assistant","timestamp":"2026-10-04T10:00:05.000Z","message":{"id":"m1","content":[{"type":"text","text":"go"}]}}
{"type":"assistant","timestamp":"2026-10-04T10:00:05.100Z","message":{"id":"m1","content":[{"type":"tool_use","id":"t1","name":"WebFetch","input":{"url":"https://example.test/x"}}]}}
{"type":"assistant","timestamp":"2026-10-04T10:00:05.200Z","message":{"id":"m1","content":[{"type":"tool_use","id":"t1","name":"WebFetch","input":{"url":"https://example.test/x"}}]}}
{"type":"user","timestamp":"2026-10-04T10:00:06.000Z","toolUseResult":{"code":404,"url":"https://example.test/x"},"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"t1","is_error":true,"content":"Request failed with status code 404 token=$TOKA"}]}}
{"type":"user","isMeta":true,"timestamp":"2026-10-04T10:00:07.000Z","message":{"role":"user","content":[{"type":"text","text":"Base directory for this skill: /p/skills/local-skill\n\nbody"}]}}
{"type":"system","subtype":"api_error","timestamp":"2026-10-04T10:00:08.000Z","retryAttempt":2,"error":{"status":529,"message":"overloaded"}}
{"type":"assistant","timestamp":"2026-10-04T10:00:09.000Z","isApiErrorMessage":true,"apiErrorStatus":429,"error":"rate_limit","message":{"id":"m2","content":[{"type":"text","text":"API Error"}]}}
{"type":"assistant","timestamp":"2026-10-04T10:00:09.500Z","message":{"id":"m3","content":[{"type":"tool_use","id":"t9","name":"Bash","input":{"command":"env"}}]}}
{"type":"user","timestamp":"2026-10-04T10:00:09.600Z","toolUseResult":{"stdout":"LEAKMARK $TOKB","stderr":"","interrupted":false,"durationMs":12},"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"t9","content":"ok"}]}}
{"type":"assistant","timestamp":"2026-10-04T10:00:09.700Z","message":{"id":"m4","content":[{"type":"tool_use","id":"t8","name":"mcp__x__y","input":{}}]}}
{"type":"user","timestamp":"2026-10-04T10:00:09.800Z","toolUseResult":"Error: boom token=$TOKB","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"t8","is_error":true,"content":"Error: boom"}]}}
{"type":"user","timestamp":"2026-10-04T10:00:09.900Z","message":{"role":"user","content":"<command-name>/clear</command-name>\n<command-message>clear</command-message>"}}
{"type":"user","timestamp":"2026-10-04T10:00:09.950Z","message":{"role":"user","content":"look: <command-name>/quoted</command-name>"}}
{"type":"file-history-snapshot","messageId":"x"}
JSONL
  local sub="$CFG/projects/$SLUG/$SID/subagents/agent-abc123"
  cat > "$sub.jsonl" <<'JSONL'
{"type":"assistant","isSidechain":true,"timestamp":"2026-10-04T10:00:05.500Z","message":{"id":"s1","content":[{"type":"tool_use","id":"u1","name":"Bash","input":{"command":"ls"}}]}}
{"type":"user","isSidechain":true,"timestamp":"2026-10-04T10:00:05.600Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"u1","content":[{"type":"text","text":"file.txt"}]}]}}
JSONL
  printf '{"agentType":"reviewer","description":"Review"}\n' > "$sub.meta.json"
}

# Профиль, где нераспознанных записей больше половины: 3 из 4.
make_garbage_fixture() {
  cat > "$TR2" <<JSONL
{"type":"user","sessionId":"$SID2","cwd":"$PROJ","timestamp":"2026-10-04T10:00:00.000Z","message":{"role":"user","content":"hi"}}
{"type":"weird-one","timestamp":"2026-10-04T10:00:01.000Z"}
{"type":"weird-two","timestamp":"2026-10-04T10:00:02.000Z"}
{"type":"weird-three","timestamp":"2026-10-04T10:00:03.000Z"}
JSONL
}

# Профиль навыков: slash пользователя, Skill модели, Skill субагента, встроенные команды, цитата.
make_skills_fixture() {
  mkdir -p "$CFG/projects/$SLUG/$SID3/subagents"
  cat > "$TR3" <<JSONL
{"type":"user","sessionId":"$SID3","cwd":"$PROJ","timestamp":"2026-10-04T11:00:00.000Z","message":{"role":"user","content":"<command-message>model</command-message>\n<command-name>/model</command-name>"}}
{"type":"attachment","timestamp":"2026-10-04T11:00:01.000Z","attachment":{"type":"skill_listing","names":["listed-skill","dual"]}}
{"type":"user","timestamp":"2026-10-04T11:00:01.500Z","message":{"role":"user","content":"<command-name>/clear</command-name>\n<command-message>clear</command-message>"}}
{"type":"user","timestamp":"2026-10-04T11:00:01.600Z","message":{"role":"user","content":"<command-message>compact</command-message>\n<command-name>/compact</command-name>"}}
{"type":"user","timestamp":"2026-10-04T11:00:02.000Z","message":{"role":"user","content":"<command-message>plugin-dev:create-plugin</command-message>\n<command-name>/plugin-dev:create-plugin</command-name>"}}
{"type":"user","isMeta":true,"timestamp":"2026-10-04T11:00:03.000Z","message":{"role":"user","content":[{"type":"text","text":"Base directory for this skill: /p/skills/create-plugin\n\nbody"}]}}
{"type":"user","timestamp":"2026-10-04T11:00:04.000Z","message":{"role":"user","content":"<command-name>/listed-skill</command-name>"}}
{"type":"user","timestamp":"2026-10-04T11:00:05.000Z","message":{"role":"user","content":"<command-name>/dual</command-name>"}}
{"type":"assistant","timestamp":"2026-10-04T11:00:06.000Z","message":{"id":"a1","content":[{"type":"tool_use","id":"k1","name":"Skill","input":{"skill":"superpowers:brainstorming"}}]}}
{"type":"user","timestamp":"2026-10-04T11:00:06.500Z","toolUseResult":{"success":true,"commandName":"superpowers:brainstorming"},"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"k1","content":"Launching skill"}]}}
{"type":"assistant","timestamp":"2026-10-04T11:00:07.000Z","message":{"id":"a2","content":[{"type":"tool_use","id":"k2","name":"Skill","input":{"skill":"superpowers:brainstorming"}}]}}
{"type":"user","timestamp":"2026-10-04T11:00:07.500Z","toolUseResult":{"success":true},"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"k2","content":"Launching skill"}]}}
{"type":"assistant","timestamp":"2026-10-04T11:00:08.000Z","message":{"id":"a3","content":[{"type":"tool_use","id":"k3","name":"Skill","input":{"skill":"forky"}}]}}
{"type":"user","timestamp":"2026-10-04T11:00:08.500Z","toolUseResult":{"success":true,"status":"forked","commandName":"forky"},"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"k3","content":"forked"}]}}
{"type":"assistant","timestamp":"2026-10-04T11:00:09.000Z","message":{"id":"a4","content":[{"type":"tool_use","id":"k4","name":"Skill","input":{"skill":"broken-skill"}}]}}
{"type":"user","timestamp":"2026-10-04T11:00:09.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"k4","is_error":true,"content":"Unknown skill"}]}}
{"type":"assistant","timestamp":"2026-10-04T11:00:09.700Z","message":{"id":"a5","content":[{"type":"tool_use","id":"k5","name":"Skill","input":{"skill":"dual"}}]}}
{"type":"user","timestamp":"2026-10-04T11:00:09.800Z","toolUseResult":{"success":true},"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"k5","content":"ok"}]}}
{"type":"attachment","timestamp":"2026-10-04T11:00:10.000Z","attachment":{"type":"invoked_skills","skills":[{"name":"compacted-skill","path":"/p/c/SKILL.md","content":"X"},{"name":"superpowers:brainstorming","path":"/p/b/SKILL.md"}]}}
{"type":"user","timestamp":"2026-10-04T11:00:11.000Z","message":{"role":"user","content":[{"type":"text","text":"see <command-name>/foo</command-name> in docs"}]}}
{"type":"user","timestamp":"2026-10-04T11:00:12.000Z","message":{"role":"user","content":"pasted: <command-name>/foo</command-name> in docs"}}
JSONL
  local sub="$CFG/projects/$SLUG/$SID3/subagents/agent-def456"
  cat > "$sub.jsonl" <<'JSONL'
{"type":"assistant","isSidechain":true,"timestamp":"2026-10-04T11:00:06.200Z","message":{"id":"r1","content":[{"type":"tool_use","id":"r1t","name":"Skill","input":{"skill":"review-skill"}}]}}
{"type":"user","isSidechain":true,"timestamp":"2026-10-04T11:00:06.300Z","toolUseResult":{"success":true},"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"r1t","content":"ok"}]}}
JSONL
  printf '{"agentType":"reviewer","description":"Review"}\n' > "$sub.meta.json"
}

# Профиль HTTP: curl с кодом и без, WebFetch 404/err, MCP 401, цепочка с git/npm, curl-ошибка, gh, python, api_error с ретраями.
make_http_fixture() {
  cat > "$TR4" <<JSONL
{"type":"user","sessionId":"$SID4","cwd":"$PROJ","timestamp":"2026-10-04T12:00:00.000Z","message":{"role":"user","content":"go"}}
{"type":"assistant","timestamp":"2026-10-04T12:00:01.000Z","message":{"id":"h1","content":[{"type":"tool_use","id":"c1","name":"Bash","input":{"command":"curl -s -w '%{http_code}' -o /dev/null https://api.example.test/v1/x"}}]}}
{"type":"user","timestamp":"2026-10-04T12:00:01.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"c1","content":"200"}]}}
{"type":"assistant","timestamp":"2026-10-04T12:00:02.000Z","message":{"id":"h2","content":[{"type":"tool_use","id":"c2","name":"Bash","input":{"command":"curl https://api.example.test/v1/y"}}]}}
{"type":"user","timestamp":"2026-10-04T12:00:02.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"c2","content":"{\"ok\":true,\"n\":404}"}]}}
{"type":"assistant","timestamp":"2026-10-04T12:00:03.000Z","message":{"id":"h3","content":[{"type":"tool_use","id":"w1","name":"WebFetch","input":{"url":"https://docs.example.test/page"}}]}}
{"type":"user","timestamp":"2026-10-04T12:00:03.500Z","toolUseResult":{"code":404,"url":"https://docs.example.test/page"},"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"w1","content":"Not found"}]}}
{"type":"assistant","timestamp":"2026-10-04T12:00:04.000Z","message":{"id":"h4","content":[{"type":"tool_use","id":"m1","name":"mcp__gh__get","input":{}}]}}
{"type":"user","timestamp":"2026-10-04T12:00:04.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"m1","is_error":true,"content":"Request failed with status code 401"}]}}
{"type":"assistant","timestamp":"2026-10-04T12:00:05.000Z","message":{"id":"h5","content":[{"type":"tool_use","id":"c3","name":"Bash","input":{"command":"git push && npm install && curl -sI https://api.example.test/v1/items/12345 | head -1"}}]}}
{"type":"user","timestamp":"2026-10-04T12:00:05.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"c3","content":"HTTP/2 503"}]}}
{"type":"assistant","timestamp":"2026-10-04T12:00:06.000Z","message":{"id":"h6","content":[{"type":"tool_use","id":"c4","name":"Bash","input":{"command":"curl -s https://nowhere.invalid/x"}}]}}
{"type":"user","timestamp":"2026-10-04T12:00:06.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"c4","content":"curl: (6) Could not resolve host: nowhere.invalid"}]}}
{"type":"assistant","timestamp":"2026-10-04T12:00:07.000Z","message":{"id":"h7","content":[{"type":"tool_use","id":"s1","name":"WebSearch","input":{"query":"something"}}]}}
{"type":"user","timestamp":"2026-10-04T12:00:07.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"s1","content":"results"}]}}
{"type":"system","subtype":"api_error","timestamp":"2026-10-04T12:00:08.000Z","retryAttempt":1,"error":{"status":529,"message":"overloaded"}}
{"type":"system","subtype":"api_error","timestamp":"2026-10-04T12:00:09.000Z","retryAttempt":2,"error":{"status":529,"message":"overloaded"}}
{"type":"system","subtype":"api_error","timestamp":"2026-10-04T12:00:10.000Z","retryAttempt":3,"error":{"status":529,"message":"overloaded"}}
{"type":"assistant","timestamp":"2026-10-04T12:00:11.000Z","message":{"id":"h8","content":[{"type":"tool_use","id":"g1","name":"Bash","input":{"command":"gh api repos/octo/demo/pulls/7"}}]}}
{"type":"user","timestamp":"2026-10-04T12:00:11.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"g1","content":"gh: Not Found (HTTP 404)"}]}}
{"type":"assistant","timestamp":"2026-10-04T12:00:12.000Z","message":{"id":"h9","content":[{"type":"tool_use","id":"p1","name":"Bash","input":{"command":"python3 -c \"import requests; requests.post('https://api.example.test/v1/z', json={})\""}}]}}
{"type":"user","timestamp":"2026-10-04T12:00:12.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"p1","content":"done"}]}}
{"type":"assistant","timestamp":"2026-10-04T12:00:13.000Z","message":{"id":"h10","content":[{"type":"tool_use","id":"w2","name":"WebFetch","input":{"url":"https://flaky.example.test/a"}}]}}
{"type":"user","timestamp":"2026-10-04T12:00:13.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"w2","is_error":true,"content":"fetch failed: ECONNRESET"}]}}
{"type":"assistant","timestamp":"2026-10-04T12:00:14.000Z","message":{"id":"h11","content":[{"type":"tool_use","id":"c5","name":"Bash","input":{"command":"curl -s -X POST -u admin:$TOKH -H 'Authorization: Bearer $TOKH' 'https://admin:$TOKH@secure.example.test/v1/users/550e8400-e29b-41d4-a716-446655440000?api_key=$TOKH' -d '{\"a\":1}'"}}]}}
{"type":"user","timestamp":"2026-10-04T12:00:14.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"c5","content":"HTTP/1.1 201 Created"}]}}
{"type":"assistant","timestamp":"2026-10-04T12:00:15.000Z","message":{"id":"h12","content":[{"type":"tool_use","id":"c6","name":"Bash","input":{"command":"git clone https://github.com/octo/demo && echo hi"}}]}}
{"type":"user","timestamp":"2026-10-04T12:00:15.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"c6","content":"Cloning"}]}}
{"type":"attachment","timestamp":"2026-10-04T12:00:20.000Z","attachment":{"type":"deferred_tools_delta","failedMcpServers":[{"name":"cms","errorCode":"502","error":"bad gateway"}]}}
{"type":"attachment","timestamp":"2026-10-04T12:00:21.000Z","attachment":{"type":"deferred_tools_delta","failedMcpServers":[{"name":"cms","errorCode":"502","error":"bad gateway"}]}}
{"type":"attachment","timestamp":"2026-10-04T12:00:22.000Z","attachment":{"type":"deferred_tools_delta","failedMcpServers":[{"name":"cms","errorCode":"502","error":"bad gateway"}]}}
JSONL
}

# Профиль токенов: 401, 200, $VAR из settings env, $VAR без значения, WebFetch с секретом в query.
make_tokens_fixture() {
  printf '{"env":{"CMS_TOKEN":"%s","SHORT_TOKEN":"abc123"}}\n' "$TOKVAR" > "$CFG/settings.json"
  cat > "$TR5" <<JSONL
{"type":"user","sessionId":"$SID5","cwd":"$PROJ","timestamp":"2026-10-04T13:00:00.000Z","message":{"role":"user","content":"go"}}
{"type":"assistant","timestamp":"2026-10-04T13:00:01.000Z","message":{"id":"k1","content":[{"type":"tool_use","id":"a1","name":"Bash","input":{"command":"curl -s -i -H \"Authorization: Bearer $TOKREJ\" https://rej.example.test/v1/items"}}]}}
{"type":"user","timestamp":"2026-10-04T13:00:01.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"a1","content":"HTTP/1.1 401 Unauthorized"}]}}
{"type":"assistant","timestamp":"2026-10-04T13:00:02.000Z","message":{"id":"k2","content":[{"type":"tool_use","id":"a2","name":"Bash","input":{"command":"curl -s -i -H \"x-api-key: $TOKOK\" https://ok.example.test/v1/ping"}}]}}
{"type":"user","timestamp":"2026-10-04T13:00:02.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"a2","content":"HTTP/2 200"}]}}
{"type":"assistant","timestamp":"2026-10-04T13:00:03.000Z","message":{"id":"k3","content":[{"type":"tool_use","id":"a3","name":"Bash","input":{"command":"curl -s -H \"Authorization: Bearer \$CMS_TOKEN\" https://cms.example.test/items"}}]}}
{"type":"user","timestamp":"2026-10-04T13:00:03.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"a3","content":"{\"data\":[]}"}]}}
{"type":"assistant","timestamp":"2026-10-04T13:00:04.000Z","message":{"id":"k4","content":[{"type":"tool_use","id":"a4","name":"Bash","input":{"command":"curl -s -H \"X-Directus-Token: \$GONE_TOKEN\" https://gone.example.test/z"}}]}}
{"type":"user","timestamp":"2026-10-04T13:00:04.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"a4","content":"{}"}]}}
{"type":"assistant","timestamp":"2026-10-04T13:00:05.000Z","message":{"id":"k5","content":[{"type":"tool_use","id":"a5","name":"WebFetch","input":{"url":"https://web.example.test/p?access_token=$TOKW"}}]}}
{"type":"user","timestamp":"2026-10-04T13:00:05.500Z","toolUseResult":{"code":200,"url":"https://web.example.test/p"},"message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"a5","content":"ok"}]}}
{"type":"assistant","timestamp":"2026-10-04T13:00:06.000Z","message":{"id":"k6","content":[{"type":"tool_use","id":"a6","name":"Bash","input":{"command":"curl -s -H \"x-api-key: $TOKLIT\" https://lit.example.test/a"}}]}}
{"type":"user","timestamp":"2026-10-04T13:00:06.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"a6","content":"{}"}]}}
{"type":"assistant","timestamp":"2026-10-04T13:00:07.000Z","message":{"id":"k7","content":[{"type":"tool_use","id":"a7","name":"Bash","input":{"command":"curl -s -H 'x-api-key: $TOKQ1'\"$TOKQ2\" https://q.example.test/b"}}]}}
{"type":"user","timestamp":"2026-10-04T13:00:07.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"a7","content":"{}"}]}}
{"type":"assistant","timestamp":"2026-10-04T13:00:08.000Z","message":{"id":"k8","content":[{"type":"tool_use","id":"a8","name":"Bash","input":{"command":"curl -s -H \"Authorization: Bearer \$SHORT_TOKEN\" https://short.example.test/c"}}]}}
{"type":"user","timestamp":"2026-10-04T13:00:08.500Z","message":{"role":"user","content":[{"type":"tool_result","tool_use_id":"a8","content":"{}"}]}}
JSONL
}

make_events_fixture
make_garbage_fixture
make_skills_fixture
make_http_fixture
make_tokens_fixture

doctor() {
  env -i HOME="$T/home" PATH="$PATH" PYTHONIOENCODING=utf-8 \
    CLAUDE_CONFIG_DIR="$CFG" CLAUDE_CODE_SESSION_ID="${SESSION:-$SID}" \
    python3 "$SCRIPT" --cwd "$PROJ" "$@"
}

py() { (cd "$SCRIPTS" && env -i HOME="$T/home" PATH="$PATH" PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1 \
  python3 -c "$1" 2>&1); }

# ═══ section: events ═════════════════════════════════════════════════════════
echo "▸ doctor_events"
JSON="$(doctor --json)"
EV="$(printf '%s' "$JSON" | jq '.events.events | length')"
assert_eq "yes" "$([ "${EV:-0}" -ge 6 ] && echo yes || echo no)" "события собраны из main и субагента"
assert_eq "0" "$(printf '%s' "$JSON" | jq '[.findings[]|select(.id=="EVENTS_FORMAT")]|length')" "валидный транскрипт — без EVENTS_FORMAT"

ek() { printf '%s' "$JSON" | jq -r "$1"; }
assert_eq "1" "$(ek '[.events.events[]|select(.kind=="tool" and .name=="WebFetch")]|length')" "tool_use дедуплицирован по id"
assert_eq "404 true" "$(ek '.events.events[]|select(.kind=="tool" and .name=="WebFetch")|"\(.tool_result.code) \(.is_error)"')" "toolUseResult и is_error привязаны к tool_use"
assert_missing "$TOKA" "$JSON" "токен в result_text не попал в отчёт"
assert_eq "reviewer" "$(ek '.events.events[]|select(.kind=="tool" and .input.command=="ls")|.actor')" "актёр субагента — agentType из meta.json"
assert_eq "file.txt" "$(ek '.events.events[]|select(.input.command=="ls")|.result_text')" "результат-список блоков склеен в текст"
assert_eq "/model /clear" "$(ek '[.events.events[]|select(.kind=="slash")|.command]|join(" ")')" "slash: <command-message> и <command-name> первым; цитата в середине игнорируется"
assert_missing "LEAKMARK" "$JSON" "длинный stdout из toolUseResult не попал в --json"
assert_missing "$TOKB" "$JSON" "секрет из stdout/строкового toolUseResult не попал в --json"
assert_eq "12" "$(ek '.events.events[]|select(.name=="Bash" and .input.command=="env")|.tool_result.durationMs')" "toolUseResult урезан до скаляров (durationMs остался)"
assert_eq "null" "$(ek '.events.events[]|select(.name=="Bash" and .input.command=="env")|.tool_result.stdout')" "stdout не хранится"
assert_eq "Error: boom token=***" "$(ek '.events.events[]|select(.name=="mcp__x__y")|.tool_result.text')" "строковый toolUseResult -> {text} с редактированием"
assert_eq "local-skill hooky:greet" "$(ek '.events.events[]|select(.kind=="listing")|.names|join(" ")')" "listing: имена навыков"
assert_eq "nope:cmd" "$(ek '.events.events[]|select(.kind=="unknown_command")|.command')" "unknown_command_fallback"
assert_eq "cms INVALID_CONFIG" "$(ek '.events.events[]|select(.kind=="mcp_connect")|"\(.name) \(.error_code)"')" "mcp_connect из failedMcpServers"
assert_eq "local-skill /p/SKILL.md" "$(ek '.events.events[]|select(.kind=="invoked_skills")|.skills[0]|"\(.name) \(.path)"')" "invoked_skills: имя и путь"
assert_missing "BODYMARK" "$JSON" "тело invoked_skills не хранится"
assert_eq "1" "$(ek '[.events.events[]|select(.kind=="skill_body")]|length')" "skill_body найден по Base directory"
assert_eq "529:2 429:" "$(ek '[.events.events[]|select(.kind=="api_error")|"\(.status):\(.retry_attempt // "")"]|join(" ")')" "api_error: system и isApiErrorMessage"
assert_eq "yes" "$(ek '.events.events|map(.ts)|. == sort|if . then "yes" else "no" end')" "события отсортированы по времени"
assert_eq "yes" "$([ "$(ek '.events.skipped')" = "0" ] && echo yes || echo no)" "служебные записи не считаются пропущенными"

OUT="$(py "
import doctor_events
class C: transcript_path=None
print(doctor_events.iter_session_files(C()), doctor_events.collect_events(C()))")"
assert_eq "[] {'events': [], 'skipped': 0, 'total': 0}" "$OUT" "без транскрипта — пустой результат"

# ═══ section: events format ══════════════════════════════════════════════════
echo "▸ EVENTS_FORMAT"
JSON2="$(SESSION="$SID2" doctor --json)"
assert_eq "1" "$(printf '%s' "$JSON2" | jq '[.findings[]|select(.id=="EVENTS_FORMAT")]|length')" "3 из 4 нераспознанных записей — EVENTS_FORMAT"
assert_eq "medium" "$(printf '%s' "$JSON2" | jq -r '.findings[]|select(.id=="EVENTS_FORMAT")|.severity')" "EVENTS_FORMAT — medium"
assert_eq "0" "$(find "$SCRIPTS" -name __pycache__ | wc -l | tr -d ' ')" "__pycache__ не создан"

# ═══ section: skills invoked ═════════════════════════════════════════════════
echo "▸ doctor_skills"
J="$(SESSION="$SID3" doctor --json)"
sk() { printf '%s' "$J" | jq -r "$1"; }
assert_contains "plugin-dev:create-plugin" "$(sk '.skills_invoked_v2.skills[].name')" "skill пользователя в списке"
assert_eq "user" "$(sk '.skills_invoked_v2.skills[]|select(.name=="plugin-dev:create-plugin")|.caller')" "slash с телом skill — caller user"
assert_contains "superpowers:brainstorming" "$(sk '.skills_invoked_v2.skills[]|select(.caller=="model").name')" "skill модели в списке"
assert_eq "0" "$(sk '[.skills_invoked_v2.skills[]|select(.name=="model")]|length')" "встроенная /model не skill"
assert_eq "2" "$(sk '[.events.events[]|select(.kind=="slash" and (.command=="/clear" or .command=="/compact"))]|length')" "фикстура: /clear и /compact есть среди slash-событий"
assert_eq "0" "$(sk '[.skills_invoked_v2.skills[]|select(.name=="clear" or .name=="compact")]|length')" "встроенные команды не skill"
assert_eq "1" "$(py "
import doctor_events
class C: transcript_path='$TR3'
a=doctor_events.events(C()); c=C(); b1=doctor_events.events(c); b2=doctor_events.events(c)
print(int(b1 is b2))")" "events(ctx) мемоизирован: один разбор на ctx"
assert_contains "reviewer" "$(sk '.skills_invoked_v2.skills[].caller')" "вызов skill субагентом атрибутирован"
assert_eq "reviewer" "$(sk '.skills_invoked_v2.skills[]|select(.name=="review-skill")|.caller')" "review-skill вызвал reviewer"
assert_eq "2 ok" "$(sk '.skills_invoked_v2.skills[]|select(.name=="superpowers:brainstorming")|"\(.count) \(.outcome)"')" "повторные вызовы сгруппированы; invoked_skills не дублирует"
assert_eq "forked" "$(sk '.skills_invoked_v2.skills[]|select(.name=="forky")|.outcome')" "status forked -> forked"
assert_eq "error" "$(sk '.skills_invoked_v2.skills[]|select(.name=="broken-skill")|.outcome')" "is_error -> error"
assert_eq "after-compact model" "$(sk '.skills_invoked_v2.skills[]|select(.name=="compacted-skill")|"\(.outcome) \(.caller)"')" "invoked_skills без своего вызова -> after-compact"
assert_eq "user" "$(sk '.skills_invoked_v2.skills[]|select(.name=="listed-skill")|.caller')" "slash без тела, но имя в listing -> skill"
assert_eq "user 2" "$(sk '.skills_invoked_v2.skills[]|select(.name=="dual")|"\(.caller) \(.count)"')" "user специфичнее model; счётчик суммируется"
assert_eq "0" "$(sk '[.skills_invoked_v2.skills[]|select(.name=="foo")]|length')" "<command-name> в цитате — не вызов"
assert_eq "yes" "$([ "$(sk '.skills_invoked_v2.skills[0].first_ts | type')" = "number" ] && echo yes || echo no)" "first_ts заполнен"
DIG="$(SESSION="$SID3" doctor)"
assert_contains "SKILLS INVOKED" "$DIG" "раздел SKILLS INVOKED в дайджесте"
TABLE="$(printf '%s\n' "$DIG" | awk '/^SKILLS INVOKED/{p=1;print;next} p&&/^  /{print;next} {p=0}')"
assert_contains "plugin-dev:create-plugin" "$TABLE" "таблица содержит skill"
assert_missing "foo" "$TABLE" "цитата не попала в таблицу"
assert_eq "0" "$(printf '%s\n' "$TABLE" | awk 'NR>1 && $1=="model"' | wc -l | tr -d ' ')" "встроенная /model не попала в таблицу"
assert_eq "0" "$(printf '%s' "$J" | jq '.errors|map(select(startswith("skills_invoked_v2")))|length')" "коллектор skills_invoked_v2 не упал"

# ═══ section: http ═══════════════════════════════════════════════════════════
echo "▸ doctor_http"
J="$(SESSION="$SID4" doctor --json)"
hq() { printf '%s' "$J" | jq -r "$1"; }
assert_contains "200" "$(hq '.http.lines[]|select(.source=="curl")|.codes|keys[]')" "curl 200 распознан (-w %{http_code})"
assert_eq "?" "$(hq '.http.lines[]|select(.path=="/v1/y")|.codes|keys[]')" "curl с JSON-телом без кода — ?"
assert_contains "404" "$(hq '.http.lines[]|select(.source=="WebFetch")|.codes|keys[]')" "WebFetch 404"
assert_contains "401" "$(hq '.http.lines[]|select(.source=="mcp")|.codes|keys[]')" "MCP 401 из текста"
assert_eq "gh get" "$(hq '.http.lines[]|select(.source=="mcp")|"\(.host) \(.path)"')" "MCP: host — сервер, path — инструмент"
assert_eq "503 1" "$(hq '.http.lines[]|select(.path=="/v1/items/:id")|"\(.codes|keys[0]) \(.count)"')" "git/npm не запросы; HTTP/2 503; числовой id -> :id"
assert_eq "HEAD" "$(hq '.http.lines[]|select(.path=="/v1/items/:id")|.method')" "curl -I — HEAD"
assert_eq "curl:6" "$(hq '.http.lines[]|select(.host=="nowhere.invalid")|.codes|keys[0]')" "сетевая ошибка curl — curl:N, не HTTP-код"
assert_eq "true" "$(hq '.http.lines[]|select(.host=="nowhere.invalid")|.has_error')" "curl:N — has_error"
assert_eq "false" "$(hq '.http.lines[]|select(.path=="/v1/x")|.has_error')" "200 — не ошибка"
assert_eq "ok" "$(hq '.http.lines[]|select(.source=="WebSearch")|.codes|keys[0]')" "WebSearch ok"
assert_eq "1 3" "$(hq '.http.lines[]|select(.source=="api")|"\(.count) \(.retries)"')" "ретраи api_error схлопнуты в одну строку"
assert_eq "529" "$(hq '.http.lines[]|select(.source=="api")|.codes|keys[0]')" "api: код из status"
assert_eq "404 api.github.com /repos/octo/demo/pulls/:id" "$(hq '.http.lines[]|select(.source=="gh")|"\(.codes|keys[0]) \(.host) \(.path)"')" "gh api: путь и код из (HTTP 404)"
assert_eq "POST" "$(hq '.http.lines[]|select(.source=="python")|.method')" "python requests.post найден в -c"
assert_eq "err" "$(hq '.http.lines[]|select(.host=="flaky.example.test")|.codes|keys[0]')" "WebFetch ECONNRESET — err"
assert_eq "201 POST secure.example.test /v1/users/:id" "$(hq '.http.lines[]|select(.host=="secure.example.test")|"\(.codes|keys[0]) \(.method) \(.host) \(.path)"')" "userinfo и query убраны, uuid -> :id, -d даёт POST"
assert_eq "0" "$(hq '[.http.lines[]|select(.host=="github.com")]|length')" "git clone не запрос"
assert_missing "$TOKH" "$(hq '.http')" "токен из URL/-u/-H не попал в .http (raw input живёт только в .events)"
DIG="$(SESSION="$SID4" doctor)"
FULL="$(SESSION="$SID4" doctor --full)"
assert_contains "HTTP REQUESTS" "$DIG" "раздел HTTP REQUESTS в дайджесте"
assert_contains "api.example.test/v1/x" "$FULL" "full: запросы по времени"
assert_missing "$TOKH" "$DIG$FULL" "токен не попал в дайджест и full"
assert_eq "0" "$(printf '%s' "$J" | jq '.errors|map(select(startswith("http")))|length')" "коллектор http не упал"
assert_eq "1" "$(py "
import doctor_http as h
print(int(h.parse_curl('curl -k -XPUT -H \"X-A: b\" -u me:pw --url https://h.test/p')=={'method':'PUT','url':'https://h.test/p','headers':{'x-a':'b'},'user':'me:pw','insecure':True}))")" "parse_curl: короткие флаги, --url, заголовки в нижнем регистре"
assert_eq "1" "$(py "
import doctor_http as h
print(int(h.parse_curl('curl --version') is None and h.parse_curl('curl \$BASE/x')['url']=='\$BASE/x'))")" "parse_curl: без URL — None; \$VAR-URL принят"

assert_eq "1" "$(hq '[.http.lines[]|select(.source=="mcp-connect" and .host=="cms")]|length')" "упавший MCP — одна строка, не три"
assert_contains "502" "$(hq '.http.lines[]|select(.source=="mcp-connect")|.codes|keys[]')" "errorCode в строке"
assert_eq "1 true" "$(hq '.http.lines[]|select(.source=="mcp-connect" and .host=="cms")|"\(.count) \(.has_error)"')" "mcp-connect: count 1, has_error"
assert_contains "cms" "$(SESSION="$SID4" doctor)" "упавший MCP виден в коротком дайджесте"

# ═══ section: tokens ═════════════════════════════════════════════════════════
echo "▸ doctor_tokens"
J="$(SESSION="$SID5" doctor --json)"
tk() { printf '%s' "$J" | jq -r "$1"; }
ids_of() { printf '%s' "$1" | jq -r '.findings[].id'; }
assert_contains "❌" "$(tk '.tokens.tokens[]|select(.codes["401"])|.verdict')" "токен с 401 — не принят"
assert_contains "TOKEN_REJECTED" "$(ids_of "$J")" "находка TOKEN_REJECTED"
assert_eq "high" "$(tk '.findings[]|select(.id=="TOKEN_REJECTED")|.severity')" "TOKEN_REJECTED — high"
assert_contains "✅" "$(tk '.tokens.tokens[]|select(.codes["200"])|.verdict')" "токен с 200 — принимался"
assert_contains "CMS_TOKEN" "$(tk '.tokens.tokens[].var')" "токен из \$VAR опознан по имени переменной"
assert_eq "yes" "$([ "$(tk '.tokens.tokens[]|select(.var=="CMS_TOKEN")|.fp|length')" = "8" ] && echo yes || echo no)" "\$VAR из settings env разрешён: fp из 8 hex"
assert_contains "кода про токен нет" "$(tk '.tokens.tokens[]|select(.var=="CMS_TOKEN")|.verdict')" "разрешённый токен без кода — кода про токен нет"
assert_eq "bearer-jwt x-api-key x-api-key x-api-key" "$(tk '[.tokens.tokens[]|select(.var==null and .fp!=null)|.kind]|sort|join(" ")')" "kind по форме значения"
assert_eq "gone.example.test null" "$(tk '.tokens.tokens[]|select(.var=="GONE_TOKEN")|"\(.hosts[0]) \(.fp)"')" "неразрешённый \$VAR: имя есть, fp null"
assert_contains "не проверить" "$(tk '.tokens.tokens[]|select(.var=="GONE_TOKEN")|.verdict')" "неразрешённый \$VAR без кода — не проверить по сессии"
assert_eq "0" "$(tk '[.tokens.tokens[]|select(.fp==null and .var==null)]|length')" "без значения и без имени — не строка"
assert_eq "0" "$(tk '[.tokens.tokens[]|select(.hosts|index("web.example.test"))]|length')" "токен только в WebFetch — не строка"
assert_eq "7" "$(tk '.tokens.tokens|length')" "ровно семь токенов: 401, 200, CMS_TOKEN, GONE_TOKEN, литерал с \$, два куска, SHORT_TOKEN"
assert_contains "TOKEN_UNVERIFIED" "$(ids_of "$J")" "находка TOKEN_UNVERIFIED для токенов без кода"
assert_eq "info" "$(tk '.findings[]|select(.id=="TOKEN_UNVERIFIED")|.severity')" "TOKEN_UNVERIFIED — info"
# the big one: no value, anywhere (--json includes the raw tool input)
assert_missing "$TOKREJ" "$J" "значение отклонённого токена не напечатано (--json)"
assert_missing "$TOKOK" "$J" "значение рабочего токена не напечатано (--json)"
assert_missing "$TOKVAR" "$J" "значение токена из settings env не напечатано (--json)"
assert_missing "$TOKW" "$J" "секрет из query WebFetch стёрт из --json"
# fix round 1: a literal with a $ inside is a literal, not a variable; quote-concatenated values are scrubbed
assert_missing "$TOKLIT" "$J" "литерал с \$ внутри не напечатан (--json)"
assert_missing "sw0rd" "$J" "ни хвост, ни середина литерала с \$ не напечатаны (--json)"
assert_eq "0" "$(tk '[.tokens.tokens[]|select(.var!=null and (.var|test("sw0rd|SSSS|Tail9")))]|length')" "var не содержит часть значения литерала"
assert_eq "CMS_TOKEN GONE_TOKEN SHORT_TOKEN" "$(tk '[.tokens.tokens[].var // empty]|sort|join(" ")')" "var — только настоящие имена переменных"
assert_eq "1" "$(tk '[.tokens.tokens[]|select(.hosts==["lit.example.test"] and .var==null and (.fp|length)==8)]|length')" "литерал с \$ — строка с fp и без var"
assert_missing "$TOKQ1" "$J" "первый кусок значения из двух кавычек не напечатан (--json)"
assert_missing "$TOKQ2" "$J" "второй кусок значения из двух кавычек не напечатан (--json)"
assert_eq "1" "$(tk '[.tokens.tokens[]|select(.hosts==["q.example.test"] and (.fp|length)==8)]|length')" "значение из двух кавычек — одна строка"
assert_eq "null" "$(tk '.tokens.tokens[]|select(.var=="SHORT_TOKEN")|.fp')" "значение короче 8 — строка есть, fp null"
DIG="$(SESSION="$SID5" doctor)"
FULL="$(SESSION="$SID5" doctor --full)"
assert_missing "$TOKLIT" "$DIG$FULL" "литерал с \$ не в дайджесте и full"
assert_missing "sw0rd" "$DIG$FULL" "хвост литерала не в дайджесте и full (TOKEN_REJECTED/раздел)"
assert_missing "$TOKQ1" "$DIG$FULL" "кусок 1 не в дайджесте и full"
assert_missing "$TOKQ2" "$DIG$FULL" "кусок 2 не в дайджесте и full"
assert_contains "TOKENS" "$DIG" "раздел TOKENS в дайджесте"
assert_contains "❌ не принят" "$DIG" "дайджест: строка с вердиктом ❌"
assert_missing "$TOKREJ" "$DIG$FULL" "значение отклонённого токена не в дайджесте и full"
assert_missing "$TOKOK" "$DIG$FULL" "значение рабочего токена не в дайджесте и full"
assert_missing "$TOKVAR" "$DIG$FULL" "значение токена из settings env не в дайджесте и full"
assert_eq "0" "$(printf '%s' "$J" | jq '.errors|map(select(startswith("tokens")))|length')" "коллектор tokens не упал"
assert_eq "0" "$(py "
import doctor_tokens as t
print(sum(1 for m in ('urllib.request','socket','http.client') if m in __import__('sys').modules))")" "doctor_tokens не тянет сетевые модули"
assert_eq "0" "$(find "$SCRIPTS" -name __pycache__ | wc -l | tr -d ' ')" "__pycache__ не создан"

# ── SKILL.md: контракт отчёта (Task 8) ──────────────────────────────────────
SKILLMD="$SCRIPTS/../SKILL.md"
S="$(cat "$SKILLMD")"
SHEAD="$(sed -n '1,8p' "$SKILLMD")"
assert_contains "name: audit" "$SHEAD" "SKILL.md: frontmatter name: audit"
assert_contains "### Skills" "$S" "шаблон отчёта: таблица Skills"
assert_contains "### HTTP" "$S" "шаблон отчёта: таблица HTTP"
assert_contains "### Tokens" "$S" "шаблон отчёта: таблица Tokens"
assert_contains "This audit makes no network requests; token status is read from the codes requests already received in this session. A token value is never printed." "$S" "гарантия: без сети, значение токена не печатается"
assert_contains "about 90 lines" "$S" "лимит длины отчёта поднят до ~90 строк"
assert_eq "audit" "$(jq -r .skill_name "$SCRIPTS/../evals/evals.json")" "evals.json: skill_name == audit"
DIG="$(SESSION="$SID3" doctor)"
assert_contains "TOKENS" "$DIG" "дайджест фикстуры отдаёт раздел TOKENS"
assert_contains "HTTP" "$DIG" "дайджест фикстуры отдаёт раздел HTTP"
assert_contains "SKILLS" "$DIG" "дайджест фикстуры отдаёт раздел SKILLS"

assert_contains "SKILLS INVOKED" "$S" "SKILL.md: метка блока SKILLS INVOKED"
assert_contains "HTTP REQUESTS" "$S" "SKILL.md: метка блока HTTP REQUESTS"
assert_contains "never infer or guess a token's validity" "$S" "SKILL.md: статус токена только из кодов"
AREAS="$(cat "$SCRIPTS/doctor_areas.py")"
assert_contains "run /session-doctor-dev:audit again" "$AREAS" "TRANSCRIPT_MISSING: fix называет /session-doctor-dev:audit"
assert_missing "/session-doctor again" "$AREAS" "TRANSCRIPT_MISSING: нет устаревшей команды /session-doctor"

# ═══ end of sections ═════════════════════════════════════════════════════════
printf '\n  итого: %d ✓, %d ✗\n' "$PASS" "$FAIL"
[ "$FAIL" -eq 0 ]
