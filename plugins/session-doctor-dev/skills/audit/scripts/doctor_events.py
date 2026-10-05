"""One typed event list over the main transcript and every subagent transcript.

Tasks that audit tools, skills, HTTP calls and tokens read report["events"] instead
of re-walking the files. Read-only: no network, no writes. An unknown record type or
an unreadable block is counted in `skipped`, never raised.
"""
import glob
import os
import re

from doctor_common import (check, collector, finding, iso_seconds, iter_jsonl, read_json,
                           redact, short, text_of)

RESULT_LIMIT = 4000
BODY_LIMIT = 4000
SKILL_BODY_PREFIX = "Base directory for this skill:"
COMMAND_NAME = re.compile(r"<command-name>\s*([^<]*?)\s*</command-name>")

# Record types Claude Code writes that carry nothing for the audit: counted, not "skipped".
HANDLED_TYPES = ("user", "assistant", "system", "attachment")
BOOKKEEPING_TYPES = frozenset((
    "summary", "file-history-snapshot", "queue-operation", "last-prompt", "permission-mode",
    "progress", "custom-title", "ai-title", "agent-name", "agent-setting", "mode", "tag",
    "pr-link", "cost-state", "worktree-state", "content-replacement", "marble-origami-commit",
    "marble-origami-snapshot", "attribution-snapshot",
))


def iter_session_files(ctx):
    """[(actor, path), ...]: ("main", transcript) first, then each subagent transcript."""
    files = []
    path = getattr(ctx, "transcript_path", None)
    if not path:
        return files
    files.append(("main", path))
    base = os.path.basename(path)
    stem = base[:-6] if base.endswith(".jsonl") else base
    sub = os.path.join(os.path.dirname(path), stem, "subagents")
    for agent in sorted(glob.glob(os.path.join(sub, "agent-*.jsonl"))):
        meta, _ = read_json(agent[:-6] + ".meta.json")
        actor = meta.get("agentType") if isinstance(meta, dict) else None
        files.append((actor if isinstance(actor, str) and actor else "subagent", agent))
    return files


def _text(value, limit):
    return redact(text_of(value) if not isinstance(value, str) else value[: limit * 2])[:limit]


TOOL_RESULT_KEYS = ("code", "codeText", "success", "status", "commandName", "bytes",
                    "durationMs", "url", "query")


def _trim_tool_result(tur):
    """A small, redacted copy of toolUseResult: scalars the audit reads, never stdout or file bodies."""
    if isinstance(tur, str):
        return {"text": short(redact(tur[: RESULT_LIMIT * 2]), RESULT_LIMIT)}
    if not isinstance(tur, dict):
        return None
    out = {}
    for key in TOOL_RESULT_KEYS:
        if key in tur:
            val = tur[key]
            if isinstance(val, str):
                out[key] = short(redact(val), 500)
            elif isinstance(val, (int, float, bool)) or val is None:
                out[key] = val
    return out


def _api_error(actor, ts, status, retry, error):
    return {"ts": ts, "actor": actor, "kind": "api_error",
            "status": status if isinstance(status, int) else None,
            "retry_attempt": retry if isinstance(retry, int) else None,
            "error": redact(str(error))[:300] if error is not None else ""}


def _attachment(actor, ts, att):
    """Events for one attachment record; unknown attachment types yield none (not an error)."""
    kind = att.get("type")
    if kind == "skill_listing":
        names = att.get("names")
        return [{"ts": ts, "actor": actor, "kind": "listing",
                 "names": [n for n in names if isinstance(n, str)] if isinstance(names, list) else []}]
    if kind == "unknown_command_fallback":
        return [{"ts": ts, "actor": actor, "kind": "unknown_command",
                 "command": str(att.get("commandName") or "")}]
    if kind == "deferred_tools_delta":
        out = []
        for srv in att.get("failedMcpServers") or []:
            if isinstance(srv, dict):
                out.append({"ts": ts, "actor": actor, "kind": "mcp_connect",
                            "name": str(srv.get("name") or ""),
                            "error_code": str(srv.get("errorCode") or ""),
                            "error": redact(str(srv.get("error") or ""))[:300]})
        return out
    if kind == "invoked_skills":
        skills = [{"name": str(s.get("name") or ""), "path": str(s.get("path") or "")}
                  for s in att.get("skills") or [] if isinstance(s, dict)]
        return [{"ts": ts, "actor": actor, "kind": "invoked_skills", "skills": skills}]
    return []


def _parse_file(actor, path):
    """Single pass over one transcript file -> (skipped, total, [event, ...])."""
    events, skipped, total = [], 0, 0
    pending = {}   # tool_use id -> its event, until the tool_result arrives
    for rec in iter_jsonl(path):
        total += 1
        rtype = rec.get("type")
        ts = iso_seconds(rec.get("timestamp")) if rec.get("timestamp") else None
        msg = rec.get("message") if isinstance(rec.get("message"), dict) else {}
        content = msg.get("content")

        if rtype == "assistant":
            if rec.get("isApiErrorMessage"):
                events.append(_api_error(actor, ts, rec.get("apiErrorStatus"), None,
                                         rec.get("error") or text_of(content)))
            if not isinstance(content, list):
                if not rec.get("isApiErrorMessage"):
                    skipped += 1
                continue
            for block in content:
                if not isinstance(block, dict):
                    skipped += 1
                    continue
                if block.get("type") != "tool_use":
                    continue
                tid = block.get("id")
                if not isinstance(tid, str) or tid in pending:
                    continue   # streaming repeats a block; first sighting wins
                inp = block.get("input")
                ev = {"ts": ts, "actor": actor, "kind": "tool", "name": str(block.get("name") or ""),
                      "input": inp if isinstance(inp, dict) else {}, "is_error": False,
                      "result_text": "", "tool_result": None}
                pending[tid] = ev
                events.append(ev)

        elif rtype == "user":
            if isinstance(content, str):
                if content.startswith(("<command-message>", "<command-name>")):
                    found = COMMAND_NAME.search(content)
                    if found and found.group(1):
                        events.append({"ts": ts, "actor": actor, "kind": "slash",
                                       "command": found.group(1), "is_meta_body_follows": False})
                continue
            if not isinstance(content, list):
                skipped += 1
                continue
            if rec.get("isMeta") and text_of(content).startswith(SKILL_BODY_PREFIX):
                events.append({"ts": ts, "actor": actor, "kind": "skill_body",
                               "text": redact(text_of(content)[:BODY_LIMIT * 2])[:BODY_LIMIT]})
                continue
            tur = rec.get("toolUseResult")
            for block in content:
                if not isinstance(block, dict):
                    skipped += 1
                    continue
                if block.get("type") != "tool_result":
                    continue
                ev = pending.get(block.get("tool_use_id"))
                if ev is None:
                    continue
                ev["is_error"] = bool(block.get("is_error"))
                ev["result_text"] = _text(block.get("content"), RESULT_LIMIT)
                ev["tool_result"] = _trim_tool_result(tur)

        elif rtype == "system":
            if rec.get("subtype") == "api_error":
                err = rec.get("error") if isinstance(rec.get("error"), dict) else {}
                events.append(_api_error(actor, ts, err.get("status"), rec.get("retryAttempt"),
                                         err.get("message") or err.get("type") or rec.get("error")))

        elif rtype == "attachment":
            att = rec.get("attachment")
            if isinstance(att, dict):
                events.extend(_attachment(actor, ts, att))
            else:
                skipped += 1

        elif rtype not in BOOKKEEPING_TYPES:
            skipped += 1
    return skipped, total, events


def _compute_events(ctx):
    events, skipped, total = [], 0, 0
    for actor, path in iter_session_files(ctx):
        file_skipped, file_total, file_events = _parse_file(actor, path)
        skipped += file_skipped
        total += file_total
        events += file_events
    events.sort(key=lambda e: (e.get("ts") is None, e.get("ts") or 0))
    return {"events": events, "skipped": skipped, "total": total}


def events(ctx):
    """The event list for this audit run, parsed once and cached on ctx (read-only, one run)."""
    cached = getattr(ctx, "_sd_events", None)
    if cached is None:
        cached = _compute_events(ctx)
        try:
            ctx._sd_events = cached
        except Exception:
            pass
    return cached


@collector("events")
def collect_events(ctx):
    return events(ctx)


@check
def events_format(report):
    ev = report.get("events") or {}
    total, skipped = ev.get("total") or 0, ev.get("skipped") or 0
    if total > 0 and skipped > total / 2:
        return [finding("medium", "EVENTS_FORMAT", "Transcript records not recognised",
                        "%d of %d records could not be read as events" % (skipped, total),
                        "Claude Code probably changed the transcript format; the tool, skill and "
                        "HTTP sections below may be incomplete. Update the session-doctor-dev plugin.")]
    return []
