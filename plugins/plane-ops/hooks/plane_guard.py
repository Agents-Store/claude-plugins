#!/usr/bin/env python3
"""PreToolUse guard for Plane MCP tools (stdlib only).

Reads the hook input JSON from stdin (``tool_name``, ``tool_input``) and answers with
Claude Code's PreToolUse decision format:

* destructive action  -> ``permissionDecision: "ask"``: Claude Code shows its normal
  permission dialog with the reason; the user's "yes" lets the call through. Besides the
  actions the server marks destructive, ``manage_workitems`` with a non-empty ``remove_ids``
  counts: it takes work items out of a cycle, module, milestone, initiative or release, which
  the per-operation ``remove_*`` tools did and which the dialog must keep covering.
* archive action      -> ``additionalContext`` only (a warning for Claude, no dialog).
* anything else, a tool of a server that is not Plane, or malformed input -> no output.

The guard fails open: it never exits non-zero and never prints on bad input.
Plane MCP 0.3+ exposes resource tools (``mcp__<server>__cycle`` with ``action``); older
per-operation connectors put the operation in the tool name (``mcp__<server>__delete_cycle``).
"""

import json
import re
import sys

# Actions that upstream (plane-mcp-server) marks destructive=True and the plugin guards.
DESTRUCTIVE_ACTIONS = frozenset(
    {
        "delete",
        "remove_projects",
        "remove_page",
        "remove_member",
        "detach",
        "detach_from_workitem",
        "delete_point",
        "delete_option",
        "delete_value",
        "delete_definition",
    }
)

# manage_workitems is a plural action (add_ids and/or remove_ids) that the server does not mark
# destructive; the removal half is what the old remove_* tools asked about.
UNLINK_ACTION = "manage_workitems"
UNLINK_PARAM = "remove_ids"

LEGACY_DESTRUCTIVE = re.compile(r"^(delete|remove|detach)_")
LEGACY_ARCHIVE = re.compile(r"^archive_")

# What is lost, by resource tool (resource surface) - a short, honest consequence line.
LOSS_BY_RESOURCE = {
    "project": "the whole project with its work items, cycles, modules and pages (catastrophic)",
    "cycle": "the cycle; its work items are unlinked but kept",
    "module": "the module; its work items are unlinked but kept",
    "milestone": "the milestone; its work items are unlinked but kept",
    "initiative": "the initiative (or its project links)",
    "state": "the state; move its work items to another state first",
    "label": "the label and its assignment to every work item",
    "workitem": "the work item with its comments, links, attachments and work logs",
    "workitem_type": "the work item type",
    "workitem_property": "the custom property definition or its options and values",
    "workitem_comment": "the comment",
    "workitem_link": "the link",
    "workitem_relation": "the relation or relation definition",
    "workitem_attachment": "the attachment",
    "work_log": "the time entry",
    "intake": "the intake item",
    "page": "the page permanently (only an archived page can be deleted)",
    "project_estimate": "the estimate or its points",
    "release": "the release",
    "release_tag": "the release tag",
    "release_label": "the release label or its attachment",
    "customer": "the customer record",
    "customer_property": "the customer property",
    "customer_request": "the customer request",
    "collection": "the collection or its pages and members",
    "template": "the template",
}

# What the non-"delete" destructive actions remove.
LOSS_BY_ACTION = {
    "remove_projects": "the project links to the initiative (the projects themselves are kept)",
    "remove_page": "the page from the collection (the page itself is kept)",
    "remove_member": "the member from the collection",
    "detach": "the label from the release (label and release are kept)",
    "detach_from_workitem": "the page link to the work item (page and work item are kept)",
    "delete_point": "the estimate point",
    "delete_option": "the property option",
    "delete_value": "the property value on the work item",
    "delete_definition": "the relation definition (relations that use it lose their type)",
}

# What a removal through manage_workitems takes the work items out of, by resource tool.
UNLINK_FROM = {
    "cycle": "the cycle; the work items are kept and return to the backlog",
    "module": "the module; the work items are kept in the project",
    "milestone": "the milestone; the work items are kept in the project",
    "initiative": "the initiative; the work items are kept in their projects",
    "release": "the release; the work items are kept in the project",
    "customer": "the customer record; the work items are kept in the project",
}

# Fields worth echoing to the user in the dialog; everything else (bodies, HTML) is left out.
ID_KEY = re.compile(r"(?:^|_)ids?$")
SHOWN_KEYS = ("name", "workitem_identifier")
MAX_VALUE = 60
MAX_FIELDS = 6


def _split_tool_name(tool_name):
    """Return (server, tool) for ``mcp__<server>__<tool>``, else None."""
    if not isinstance(tool_name, str) or not tool_name.startswith("mcp__"):
        return None
    server, sep, tool = tool_name[len("mcp__"):].rpartition("__")
    if not sep or not server or not tool:
        return None
    return server, tool


def _short(value):
    if isinstance(value, (list, tuple)):
        text = ", ".join(str(v) for v in value[:5])
        if len(value) > 5:
            text += ", ..."
    else:
        text = str(value)
    return text if len(text) <= MAX_VALUE else text[: MAX_VALUE - 3] + "..."


def _target(tool_input):
    """Compact 'key=value' list of the ids and names the call addresses."""
    parts = []
    for key, value in tool_input.items():
        if value in (None, "", [], {}):
            continue
        if ID_KEY.search(key) or key in SHOWN_KEYS:
            parts.append("%s=%s" % (key, _short(value)))
        if len(parts) >= MAX_FIELDS:
            break
    return ", ".join(parts) if parts else "target not named in the call"


def _is_set(value):
    """True for a value a caller really supplied: not empty, not an empty JSON array or null."""
    if value in (None, "", [], {}):
        return False
    return not (isinstance(value, str) and value.strip() in ("[]", "{}", "null"))


def _is_off(value):
    return value is False or (isinstance(value, str) and value.strip().lower() in ("false", "0"))


def decide(payload):
    """Map a hook input dict to a ``hookSpecificOutput`` dict, or None to stay silent."""
    if not isinstance(payload, dict):
        return None
    parsed = _split_tool_name(payload.get("tool_name"))
    if parsed is None:
        return None
    server, tool = parsed
    if "plane" not in server.lower():
        return None

    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        tool_input = {}
    action = tool_input.get("action")
    action = action if isinstance(action, str) else ""

    resource_surface = bool(action)
    name = "%s(action=%s)" % (tool, action) if resource_surface else tool

    if action in DESTRUCTIVE_ACTIONS or (not resource_surface and LEGACY_DESTRUCTIVE.match(tool)):
        if action == "delete":
            loss = LOSS_BY_RESOURCE.get(tool, "the addressed Plane object")
        elif resource_surface:
            loss = LOSS_BY_ACTION.get(action, "the addressed Plane object")
        else:
            loss = "the addressed Plane object (or its link to another object)"
        reason = "Plane %s is destructive. Target: %s. Removes: %s. Confirm before it runs." % (
            name,
            _target(tool_input),
            loss,
        )
        return {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }

    if action == UNLINK_ACTION and _is_set(tool_input.get(UNLINK_PARAM)):
        reason = "Plane %s removes work items. Target: %s. Removes: the listed work items from %s. Confirm before it runs." % (
            name,
            _target(tool_input),
            UNLINK_FROM.get(tool, "the container; the work items are kept in the project"),
        )
        return {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }

    if (action == "archive" and not _is_off(tool_input.get("archive"))) or (
        not resource_surface and LEGACY_ARCHIVE.match(tool)
    ):
        if tool in ("workitem", "page"):
            restore = "restore with %s(action=archive, archive=false)" % tool
        elif resource_surface:
            restore = "restore with %s(action=unarchive)" % tool
        else:
            restore = "restore with the matching unarchive call"
        extra = ""
        if tool == "cycle":
            extra = (
                " Archiving a still-running cycle ends it first;"
                " complete the sprint and transfer unfinished work items before archiving."
            )
        elif tool == "workitem":
            extra = " Only completed or cancelled work items can be archived."
        elif tool == "page":
            extra = " An archived page can then be deleted."
        context = "Plane archive requested: %s (%s). Archived objects are hidden, not deleted; %s.%s" % (
            name,
            _target(tool_input),
            restore,
            extra,
        )
        return {"hookEventName": "PreToolUse", "additionalContext": context}

    return None


def main():
    try:
        payload = json.loads(sys.stdin.read())
        result = decide(payload)
        if result is not None:
            sys.stdout.write(json.dumps({"hookSpecificOutput": result}))
            sys.stdout.write("\n")
    except Exception:  # fail open: a guard bug must never block Plane work
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
