#!/usr/bin/env python3
"""Safety gate — dangerous tricks in a plugin's code and harmful instructions in its text.

The fourth pass of ./scripts/scrub-check.sh (next to scrub_check.py, plugin_lint.py and validate_pass.py). Where the
scrub pass asks «does this leak our deployment?», this one asks «would this hurt the person who installs it?»:

  code (scripts, hooks.json, .mcp.json)      remote-exec, decode-exec, reverse-shell, secret-exfil, destroy  → FAIL
                                             secret-read, persistence, hidden-chars                          → WARN
  instructions (SKILL.md, agents, commands,  prompt-injection, hidden-chars                                  → FAIL
  references, README, CLAUDE.md)             the code tricks inside documentation (an official installer)    → WARN
  examples, everywhere                       demo-contact: a mailbox off the demo and vendor domains, a phone
                                             outside the reserved fictional ranges                           → WARN
  anything, when the owner's list exists     private-name: a name from the owner's private list, a file kept
  (~/.config/agents-store/private-names.txt  outside every repository (AGENTS_STORE_PRIVATE_NAMES overrides
                                             the path; CI has none and stays silent)                         → FAIL

demo-contact skips a plugin's vendored text ([upstream] skip_paths in tests/plugins/<p>/plugin-test.toml): that is the
vendor's own demo data and the sync overwrites ours.

--base <ref> reports only findings that are new against that commit, and every new finding is a FAIL: what is already
there does not block, everything added must be fixed or excused on its own (scripts/safety-allow.txt, own PR).

Exit: 0 clean · 1 FAIL · 2 WARN only. Rules are shapes, never literal payloads; matches are redacted in the output.
Exceptions: scripts/safety-allow.txt, `path:rule-id[#value-selector]:reason`, the same format as scrub-allow.txt.
"""
import argparse
import collections
import fnmatch
import functools
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import scrub_check  # noqa: E402 — one file walker, one baseline matcher, one redaction for all passes

REPO_ROOT = scrub_check.REPO_ROOT
DEFAULT_BASELINE = os.path.join(REPO_ROOT, "scripts", "safety-allow.txt")
DEFAULT_TARGETS = ("plugins",)
FAIL, WARN = "FAIL", "WARN"

CODE_SUFFIXES = (".sh", ".bash", ".zsh", ".py", ".js", ".mjs", ".cjs", ".ts", ".rb", ".ps1", ".pl")
CODE_BASENAMES = ("hooks.json", ".mcp.json")
DATA_SUFFIXES = (".json", ".yaml", ".yml", ".toml", ".txt")      # only private-name looks there

SHELLS = r"(?:sudo\s+(?:-\S+\s+)*)?(?:ba|z|da|k)?sh\b"
DOWNLOAD = r"\b(?:curl|wget|iwr|irm|Invoke-WebRequest|Invoke-RestMethod)\b"
RE_REMOTE_EXEC = [
    re.compile(DOWNLOAD + r"[^\n|;]*\|\s*" + SHELLS),
    re.compile(r"\b(?:ba|z)?sh\s+<\(\s*(?:curl|wget)\b|\b(?:source|\.)\s+<\(\s*(?:curl|wget)\b"),
    re.compile(r"\beval\s+[\"']?\$\(\s*(?:curl|wget)\b"),
    re.compile(r"\biex\s*\(?\s*(?:iwr|irm|Invoke-WebRequest|Invoke-RestMethod|\(New-Object\s+Net\.WebClient\))", re.I),
]
RE_DECODE_EXEC = [
    re.compile(r"\bbase64\s+(?:-d|--decode|-D)\b[^\n]*\|\s*" + SHELLS),
    re.compile(r"\bxxd\s+-r\b[^\n]*\|\s*" + SHELLS),
    re.compile(r"\beval\s*\(\s*(?:atob|Buffer\.from)\s*\("),
    re.compile(r"\bnew\s+Function\s*\(\s*atob\s*\("),
    re.compile(r"\bexec\s*\(\s*(?:base64\.b64decode|codecs\.decode|zlib\.decompress|marshal\.loads)\s*\("),
]
RE_REVERSE_SHELL = [
    re.compile(r"/dev/tcp/"),
    re.compile(r"\bnc(?:at)?\b[^\n]*\s-[a-z]*[ec]\s"),
    re.compile(r"\bncat\b[^\n]*--(?:exec|sh-exec)\b"),
    re.compile(r"\bsocat\b[^\n]*\bexec:", re.I),
]
RE_SECRET_PATH = re.compile(
    r"(?:~|\$HOME|\$\{HOME\})/\.ssh/|\bid_(?:rsa|ed25519|ecdsa)\b|\.aws/credentials\b|\.config/gh/hosts\.yml\b"
    r"|\.claude/\.credentials\.json\b|\.netrc\b|\.docker/config\.json\b")
RE_NET_SEND = re.compile(
    r"\b(?:curl|wget|nc|ncat|scp|rsync|sftp)\b|\brequests\.(?:post|put|patch)\b|\bfetch\s*\(|\bhttps?\.request\s*\("
    r"|\burllib\.request\b|\baxios\.(?:post|put)\b")
RE_DESTROY = [
    re.compile(r"\brm\s+(?:-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*|-r\s+-f|-f\s+-r)\s+"
               r"(?:--no-preserve-root\s+)?[\"']?(?:/|/\*|~|~/|~/\*|\$HOME|\$\{HOME\}|\$HOME/\*)[\"']?(?=\s|$|[;&|)])"),
    re.compile(r"\bmkfs(?:\.\w+)?\s+/dev/"),
    re.compile(r"\bdd\b[^\n]*\bof=/dev/(?:sd|nvme|hd|vd|xvd|disk|mmcblk)"),
    re.compile(r"\bchmod\s+-R\s+0?777\s+/(?=\s|$)"),
    re.compile(r":\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:"),
]
RE_PERSISTENCE = [
    re.compile(r">>?\s*[\"']?(?:~|\$HOME|\$\{HOME\})/\.(?:bashrc|zshrc|profile|bash_profile|zprofile)\b"),
    re.compile(r"\bcrontab\s+(?:-\s*$|-\s|-l\b[^\n]*\|)"),
    re.compile(r"\bauthorized_keys\b"),
    re.compile(r"\bsystemctl\s+(?:--user\s+)?enable\b"),
]
# Zero-width and joiner characters, bidi controls, word joiners, Unicode tag characters (invisible prompt text).
RE_HIDDEN = re.compile("[\u200b-\u200f\u202a-\u202e\u2060-\u2064\u2066-\u2069\ufeff\U000e0000-\U000e007f]")
RE_INJECTION = [
    re.compile(r"\bignore\s+(?:all\s+|any\s+|the\s+)?(?:previous|prior|above|earlier|preceding)\s+"
               r"(?:instructions|prompts?|messages|rules|directions)\b", re.I),
    re.compile(r"\bdisregard\s+(?:all\s+|any\s+)?(?:the\s+|your\s+)?(?:previous|prior|above|system)\s+"
               r"(?:instructions|prompts?|rules|message)\b", re.I),
    # «do not tell the user (about this)» hides; «never tell the user TO do X» is advice on what to suggest — not caught
    re.compile(r"\b(?:do\s+not|don't|never)\s+(?:tell|inform|notify|alert|mention\s+(?:this|it)\s+to)\s+"
               r"the\s+user\b(?![\s*_\"']*(?:to|how)\b)", re.I),
    re.compile(r"\bhide\s+(?:this|it|these|that|the\s+\w+)\s+from\s+the\s+user\b", re.I),
    re.compile(r"\bwithout\s+the\s+user'?s?\s+(?:knowledge|noticing|awareness|consent)\b", re.I),
    re.compile(r"\byou\s+are\s+now\s+(?:in\s+)?(?:developer|DAN|jailbreak|god|unrestricted)\s+mode\b", re.I),
]

# A mailbox or a site in an example must be a demo one: RFC 2606/6761 names or the product's own vendor.
RE_EMAIL = re.compile(r"(?<![\w.+-])[A-Za-z0-9_.+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})(?![\w@])")
DEMO_DOMAINS = ("example.com", "example.org", "example.net", ".example", ".test", ".invalid", ".localhost")
# Fictional by convention: NANP 555-01xx, Ofcom drama numbers.
RE_PHONE = re.compile(r"(?<![\w.])\+\d[\d\s().-]{8,}\d(?![\w])")
FICTIONAL_PHONES = (re.compile(r"^1(?:\d{3})?55501\d\d$"), re.compile(r"^447700900\d{3}$"), re.compile(r"^44207946\d{4}$"))

MESSAGES = {
    "remote-exec": "downloaded content goes straight into a shell — pin a version, download, verify, then run",
    "decode-exec": "decoded data is executed — hidden payloads have no place in a plugin",
    "reverse-shell": "opens a shell to a remote host",
    "secret-exfil": "reads a credential file and sends data over the network on the same line",
    "secret-read": "reads a credential file — make sure nothing of it leaves the machine",
    "destroy": "wipes a root, the home directory or a disk",
    "persistence": "changes the user's shell startup, cron, SSH keys or services",
    "hidden-chars": "invisible Unicode characters (zero-width, bidi or tag) — text the reader cannot see",
    "prompt-injection": "tells the model to drop its instructions or to hide something from the user",
    "demo-contact": "a real-looking mailbox or phone — examples use example.com addresses and 555-01xx numbers",
    "private-name": "a name from the owner's private list — examples use demo companies, people and projects",
}
CODE_TRICKS = (("remote-exec", RE_REMOTE_EXEC), ("decode-exec", RE_DECODE_EXEC),
               ("reverse-shell", RE_REVERSE_SHELL), ("destroy", RE_DESTROY))


def file_kind(rel_path):
    base = os.path.basename(rel_path)
    if base in CODE_BASENAMES or rel_path.endswith(CODE_SUFFIXES):
        return "code"
    if base.endswith(".md"):
        return "instruction"
    if rel_path.endswith(DATA_SUFFIXES):
        return "data"
    return None


def skip_globs(root, plugin):
    """[upstream] skip_paths of a plugin: text it vendors from upstream."""
    path = os.path.join(root, "tests", "plugins", plugin, "plugin-test.toml")
    try:
        import tomllib
        with open(path, "rb") as fh:
            skip = tomllib.load(fh).get("upstream", {}).get("skip_paths") or []
    except (OSError, ValueError, ImportError):
        return []
    return [g for g in skip if isinstance(g, str)]


def is_skipped(root, rel_path):
    parts = rel_path.split("/")
    if len(parts) < 3 or parts[0] != "plugins":
        return False
    inside = "/".join(parts[2:])
    return any(fnmatch.fnmatch(inside, g) or fnmatch.fnmatch(inside, g.rstrip("/*") + "/*") for g in skip_globs(root, parts[1]))


def is_demo_mailbox(domain):
    d = domain.lower()
    return any(d == x or d.endswith("." + x.lstrip(".")) or (x.startswith(".") and d.endswith(x)) for x in DEMO_DOMAINS) \
        or scrub_check.host_allowed(d)


def is_demo_phone(text):
    digits = re.sub(r"\D", "", text)
    if not 10 <= len(digits) <= 15 or len(set(digits)) == 1 or digits.endswith("000000"):
        return True                       # not a phone number, or an obvious placeholder
    return any(p.match(digits) for p in FICTIONAL_PHONES)


def _common_dir(path):
    try:
        out = subprocess.run(["git", "-C", path, "rev-parse", "--path-format=absolute", "--git-common-dir"],
                             capture_output=True, text=True, check=True).stdout.strip()
        return os.path.realpath(out) if out else ""
    except (subprocess.CalledProcessError, FileNotFoundError):
        return ""


@functools.lru_cache(maxsize=None)
def in_this_repository(directory):
    """A directory of this repository or of any of its worktrees: the owner's names matter only in what is published."""
    here = _common_dir(REPO_ROOT)
    return bool(here) and _common_dir(directory) == here


@functools.lru_cache(maxsize=1)
def private_names():
    """Compiled matcher of the owner's private names, or None. The list lives outside every repository."""
    path = os.environ.get("AGENTS_STORE_PRIVATE_NAMES")
    if path is None:                                   # unset → the owner's default place; set to "" → off
        path = os.path.expanduser("~/.config/agents-store/private-names.txt")
        if not os.path.isfile(path):
            return None
    if not path:
        return None
    try:
        with open(path, encoding="utf-8") as fh:
            terms = [t.strip() for t in fh if t.strip() and not t.lstrip().startswith("#")]
    except OSError:
        print("safety-check: AGENTS_STORE_PRIVATE_NAMES points at a file that cannot be read", file=sys.stderr)
        return None
    if not terms:
        return None
    return re.compile("|".join(r"(?<![A-Za-z0-9])" + re.escape(t) + r"(?![A-Za-z0-9])" for t in terms), re.I)


def scan_text(rel_path, text, root=None, names_ok=True):
    """Findings for one file's text; the kind (code / instruction / data) decides the rules and the severity."""
    kind = file_kind(rel_path)
    if kind is None:
        return []
    out = []
    names = private_names() if names_ok else None
    vendored = is_skipped(root or REPO_ROOT, rel_path)

    def add(lineno, rule, severity, line):
        out.append(scrub_check.Finding(rel_path, lineno, rule, severity, scrub_check.redact(line), MESSAGES[rule]))

    doc = kind == "instruction"
    for lineno, line in enumerate(text.splitlines(), 1):
        if names is not None and names.search(line):
            add(lineno, "private-name", FAIL, line)
        if kind == "data":
            continue
        if not vendored:
            mails = [m.group(0) for m in RE_EMAIL.finditer(line) if not is_demo_mailbox(m.group(1))]
            phones = [m.group(0) for m in RE_PHONE.finditer(line) if not is_demo_phone(m.group(0))]
            if mails or phones:
                add(lineno, "demo-contact", WARN, line)
        for rule, patterns in CODE_TRICKS:
            if any(p.search(line) for p in patterns):
                add(lineno, rule, WARN if doc else FAIL, line)
        if RE_SECRET_PATH.search(line):
            if RE_NET_SEND.search(line):
                add(lineno, "secret-exfil", WARN if doc else FAIL, line)
            elif not doc:
                add(lineno, "secret-read", WARN, line)
        if not doc and any(p.search(line) for p in RE_PERSISTENCE):
            add(lineno, "persistence", WARN, line)
        hidden = RE_HIDDEN.search(line[1:] if lineno == 1 and line.startswith("\ufeff") else line)
        if hidden:
            add(lineno, "hidden-chars", FAIL if doc else WARN, "U+%04X in: %s" % (ord(hidden.group(0)), line))
        if doc and any(p.search(line) for p in RE_INJECTION):
            add(lineno, "prompt-injection", FAIL, line)
    return out


def load_allow(path):
    """path:rule-id[#value-selector]:reason — the scrub-allow.txt format, with this pass's rule ids."""
    entries = []
    if not path or not os.path.exists(path):
        return entries
    with open(path, encoding="utf-8", errors="replace") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":", 2)
            if len(parts) != 3 or not parts[2].strip():
                sys.exit("%s:%d: expected 'path:rule-id[#value-selector]:reason' with a reason" % (path, lineno))
            glob, rule = parts[0].strip(), parts[1].strip()
            selector = None
            if "#" in rule:
                rule, selector = (p.strip() for p in rule.split("#", 1))
            if rule != "*" and rule not in MESSAGES:
                sys.exit("%s:%d: unknown rule '%s'" % (path, lineno, rule))
            entries.append((glob, rule, selector))
    return entries


def read_file(rel_path):
    abs_path = os.path.join(REPO_ROOT, rel_path)
    if not os.path.isfile(abs_path) or os.path.getsize(abs_path) > scrub_check.MAX_BYTES:
        return None
    parts = rel_path.split("/")
    if any(p in scrub_check.SKIP_DIR_NAMES for p in parts[:-1]):
        return None
    try:
        with open(abs_path, encoding="utf-8") as fh:
            return fh.read()
    except (UnicodeDecodeError, OSError):
        return None


def text_at(ref, rel_path):
    """The file's text at a commit of its own repository; "" when it did not exist there."""
    abs_path = os.path.normpath(os.path.join(REPO_ROOT, rel_path))
    try:
        top = subprocess.run(["git", "-C", os.path.dirname(abs_path), "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, check=True).stdout.strip()
        rel = os.path.relpath(abs_path, top)
        return subprocess.run(["git", "-C", top, "show", "%s:%s" % (ref, rel)],
                              capture_output=True, text=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError, UnicodeDecodeError):
        return ""


def key(f):
    return (f.rule, re.sub(r"\s+", " ", f.excerpt))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("targets", nargs="*", help="paths to check (default: plugins/)")
    ap.add_argument("--baseline", default=DEFAULT_BASELINE)
    ap.add_argument("--no-baseline", action="store_true")
    ap.add_argument("--base", default="", help="report only findings new against this git ref; each is a FAIL")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    ap.add_argument("--strict", action="store_true", help="accepted for parity with the other passes")
    args = ap.parse_args(argv)

    entries = [] if args.no_baseline else load_allow(args.baseline)
    files, seen = [], set()
    for target in args.targets or [os.path.join(REPO_ROOT, t) for t in DEFAULT_TARGETS]:
        for f in scrub_check.tracked_files(target):
            if f not in seen and file_kind(f) and (file_kind(f) != "data" or private_names() is not None):
                seen.add(f)
                files.append(f)

    findings, suppressed = [], 0
    for rel_path in sorted(files):
        text = read_file(rel_path)
        if text is None:
            continue
        ours = in_this_repository(os.path.dirname(os.path.normpath(os.path.join(REPO_ROOT, rel_path))))
        current = scan_text(rel_path, text, names_ok=ours)
        if args.base:
            old = collections.Counter(key(f) for f in scan_text(rel_path, text_at(args.base, rel_path), names_ok=ours))
            fresh = []
            for f in current:
                if old[key(f)]:
                    old[key(f)] -= 1
                else:
                    f.severity = FAIL
                    f.message = "new against %s: %s" % (args.base, f.message)
                    fresh.append(f)
            current = fresh
        for f in current:
            if scrub_check.baselined(entries, f.path, f.rule, f.excerpt):
                suppressed += 1
            else:
                findings.append(f)

    fails = [f for f in findings if f.severity == FAIL]
    warns = [f for f in findings if f.severity == WARN]
    if args.format == "json":
        print(json.dumps({"files_scanned": len(files), "suppressed": suppressed, "fail": len(fails),
                          "warn": len(warns),
                          "findings": [{"path": f.path, "line": f.line, "rule": f.rule, "severity": f.severity,
                                        "excerpt": f.excerpt, "message": f.message} for f in findings]}, indent=2))
    else:
        for group in (fails, warns):
            for f in group:
                print("%s %s:%d [%s] %s — %s" % (f.severity, f.path, f.line, f.rule, f.excerpt, f.message))
        print("\nsafety-check: %d files, %d fail, %d warn, %d baselined"
              % (len(files), len(fails), len(warns), suppressed))
        if fails:
            print("Remove the trick or the instruction. Only if it is genuinely needed and safe, add a justified line "
                  "to scripts/safety-allow.txt in its own pull request.")
    if fails:
        return 1
    return 2 if warns else 0


if __name__ == "__main__":
    sys.exit(main())
