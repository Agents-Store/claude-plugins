#!/usr/bin/env python3
"""PreToolUse guard for Bash: ask before a command prints decrypted vault data.

Reads the hook payload on stdin. When the Bash command would write secrets
from the Bitwarden CLI (`bw`, also `rbw get`) or from a `bw serve` endpoint into the
tool output -- and so into the conversation transcript -- it answers
`permissionDecision: "ask"` with the reason. Everything else passes silently.

Fails open: any parsing problem exits 0 without output, so a broken payload
never blocks the user's shell. No network access, no files written.
"""

import json
import re
import sys

# `bw`, then any global flags (only --session takes a value), then the subcommand.
BW = r"(?:^|[\s;|&(`!{/])bw(?:\s+(?:--session(?:=|\s+)\S+|--[\w-]+))*\s+"
SECRET_ENV = r"(?:BW_SESSION|BW_PASSWORD|BW_CLIENTSECRET|BW_CLIENT_SECRET|VW_ADMIN_TOKEN|ADMIN_TOKEN)"

# Checked only outside $(...) / `...`: inside a capture the output goes to a variable.
# A match is also skipped when its pipeline sends stdout to a file or the clipboard.
PRINTING = [
    (BW + r"list\s+items\b",
     "`bw list items` prints every matching item with its password, TOTP seed and notes"),
    (BW + r"get\s+(?:item|password|totp|notes)\b",
     "`bw get item|password|totp|notes` prints a secret into the chat"),
    (BW + r"get\s+attachment\b(?![^;|&]*--output)",
     "`bw get attachment` without --output prints the file content"),
    (BW + r"unlock\b",
     "`bw unlock` prints the session key; capture it: export BW_SESSION=\"$(bw unlock --raw ...)\""),
    (BW + r"login\b(?![^;|&]*--(?:apikey|check))",
     "`bw login` with a password prints the session key"),
    (r"(?:^|[\s;|&(/])rbw\s+get\b",
     "`rbw get` prints the password into the chat"),
    (r"/(?:object/(?:item|password|totp|notes)/|list/object/items\b)",
     "this `bw serve` endpoint returns decrypted secrets"),
    (r"\bprintenv\s+" + SECRET_ENV + r"\b",
     "this prints a vault credential from the environment"),
]

# echo/printf of a credential variable: fine when piped into a consumer (curl, bw, ...),
# a leak when it reaches the terminal or a pass-through filter.
ECHO_SECRET = r"\b(?:echo|printf)\b[^;|&]*\$\{?" + SECRET_ENV + r"\b"
PASS_THROUGH = re.compile(r"\|\s*(?:cat|tee|less|more|head|tail|grep|sed|awk|cut|tr|sort|uniq|rev|fold|"
                          r"xxd|od|hexdump|base64|jq|column|nl)\b")

# Checked on the whole command, captured or not.
ALWAYS = [
    (BW + r"export\b(?![^;|&]*--format\s+['\"]?encrypted_json)",
     "`bw export` writes the whole vault in plain text (use --format encrypted_json for backups)"),
    (BW + r"serve\b[^;|&]*--disable-origin-protection",
     "`bw serve --disable-origin-protection` lets any web page read the unlocked vault"),
    (BW + r"serve\b[^;|&]*--hostname\s+['\"]?(?!localhost\b|127\.0\.0\.1\b|::1\b)[^\s'\"]+",
     "`bw serve` bound beyond localhost exposes the unlocked vault on the network"),
    (r"\b(?:echo|printf)\b[^;|&]*\$\(\s*(?:\S*/)?r?bw\s+(?:[^)]*\s)?"
     r"(?:get\s+(?:item|password|totp|notes)|list\s+items|unlock|login)\b",
     "a captured `bw` secret is printed straight back by echo/printf"),
    (r"<<<\s*[\"']?\$\(\s*(?:\S*/)?r?bw\b",
     "a captured `bw` secret is printed straight back through a here-string"),
]

# Rest of a pipeline element (up to ; && || or newline) that keeps stdout off the terminal.
SILENCED = re.compile(r"(?:^|(?<=\s))>>?\s*[^&\s|]|&>|\|\s*(?:pbcopy|xclip|xsel|wl-copy|clip(?:\.exe)?)\b")



def strip_captures(cmd):
    """Blank out $(...), <(...) and `...` bodies so their output counts as captured."""
    out = list(cmd)
    i, n = 0, len(cmd)
    while i < n:
        if cmd.startswith(("$(", "<("), i) and not cmd.startswith("$((", i):
            depth, j = 1, i + 2
            while j < n and depth:
                if cmd[j] == "(":
                    depth += 1
                elif cmd[j] == ")":
                    depth -= 1
                j += 1
            for k in range(i + 2, max(i + 2, j - 1)):
                out[k] = " "
            i = j
        elif cmd[i] == "`":
            j = cmd.find("`", i + 1)
            if j == -1:
                break
            for k in range(i + 1, j):
                out[k] = " "
            i = j + 1
        else:
            i += 1
    return "".join(out)


def reasons_for(cmd):
    found = []
    outside = strip_captures(cmd)
    for pattern, reason in PRINTING:
        for m in re.finditer(pattern, outside):
            rest = re.split(r";|&&|\|\||\n", outside[m.end():], maxsplit=1)[0]
            if not SILENCED.search(rest):
                found.append(reason)
                break
    for m in re.finditer(ECHO_SECRET, outside):
        rest = re.split(r";|&&|\|\||\n", outside[m.end():], maxsplit=1)[0]
        piped = re.search(r"(?<!\|)\|(?!\|)", rest)
        if SILENCED.search(rest) or (piped and not PASS_THROUGH.search(rest)):
            continue
        found.append("this prints a vault credential from the environment")
        break
    for pattern, reason in ALWAYS:
        if re.search(pattern, cmd):
            found.append(reason)
    return found


def main():
    try:
        payload = json.load(sys.stdin)
        if payload.get("tool_name") != "Bash":
            return 0
        cmd = (payload.get("tool_input") or {}).get("command") or ""
        if not isinstance(cmd, str) or not re.search(r"r?bw\b|BW_|ADMIN_TOKEN|object/", cmd):
            return 0
        found = reasons_for(cmd)
    except Exception:
        return 0
    if not found:
        return 0
    reason = (
        "vaultwarden-dev guard: " + "; ".join(dict.fromkeys(found)) + ". "
        "Output of this command lands in the conversation transcript. Prefer a filtered "
        "or captured form, e.g. DB_PASS=\"$(bw get password <item-id>)\" or "
        "bw list items --search <text> | jq '.[] | {id, name}'."
    )
    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "ask",
            "permissionDecisionReason": reason,
        }
    }, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
