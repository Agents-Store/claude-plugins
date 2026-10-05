# Scenario: a session with a rejected token and a failed MCP server

A longer session. A tool call kept answering 401, one MCP server never connected, and the
developer repeated the same correction several times. The audit turns this into a Problems
table with a concrete fix per row.

## Command

```
/session-doctor-dev:audit
```

## Rendered report

## Session audit — 🔴 broken: the API token is rejected (401) and the `tracker` MCP server failed to connect

| | |
|---|---|
| Where | /work/example-app · git feature/export, 7 uncommitted · 1 other live session |
| Session | 8d41b7f0 · Claude Code 2.x · cli · mode default · 2 h 10 min |
| Main model | <!-- example-only -->opus<!-- /example-only --> @ high ← `--model` flag; settings effort · settings: sonnet |
| Subagents | 3: general-purpose ×3 → sonnet @ default (asked default) ← `CLAUDE_CODE_SUBAGENT_MODEL` |
| Context | instructions 4 (≈9.4k tokens) · skills 11, 2 without description · plugins 3 · agents 5 · hooks 2 |
| MCP | 2 connected · 1 failed: tracker · 1 need auth: crm |
| Env | 21 names: 12 shell, 6 settings, 3 project · auth: API key |

### Skills
| Skill | Invoked by | × | Outcome |
|---|---|---|---|
| audit | user | 1 | completed |
| export-report | model | 2 | 1 failed (HTTP 401) |

### HTTP
| Source | Method | Host · path | × | Codes |
|---|---|---|---|---|
| Bash (curl) | GET | api.example.test · /v1/reports | 5 | 401 ×5 |
| Bash (curl) | POST | api.example.test · /v1/exports | 2 | 401 ×2 |
| MCP tracker | POST | tracker.example.com · /mcp | 3 | connection refused ×3 |
| MCP docs | POST | docs.example.com · /mcp | 9 | 200 ×9 |

### Tokens
| Kind | Variable | Fingerprint | Codes | Status |
|---|---|---|---|---|
| bearer | EXAMPLE_API_TOKEN | a1b2c3d4 | 401 ×7 | rejected |
| bearer | DOCS_MCP_TOKEN | 0f9e8d7c | 200 ×9 | accepted |

### Problems
| # | | Problem | Evidence | Fix |
|---|---|---|---|---|
| 1 | 🔴 | `EXAMPLE_API_TOKEN` is rejected by the API | 7 requests to api.example.test answered 401; fingerprint a1b2c3d4 | Issue a new token at the provider, update the variable in `.claude/settings.local.json`, restart the session |
| 2 | 🔴 | MCP server `tracker` failed to connect | 3 attempts, connection refused | Check the server URL variable and that the service is up; run `/mcp` to reconnect |
| 3 | 🟡 | MCP server `crm` waits for authentication | listed as needing auth | Run `/mcp` and authenticate `crm`, or remove it if unused |
| 4 | 🟡 | The same 401 was retried 7 times without changing anything | repeated curl calls with the same header | Stop after the first 401 and fix the token before retrying (judgment) |
| 5 | ⚪ | 2 skills have no description | context shows 2 skills without description | Add a `description` to each skill so it can trigger |

### Next step
Replace the rejected `EXAMPLE_API_TOKEN` — it blocks every call to api.example.test.

## What to notice

- The token Status is **rejected** only because every code in its row is 401; the audit never
  tested the token itself.
- The 401 rows in HTTP and the rejected row in Tokens point to the same cause, so Problems
  merges them into one row instead of listing each request.
- Rows 1-3 come from the data block, row 4 is a step-2 judgment and is marked "(judgment)".
- The model name is only an illustration of the Main model cell.
