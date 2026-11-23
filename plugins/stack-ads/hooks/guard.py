#!/usr/bin/env python3
"""PreToolUse guard of the stack-ads plugin.

Reads the hook event on stdin. When the call would write to an ad account, or
could start spend, it answers "ask", so the user confirms it whatever the
permission mode is. Every other call passes without a word.

The toolkit has its own guard rails (dry run on record, paused creation, budget
ceilings, --yes); this hook is a second layer for Claude Code. It also covers
what bypasses the toolkit: direct calls to an ad platform API, the Meta
command-line tool, and the write tools of the plugin's ad-platform MCP servers.

Limits, on purpose: it asks, it never blocks; it reads the command as text, so
a request assembled at run time (a URL built from pieces, a script in a file)
is out of its sight; it needs python3 on PATH (without it Claude Code reports a
hook error and the call goes ahead).
"""
import json
import os
import re
import shlex
import sys
import urllib.parse

AD_HOST = re.compile(r"graph(-video)?\.facebook\.com|mcp\.facebook\.com|graph\.instagram\.com|googleads\.googleapis\.com|"
                     r"business-api\.tiktok\.com", re.I)
GOOGLE_HOST = re.compile(r"googleads\.googleapis\.com", re.I)
# Google Ads methods that are sent as POST and only read: judged on the end of the URL path, never on its query.
GOOGLE_READ = re.compile(r":(search|searchStream|suggest\w*|generate\w+|list\w+)$")
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}
WRITE_WORD = re.compile(r"\b(POST|PUT|PATCH|DELETE)\b|\.(post|put|patch|delete)\s*\(", re.I)
# A request body in inline code, or on a client that names no method.
BODY_SIGN = re.compile(r"\b(data|json|files)=(?!=)|(?<![\w-])(-d|-F|-T|--data[\w-]*|--json|--form[\w-]*|--post-data|"
                       r"--post-file|--body-data|--body-file|--upload-file)(?![\w-])")
# The Graph API lets a parameter named method turn a GET into a write.
METHOD_OVERRIDE = re.compile(r"(^|[?&\s'\"=])_*method\s*=\s*(post|put|patch|delete)\b", re.I)
# Inline code that plainly fetches: a call of an HTTP client that can only read. A dictionary's .get() proves nothing.
PLAIN_READ = re.compile(r"\b(requests|httpx|session|client|axios|http|https)\.get\(|urlopen\(\s*(['\"])[^'\"]*\2\s*\)|"
                        r"fetch\(\s*(['\"`])[^'\"`]*\3\s*\)|Net::HTTP\.get|file_get_contents\(")
# Inline code that can send something: a second argument to urlopen, a request object, another verb, a child process.
SENDS = re.compile(r"urlopen\([^)]*,|\bRequest\(|\.(post|put|patch|delete|request|send)\(|post_form|curl_|HTTPSConnection|"
                   r"http\.client|socket\.|subprocess|os\.system|child_process|\b(exec|eval|system|popen)\(")
INTERPRETER = re.compile(r"(python[\d.]*|node|nodejs|deno|bun|ruby|php|perl|pwsh|powershell)")
SPEND_WORD = re.compile(r"\b(ACTIVE|ENABLED?)\b")
HEREDOC = re.compile(r"<<-?\s*['\"]?\w")
ASSIGNMENT = re.compile(r"[A-Za-z_]\w*=")
SHELLS = {"bash", "sh", "zsh", "dash", "ksh", "fish", "eval", "watch", "timeout", "ssh", "su", "sudo", "xargs", "env",
          "nohup", "nice", "time", "docker", "podman", "kubectl", "parallel"}
HTTPIE = {"http", "https", "xh", "xhs"}
CLIENTS = {"curl", "wget", "meta"} | HTTPIE
# curl short options that take a value: what follows them in the same token is that value, not more options.
CURL_VALUE_FLAGS = set("HouAebcmwxKErCDyYzQUPt")
META_VERBS = {"create", "update", "delete", "connect", "disconnect"}

MCP_SERVERS = {"meta-ads": "Meta", "tiktok-ads": "TikTok", "google-ads": "Google Ads"}
MCP_READ = {"get", "list", "search", "read", "check", "preview", "estimate", "recommend", "fetch", "query", "describe",
            "find", "show", "validate", "analyze", "analyse", "insight", "insights", "report", "reports", "export",
            "download", "info", "lookup", "discover", "count"}
MCP_WRITE = {"create", "update", "delete", "remove", "add", "set", "edit", "activate", "enable", "disable", "pause",
             "resume", "boost", "upload", "publish", "launch", "start", "stop", "duplicate", "clone", "copy", "archive",
             "schedule", "post", "bind", "unbind", "apply", "appeal", "manage", "authorize", "confirm", "sign",
             "transfer", "assign", "unassign", "link", "unlink", "share", "send", "submit", "replace", "toggle",
             "cancel", "change", "modify", "rename", "move", "import", "sync", "write", "put", "patch", "reset",
             "revoke", "grant", "invite", "approve", "reject", "run", "execute", "trigger", "restore", "merge",
             "increase", "decrease", "raise", "lower", "adjust", "switch", "save", "register", "subscribe",
             "unsubscribe", "exclude", "pay", "charge", "refund", "recharge", "deactivate", "terminate", "end",
             "optimize", "optimise", "fix", "tune", "scale", "refresh", "rotate", "regenerate", "clear", "purge", "drop",
             "kill", "expire", "extend", "renew", "promote", "attach", "detach", "mute", "hide", "block", "unblock",
             "convert", "migrate", "upgrade", "new", "make", "build", "init", "setup", "configure"}
# A name that joins two actions is never plainly a read: search_and_replace, get_then_cancel.
MCP_JOIN = {"and", "then", "or", "plus"}
# Product and object names of the live servers that contain a word from the lists above: Smart+ campaigns,
# product sets, event sets, upload sessions. They are read as one word, so the action in the name decides.
MCP_NOUNS = re.compile(r"(?<![a-z])(smart_plus|catalog_set|product_sets?|event_set|upload_sessions?)(?![a-z])")
# The TikTok server runs most of its tools through one dispatcher; the tool it runs is named in the input.
MCP_DISPATCHER = ("tiktok-ads", "tool_execute")
PLAIN_TOOL = re.compile(r"[a-z][a-z0-9_]*\Z")
MCP_SPEND = {"activate", "enable", "resume", "boost", "publish", "launch", "start", "status", "budget", "update",
             "increase", "raise", "toggle", "switch", "recharge", "optimize", "optimise", "scale", "promote"}

WRITES = "stack-ads: this command writes to an ad account (everything it creates stays paused)."
SPENDS = "stack-ads: this command enables ads, so spend can start. Confirm the plan and the daily budget first."
PAUSES = "stack-ads: this command pauses what the plan created in the ad account."
REMOVES = "stack-ads: this command will delete what the plan created in the ad account."
DIRECT = "stack-ads: this request writes to an ad platform API directly, outside the toolkit's guard rails.%s"


def spend(text):
    return " It may switch delivery on." if SPEND_WORD.search(text) else ""


def overrides(text):
    """True when the text carries a method override, also percent-encoded: ?method=%44ELETE, %6dethod=delete."""
    return bool(METHOD_OVERRIDE.search(urllib.parse.unquote(text)))


def reads_only(code):
    """Inline code that calls an HTTP client's plain read and nothing that could send."""
    return bool(PLAIN_READ.search(code)) and not SENDS.search(code)


def split_commands(text):
    """Cut a shell line into simple commands at unquoted ; & | ( ) ` and newlines. Also says if a quote stayed open."""
    parts, current, quote, index = [], [], None, 0
    while index < len(text):
        char = text[index]
        if quote:
            current.append(char)
            if char == "\\" and quote == '"' and index + 1 < len(text):
                index += 1
                current.append(text[index])
            elif char == quote:
                quote = None
        elif char in "'\"":
            quote = char
            current.append(char)
        elif char == "\\" and index + 1 < len(text):
            current.append(char)
            index += 1
            current.append(text[index])
        elif char in ";&|\n()`":
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
        index += 1
    parts.append("".join(current))
    return [p.strip() for p in parts if p.strip()], quote is not None


def flag(args, name):
    """True when the arguments carry the flag, whole or shortened: an older toolkit copy reads --y as --yes."""
    return any(len(arg) >= 3 and name.startswith(arg) for arg in args)


def toolkit_reason(args):
    """Verdict for arguments that follow ads.py: only a call with --yes changes anything."""
    if any(overrides(arg) for arg in args):
        return WRITES           # a Graph API read carrying method=delete: a current toolkit refuses it, an old copy sends it
    if not flag(args, "--yes"):
        return None
    words = [arg for arg in args if not arg.startswith("-")]
    launch = words[words.index("launch") + 1] if "launch" in words[:-1] else None
    if flag(args, "--activate") or launch == "activate":
        return SPENDS
    if launch == "rollback":
        return REMOVES if flag(args, "--remove") else PAUSES
    return WRITES


def curl_writes(args):
    method, data, as_query = None, False, False
    for index, arg in enumerate(args):
        following = args[index + 1] if index + 1 < len(args) else ""
        if arg.startswith("--"):
            name, _, value = arg[2:].partition("=")
            if name == "request":
                method = (value or following).upper()
            elif name == "get":
                as_query = True
            elif name.startswith(("data", "json", "form", "upload-file")):
                data = True
        elif arg.startswith("-") and len(arg) > 1:
            # Short options can be packed: -sSd, -sX POST, -XPOST, -sG.
            letters = arg[1:]
            for position, letter in enumerate(letters):
                if letter == "X":
                    method = (letters[position + 1:] or following).upper()
                    break
                if letter in "dFT":
                    data = True
                    break
                if letter == "G":
                    as_query = True
                elif letter in CURL_VALUE_FLAGS:
                    break
    if method in WRITE_METHODS:
        return True
    return data and not as_query and method is None


def wget_writes(args):
    for index, arg in enumerate(args):
        if arg.startswith(("--post-data", "--post-file", "--body-data", "--body-file")):
            return True
        if arg.startswith("--method"):
            value = arg.split("=", 1)[1] if "=" in arg else (args[index + 1] if index + 1 < len(args) else "")
            if value.upper() in WRITE_METHODS:
                return True
    return False


def httpie_writes(args):
    if any(arg.upper() in WRITE_METHODS for arg in args) or any(arg.startswith("<") for arg in args):
        return True         # a method, or a body on stdin
    return any(re.match(r"[\w.-]+(:=@?|=@?|@)(?!=)", arg) for arg in args if not arg.startswith("-"))


def client_reason(name, args, raw):
    """Verdict for a known HTTP client or the Meta tool. Returns (it handled an ad platform call, reason, it writes)."""
    if name == "meta":
        if "ads" not in args:
            return False, None, False
        verbs = [arg for arg in args if arg in META_VERBS]
        if not verbs:
            return True, None, False
        active = " It sets an active status, so spend can start." if "ACTIVE" in args else ""
        return True, "stack-ads: the Meta Ads CLI is about to %s an object in the ad account.%s" % (verbs[0], active), True
    writes = curl_writes(args) if name == "curl" else wget_writes(args) if name == "wget" else httpie_writes(args)
    hosts = [arg for arg in args if AD_HOST.search(arg)]
    if not hosts:
        return False, None, writes
    if any(overrides(arg) for arg in args):
        return True, DIRECT % spend(raw), True
    if name == "curl" and all(GOOGLE_READ.search(re.split(r"[?#]", arg)[0]) for arg in hosts if GOOGLE_HOST.search(arg)) \
            and all(GOOGLE_HOST.search(arg) for arg in hosts):
        return True, None, False
    return True, (DIRECT % spend(raw)) if writes else None, writes


def judge(segment, depth):
    """Verdict for one simple command: (reason to ask, a known tool was seen reading, facts for the cross-command rules)."""
    facts = {"assigns_host": False, "writes": False}
    try:
        tokens = shlex.split(segment, posix=True)
    except ValueError:
        return loose_reason(segment), False, facts
    names = [os.path.basename(token) for token in tokens]
    facts["assigns_host"] = any(ASSIGNMENT.match(token) and AD_HOST.search(token) for token in tokens)
    runs_a_shell = any(name in SHELLS for name in names)
    runs_code = any(INTERPRETER.fullmatch(name) for name in names)
    cleared = False
    # A whole command line passed as one argument: bash -c '...', ssh host "...", "$(...)", python3 -c "..."
    for token in tokens:
        if " " not in token and "\n" not in token:
            continue
        looks_inside = "ads.py" in token or runs_a_shell or AD_HOST.search(token) or "$(" in token or "`" in token
        inner, inner_cleared = scan(token, depth + 1) if depth < 3 and looks_inside else (None, False)
        if inner:
            return inner, False, facts
        cleared = cleared or inner_cleared
        if AD_HOST.search(token) and not inner_cleared:
            # Code handed to an interpreter can send a body without one telling word: only a plain fetch passes.
            if WRITE_WORD.search(token) or BODY_SIGN.search(token) or overrides(token) or (runs_code and not reads_only(token)):
                return DIRECT % spend(token), False, facts
    if "ads.py" in names:
        return toolkit_reason(tokens[names.index("ads.py") + 1:]), True, facts
    # A client may stand behind any wrapper and its options: timeout 30 curl, sudo -u bob curl, docker exec c curl.
    for index, name in enumerate(names):
        if name in CLIENTS:
            handled, reason, writes = client_reason(name, tokens[index + 1:], segment)
            if reason:
                return reason, False, facts
            cleared = cleared or handled
            facts["writes"] = facts["writes"] or writes
    if not cleared and AD_HOST.search(segment) and WRITE_WORD.search(segment):
        return DIRECT % spend(segment), False, facts
    facts["writes"] = facts["writes"] or bool(WRITE_WORD.search(segment))
    return None, cleared, facts


def loose_reason(text):
    """For a line whose quoting cannot be parsed: decide on its words alone, erring on the side of asking."""
    after = re.split(r"ads\.py\b", text, 1)
    if len(after) == 2:
        flags = re.findall(r"(?<![\w-])--[a-z-]+", after[1])
        if flag(flags, "--yes"):
            return SPENDS if flag(flags, "--activate") or re.search(r"\blaunch\s+activate\b", text) else WRITES
    if AD_HOST.search(text) and (WRITE_WORD.search(text) or BODY_SIGN.search(text)):
        return DIRECT % ""
    return None


def scan(command, depth=0):
    """Verdict for a command line: (reason to ask, a known tool was seen reading)."""
    command = re.sub(r"\\\r?\n", " ", str(command))      # a line continuation is one command
    segments, open_quote = split_commands(command)
    if open_quote:
        return loose_reason(command), False
    cleared, host_in_variable, writes_somewhere = False, False, False
    for segment in segments:
        reason, read, facts = judge(segment, depth)
        if reason:
            return reason, False
        cleared = cleared or read
        host_in_variable = host_in_variable or facts["assigns_host"]
        writes_somewhere = writes_somewhere or facts["writes"]
    if host_in_variable and writes_somewhere:
        return DIRECT % "", False                        # URL=<ad platform>; curl -X POST "$URL"
    if HEREDOC.search(command) and AD_HOST.search(command) and (
            WRITE_WORD.search(command) or BODY_SIGN.search(command) or not reads_only(command)):
        return DIRECT % spend(command), False            # a script fed on stdin: its lines are one program
    return None, cleared


def bash_reason(command, depth=0):
    return scan(command, depth)[0]


def mcp_reason(tool, tool_input=None):
    """Ad-platform servers of this plugin: ask for everything that is not plainly a read."""
    match = re.match(r"mcp__plugin_stack-ads_([a-z-]+)__(.+)$", tool)
    if not match or match.group(1) not in MCP_SERVERS:
        return None
    platform, name = MCP_SERVERS[match.group(1)], match.group(2)
    if (match.group(1), name) == MCP_DISPATCHER:
        name = tool_input.get("tool_name") if isinstance(tool_input, dict) else None
        if not isinstance(name, str) or not PLAIN_TOOL.match(name) or name == MCP_DISPATCHER[1]:
            return ("stack-ads: %s tool %s does not name the tool it runs. Confirm what it changes before it runs."
                    % (platform, MCP_DISPATCHER[1]))
    plain = MCP_NOUNS.sub(lambda found: found.group(0).replace("_", ""), name.lower())
    words = set(w for w in re.split(r"[^a-z]+", plain) if w)
    writes = words & MCP_WRITE
    if not writes:
        if words & MCP_READ and not words & MCP_JOIN:
            return None
        return ("stack-ads: %s tool %s is not known to be read-only. Confirm what it changes before it runs."
                % (platform, name))
    if words & MCP_SPEND:
        return "stack-ads: %s tool %s can change delivery or budget, so spend may start or grow." % (platform, name)
    return ("stack-ads: %s tool %s writes to the ad account. Create objects paused and review them before enabling."
            % (platform, name))


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        print("stack-ads guard: could not read the hook event, so this call was not checked", file=sys.stderr)
        return 0
    tool = event.get("tool_name") or ""
    reason = None
    if tool == "Bash":
        reason = bash_reason((event.get("tool_input") or {}).get("command") or "")
    elif tool.startswith("mcp__plugin_stack-ads_"):
        reason = mcp_reason(tool, event.get("tool_input"))
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "ask",
                                                 "permissionDecisionReason": reason}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
