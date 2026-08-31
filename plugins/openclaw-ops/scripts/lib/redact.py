#!/usr/bin/env python3
"""Single redaction implementation for openclaw-ops.

Everything the plugin prints lands in the session transcript on disk and in the
model context. There is no after-the-fact edit, so "do not print it" is the only
control that works. This module is the one place that decides what a secret looks
like; nothing else in the plugin is allowed to build its own masking.

Design choices, all deliberate:

* A fingerprint replaces a masked tail. ``fp:0000aaaa`` (a synthetic stub; a real
  one is eight hex digits of a digest) answers every operational
  question ("same key in .env and in the vault?", "one key across five
  instances?", "did rotation change the value?", "is it empty?") and answers
  nothing for an attacker. A tail mask (``sk-…abcd``) leaks a meaningful share of
  a short token.
* The last rule is a high-entropy catch-all. It produces false positives. That is
  the correct trade: over-redacting a harmless string costs a re-read, missing an
  unknown token format costs a leak.
* Lowercase hex runs (image digests, container ids, git SHAs) are intentionally
  NOT matched by the catch-all — pin-before-mutate needs those readable.
"""

import hashlib
import os
import re

__all__ = [
    "fp", "fp_of_file", "len_bucket", "classify_key",
    "ScrubResult", "scrub_stream", "scrub", "redact_argv",
    "read_env_file", "env_names", "structure_only",
    "SCRUB_RULES", "KEY_CLASSES", "SAFE_KEYS", "SECRET_NAME_RE",
]

FP_PREFIX = "fp:"
FP_LEN = 8


# --------------------------------------------------------------------------- #
# fingerprints
# --------------------------------------------------------------------------- #

def fp(value):
    """Stable short fingerprint of a value: ``fp:<sha256[:8]>``.

    ``None`` and the empty string return ``None`` — absence is reported as
    absence, never as a fingerprint of nothing.
    """
    if value is None:
        return None
    if isinstance(value, str):
        value = value.encode("utf-8", "replace")
    if not value:
        return None
    return FP_PREFIX + hashlib.sha256(value).hexdigest()[:FP_LEN]


def fp_of_file(path):
    """Fingerprint a file's bytes without ever returning its content."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(65536), b""):
                h.update(chunk)
        return FP_PREFIX + h.hexdigest()[:FP_LEN]
    except OSError:
        return None


def len_bucket(n):
    """Coarse size bucket. Exact lengths narrow a brute-force search; buckets do not."""
    if n is None:
        return "unknown"
    if n == 0:
        return "empty"
    if n < 16:
        return "tiny"
    if n < 40:
        return "short"
    if n < 100:
        return "medium"
    if n < 400:
        return "long"
    return "huge"


# --------------------------------------------------------------------------- #
# key classification (by public, vendor-documented prefix)
# --------------------------------------------------------------------------- #

KEY_CLASSES = [
    ("anthropic-key", re.compile(r"^sk-ant-")),
    ("openai-key", re.compile(r"^sk-(proj-|svcacct-)?[A-Za-z0-9]")),
    ("xai-key", re.compile(r"^xai-")),
    ("google-key", re.compile(r"^AIza")),
    ("groq-key", re.compile(r"^gsk_")),
    ("huggingface-key", re.compile(r"^hf_")),
    ("perplexity-key", re.compile(r"^pplx-")),
    ("github-token", re.compile(r"^(gh[pousr]_|github_pat_)")),
    ("slack-token", re.compile(r"^xox[abprs]-")),
    ("aws-access-key-id", re.compile(r"^(AKIA|ASIA)[0-9A-Z]{8,}$")),
    ("secret-store-token", re.compile(r"^st\.[A-Za-z0-9_-]{6,}\.")),
    ("jwt", re.compile(r"^eyJ[A-Za-z0-9_-]{6,}\.")),
    ("bot-token", re.compile(r"^\d{6,14}:[A-Za-z0-9_-]{20,}$")),
    ("pem-private-key", re.compile(r"^-----BEGIN [A-Z ]*PRIVATE KEY-----")),
]


def classify_key(value, name=None):
    """Name the format class of a secret value. Never returns the value."""
    if value:
        for label, rx in KEY_CLASSES:
            if rx.search(value):
                return label
    if name and SECRET_NAME_RE.search(name):
        return "opaque-secret"
    return "unclassified"


SECRET_NAME_RE = re.compile(
    r"(?i)(pass(word|phrase)?|secret|token|api[-_]?key|apikey|credential|"
    r"private[-_]?key|client[-_]?secret|auth|bearer|session[-_]?id|cookie)"
)


# --------------------------------------------------------------------------- #
# stream scrubbing
# --------------------------------------------------------------------------- #

def _sub_value(rule):
    """Replace the whole match with a fingerprinted placeholder."""
    def repl(m):
        return "[REDACTED:%s:%s]" % (rule, fp(m.group(0)) or "empty")
    return repl


def _sub_kv(m):
    """Keep the key name (needed to reason about delivery), drop the value."""
    key, sep, val = m.group("key"), m.group("sep"), m.group("val")
    if not val or val in ("''", '""'):
        return "%s%s<empty>" % (key, sep)
    return "%s%s[REDACTED:kv:%s]" % (key, sep, fp(val) or "empty")


# Guard so a second pass never redacts an existing placeholder.
_NOT_PLACEHOLDER = r"(?!\[REDACTED)"

# A placeholder already emitted by an earlier rule. Later rules never look inside
# one: `[REDACTED:bot-token:fp:…]` contains the word "token", so the key-value
# rule used to match the placeholder's own text and produce
# `[REDACTED:bot-token:[REDACTED:kv:fp:…]]` — a nesting that hides which rule
# actually fired and makes the fingerprint the operator needs unreadable. One
# secret, one flat placeholder.
_PLACEHOLDER = re.compile(r"\[REDACTED:[^\[\]]*\]")

# Ordered: most specific first, high-entropy catch-all last.
SCRUB_RULES = [
    ("pem", re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        re.S), _sub_value("pem")),
    ("anthropic-key", re.compile(r"\bsk-ant-[A-Za-z0-9_-]{16,}"), _sub_value("anthropic-key")),
    ("openai-key", re.compile(r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{20,}"), _sub_value("openai-key")),
    ("xai-key", re.compile(r"\bxai-[A-Za-z0-9_-]{16,}"), _sub_value("xai-key")),
    ("google-key", re.compile(r"\bAIza[0-9A-Za-z_-]{30,}"), _sub_value("google-key")),
    ("groq-key", re.compile(r"\bgsk_[A-Za-z0-9]{20,}"), _sub_value("groq-key")),
    ("huggingface-key", re.compile(r"\bhf_[A-Za-z0-9]{20,}"), _sub_value("huggingface-key")),
    ("perplexity-key", re.compile(r"\bpplx-[A-Za-z0-9]{20,}"), _sub_value("perplexity-key")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})"),
     _sub_value("github-token")),
    ("slack-token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}"), _sub_value("slack-token")),
    ("aws-key", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{12,}\b"), _sub_value("aws-key")),
    ("secret-store-token", re.compile(r"\bst\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}"),
     _sub_value("secret-store-token")),
    ("jwt", re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{4,}"), _sub_value("jwt")),
    ("bot-token", re.compile(r"\b\d{6,14}:[A-Za-z0-9_-]{30,}\b"), _sub_value("bot-token")),
    ("authorization", re.compile(
        r"(?P<key>\b(?:authorization|proxy-authorization|x-api-key|api-key)\b)"
        r"(?P<sep>\s*[:=]\s*(?:bearer\s+|basic\s+|token\s+)?)"
        r"(?P<val>" + _NOT_PLACEHOLDER + r"(?!bearer\b)(?!basic\b)(?!token\b)[^\s,;\"']+)",
        re.I), _sub_kv),
    ("bearer", re.compile(
        r"\bbearer\s+" + _NOT_PLACEHOLDER + r"[A-Za-z0-9._~+/=-]{12,}", re.I),
     _sub_value("bearer")),
    ("kv", re.compile(
        r"(?P<key>[A-Za-z0-9_.\-]*"
        r"(?:pass(?:word|phrase)?|secret|token|api[-_]?key|apikey|credential|"
        r"private[-_]?key|client[-_]?secret)[A-Za-z0-9_.\-]*)"
        r"(?P<sep>\s*[:=]\s*\"?)"
        r"(?P<val>" + _NOT_PLACEHOLDER + r"[^\"'\s,;)}\]]+)", re.I), _sub_kv),
    # Catch-all, deliberately last and deliberately over-eager: long mixed-case
    # base64-ish runs. Lowercase-only hex (digests, container ids, SHAs) does not
    # match, because pin-before-mutate needs those printable.
    ("high-entropy", re.compile(
        r"\b(?=[A-Za-z0-9+/_-]*[a-z])(?=[A-Za-z0-9+/_-]*[A-Z])(?=[A-Za-z0-9+/_-]*[0-9])"
        r"[A-Za-z0-9+/_-]{40,}={0,2}\b"), _sub_value("high-entropy")),
]


class ScrubResult(object):
    """Scrubbed text plus what was removed. ``count`` must be shown to the human."""

    __slots__ = ("text", "count", "by_rule")

    def __init__(self, text, count, by_rule):
        self.text = text
        self.count = count
        self.by_rule = by_rule

    def marker(self):
        """Human-visible footer, empty when nothing was replaced."""
        if not self.count:
            return ""
        detail = ", ".join("%s=%d" % (k, v) for k, v in sorted(self.by_rule.items()))
        return "[scrubbed: %d match%s (%s)]" % (
            self.count, "" if self.count == 1 else "es", detail)

    def __str__(self):
        return self.text


def scrub_stream(text):
    """Redact every known secret shape in ``text``. Returns a :class:`ScrubResult`.

    Every byte the plugin shows a human or returns to the model passes through
    here first — command output, file excerpts, log tails, error messages.
    """
    if text is None:
        return ScrubResult("", 0, {})
    if isinstance(text, bytes):
        text = text.decode("utf-8", "replace")
    counts = {}
    for name, rx, repl in SCRUB_RULES:
        text, n = _apply_outside_placeholders(text, rx, repl)
        if n:
            counts[name] = counts.get(name, 0) + n
    return ScrubResult(text, sum(counts.values()), counts)


def _apply_outside_placeholders(text, rx, repl):
    """Apply one rule to the parts of ``text`` that are not already placeholders."""
    out, count, pos = [], 0, 0
    for match in _PLACEHOLDER.finditer(text):
        chunk, n = rx.subn(repl, text[pos:match.start()])
        out.append(chunk)
        out.append(match.group(0))
        count += n
        pos = match.end()
    chunk, n = rx.subn(repl, text[pos:])
    out.append(chunk)
    return "".join(out), count + n


def scrub(text):
    """Convenience wrapper returning only the scrubbed text."""
    return scrub_stream(text).text


def redact_argv(argv):
    """Scrub a command line before it is printed or logged."""
    return [scrub(a) for a in argv]


# --------------------------------------------------------------------------- #
# structured readers that cannot return a value
# --------------------------------------------------------------------------- #

_ENV_LINE = re.compile(r"^\s*(?:export\s+)?(?P<name>[A-Za-z_][A-Za-z0-9_]*)\s*=(?P<val>.*)$")


def read_env_file(path):
    """Describe a dotenv file without reading any value into the caller.

    Returns a list of ``{name, status, len_bucket, fp, klass}`` where ``status``
    is ``present`` / ``empty``. The value never leaves this function.
    """
    out = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as exc:
        return [{"name": None, "status": "unreadable", "error": str(exc)}]
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = _ENV_LINE.match(line)
        if not m:
            continue
        name = m.group("name")
        val = m.group("val").strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        out.append({
            "name": name,
            "status": "present" if val else "empty",
            "len_bucket": len_bucket(len(val)),
            "fp": fp(val),
            "klass": classify_key(val, name),
        })
    return out


def env_names(path):
    """Just the key names in a dotenv file — the safe half of an env audit."""
    return [e["name"] for e in read_env_file(path) if e.get("name")]


# Keys whose values are metadata, not secrets: printing them is the point.
SAFE_KEYS = frozenset([
    "provider", "id", "name", "type", "mode", "method", "backend", "runtime",
    "agentRuntime", "enabled", "disabled", "status", "state", "label", "version",
    "scope", "scopes", "model", "primary", "fallbacks", "count", "port", "host",
    "expires", "expiresAt", "expires_at", "expiry", "expiresIn", "createdAt",
    "created_at", "updatedAt", "updated_at", "lastUsed", "lastRefresh",
    "disabledUntil", "path", "source", "default", "isDefault", "email_domain",
])

# Identifiers that are useful only as a comparison key across instances.
FP_KEYS = frozenset([
    "account", "accountId", "accountUuid", "userId", "user_id", "orgId",
    "organizationId", "clientId", "client_id", "subject", "sub", "email",
    "projectId", "project_id", "workspaceId", "identityId",
])


def structure_only(obj, _depth=0):
    """Reduce a parsed JSON document to shape + metadata, dropping every value.

    Use this instead of printing an auth-profile, credential or config blob:
    strings become ``{"present": true, "len_bucket": ..., "fp": ..., "klass": ...}``,
    metadata keys in :data:`SAFE_KEYS` survive verbatim (dates and modes are not
    secrets and they are what you actually need), and identity keys in
    :data:`FP_KEYS` collapse to a fingerprint so the same account can be spotted
    in two directories without printing it.
    """
    if _depth > 12:
        return "<truncated>"
    if isinstance(obj, dict):
        out = {}
        for k, v in obj.items():
            if k in FP_KEYS and isinstance(v, str):
                out[k] = fp(v)
            elif k in SAFE_KEYS and not isinstance(v, (dict, list)):
                out[k] = v
            else:
                out[k] = structure_only(v, _depth + 1)
        return out
    if isinstance(obj, list):
        return [structure_only(v, _depth + 1) for v in obj[:64]]
    if isinstance(obj, str):
        return {
            "present": bool(obj),
            "len_bucket": len_bucket(len(obj)),
            "fp": fp(obj),
            "klass": classify_key(obj),
        }
    return obj


if __name__ == "__main__":  # smoke path: read stdin, write scrubbed stdout
    import sys
    res = scrub_stream(sys.stdin.read())
    sys.stdout.write(res.text)
    if res.count:
        sys.stderr.write(res.marker() + "\n")
