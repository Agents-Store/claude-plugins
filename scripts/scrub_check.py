#!/usr/bin/env python3
"""Publication gate: refuse to ship deployment-specific data in a public plugin.

Rules are written as SHAPES, never as literal values from any real deployment.
A gate that hardcodes the strings it hunts becomes the leak it was meant to stop.

Exit codes: 0 clean, 1 hard fail, 2 warnings only.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import math
import os
import re
import subprocess
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_BASELINE = os.path.join(REPO_ROOT, "scripts", "scrub-allow.txt")

FAIL, WARN, OFF = "fail", "warn", "off"

# A plugin opts into the strict ruleset by carrying this marker file.
STRICT_MARKER = ".scrub-strict"

# Third-party or regenerated trees. `__pycache__` is deliberately NOT here: a
# committed .pyc is published like any other file, and skipping the directory is
# how one shipped an absolute source path while the gate reported it clean.
SKIP_DIR_NAMES = {
    ".git", "node_modules", ".venv", "venv", ".mypy_cache",
    ".pytest_cache", "dist", "build", ".next", "workspace",
}
SKIP_BASENAMES = {
    "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "poetry.lock",
    "Cargo.lock", "composer.lock", "go.sum",
}
# Suffixes whose bytes are not source text. These are NOT skipped: they are
# read as printable-string runs and put through the reduced binary ruleset
# below, because a build artefact (.pyc) carries the absolute source path of
# the machine that produced it, and "home paths fail everywhere" cannot have an
# exception carved out by file extension.
BINARY_SUFFIXES = (
    ".pyc", ".png", ".jpg", ".jpeg", ".gif", ".webp", ".ico", ".pdf", ".zip",
    ".gz", ".tgz", ".bz2", ".xz", ".woff", ".woff2", ".ttf", ".otf", ".mp4",
    ".mp3", ".wasm", ".lock", ".svg",
)
MAX_BYTES = 8 * 1024 * 1024

# Paths documented by upstream OpenClaw / Docker / POSIX that a plugin may name
# literally. Everything else must be discovered at runtime or come from the
# operator's own config file.
UPSTREAM_ABS_PREFIXES = (
    "/home/node/",            # container home of the upstream image
    "/opt/openclaw",          # upstream in-container mount root
    "/usr/local/bin",
    "/usr/local/lib",
    "/usr/bin",
    "/usr/share",
    "/bin/",
    "/sbin/",
    "/tmp",
    "/dev/null",
    "/dev/stdin",
    "/dev/stdout",
    "/dev/stderr",
    "/dev/urandom",
    "/var/run/docker.sock",
    "/var/lib/docker/",       # Docker's own documented layout
    "/proc/",
    "/etc/passwd",
    "/etc/group",
    "/etc/os-release",
    "/etc/hosts",
    "/etc/localtime",
    "/etc/machine-id",
    "/var/lib/dbus/machine-id",
    "/etc/timezone",
)

# First segment of something that looks like a filesystem path rather than a
# URL path (/healthz, /v1/models are not filesystem paths).
FS_ROOTS = (
    "etc", "var", "usr", "home", "root", "srv", "mnt", "media", "opt", "data",
    "docker", "agents", "projects", "instances", "stacks", "Users", "workspace",
    "app", "run", "boot", "lib",
)

PLACEHOLDER_TOKENS = re.compile(
    r"<[^>\s]+>|\{\{?[A-Za-z0-9_.-]+\}?\}|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?|"
    r"%[sd]\b|\*|\.\.\.|…|xxx+|X{3,}",
)

# Segment names that read as a placeholder rather than a real deployment noun.
GENERIC_SEGMENT = re.compile(
    r"^(?:project|projects?[a-z0-9_-]*|app|apps|stack|stacks|instance|instances|"
    r"name|names|my[a-z0-9_-]*|your[a-z0-9_-]*|our[a-z0-9_-]*|example[a-z0-9_-]*|"
    r"demo[a-z0-9_-]*|acme[a-z0-9_-]*|sample[a-z0-9_-]*|test[a-z0-9_-]*|foo|bar|baz|"
    r"placeholder|template|templates|repo|repos|service|services|container|"
    r"containers|data|backup|backups|restore|target|source|dir|path|other|custom|default|main|new|old|first|second|scenario[a-z0-9_-]*|private|shared|common|some[a-z0-9_-]*)$",
    re.IGNORECASE,
)

GENERIC_USER = re.compile(
    r"^(?:me|user\d*|users|you|youruser|username|dev|developer|node|root|admin|"
    r"ubuntu|debian|ec2-user|app|deploy|runner|ci|build|john|jane|alice|bob|"
    r"someone|somebody|example|demo|test|sandbox|[a-z-]*sandbox|\.\.\.)$",
    re.IGNORECASE,
)

# Hosts a public plugin may name: documentation ranges, vendors it integrates
# with, and RFC 2606 / RFC 6761 reserved names.
ALLOWED_HOST_SUFFIXES = (
    ".example.com", ".example.org", ".example.net", ".example",
    ".invalid", ".test", ".localhost", ".local",
    "example.com", "example.org", "example.net", "localhost",
    ".openclaw.ai", "openclaw.ai",
    ".github.com", "github.com", ".githubusercontent.com", "ghcr.io",
    ".docker.com", "docker.io", ".docker.io", "hub.docker.com",
    ".anthropic.com", "anthropic.com", ".claude.com", "claude.com",
    ".infisical.com", "infisical.com",
    ".schema.org", "schemastore.org", ".json-schema.org", "json-schema.org",
    ".w3.org", ".ietf.org", ".rfc-editor.org", ".iana.org",
    ".agents.store", "agents.store",
    # public vendor endpoints plugins in this marketplace legitimately name
    ".jina.ai", ".draw.io", ".sendpulse.com", ".vercel.com", ".vercel.app",
    ".atlassian.com", ".atlassian.net", ".openai.com", ".perplexity.ai",
    ".mattermost.com", ".getoutline.com", ".n8n.io", ".nocobase.com",
    ".nocodb.com", ".directus.io", ".trigger.dev", ".apify.com", ".mem0.ai",
    ".firecrawl.dev", ".dataforseo.com", ".cloudflare.com", ".r2.dev",
    ".backblazeb2.com", ".amazonaws.com", ".googleapis.com", ".microsoft.com",
    ".sentry.io", ".stripe.com", ".plane.so", ".taiga.io", ".chatwoot.com",
    ".dify.ai", ".payloadcms.com", ".flask.palletsprojects.com", ".python.org",
    ".npmjs.com", ".npmjs.org", ".yarnpkg.com", ".pypi.org", ".crates.io",
    ".readthedocs.io", ".mozilla.org", ".google.com", ".telegram.org", "t.me",
    ".assistant-ui.com", ".exa.ai", ".shadcn.com",
    ".jsdelivr.net", ".unpkg.com", ".cdnjs.com", ".gravatar.com",
    ".apache.org", ".oracle.com", ".python-requests.org", ".slack.com",
    ".posthog.com", ".auth0.com", ".context7.com",
    # placeholder domains conventional in documentation
    "company.com", "mycompany.com", "yourcompany.com", "your-domain.com",
    "yourdomain.com", "mydomain.com", "myapp.com", "mysite.com", "acme.com",
    "acme.inc", "contoso.com", "domain.com", "bigcorp.com", "email.com",
)

# First label of a host that only a self-hosted control plane carries.
INFRA_HOST_LABEL = re.compile(
    r"^(?:registry|panel|cp|cpanel|pma|phpmyadmin|vault|internal|intranet|vpn|"
    r"bastion|jump|ci|cd|dashboard|portal|admin|console|gateway|proxy|monitor|"
    r"monitoring|metrics|logs|logging|grafana|prometheus|kibana|graylog|traefik|"
    r"haproxy|minio|jenkins|nexus|harbor|sonar|keycloak|ldap|sso|idp|"
    r"backup|backups|nas|infra|ops|deploy|runner|builder)"
    r"(?:-[a-z0-9-]+)?\.",       # vault-node.… is the same signal as vault.…
    re.IGNORECASE,
)

# Non-routable / documentation / universally-published addresses.
ALLOWED_IPV4 = re.compile(
    r"^(?:"
    r"0\.0\.0\.0|255\.255\.255\.255|"
    r"127\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
    r"192\.168\.\d{1,3}\.\d{1,3}|"
    r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}|"
    r"169\.254\.\d{1,3}\.\d{1,3}|"
    r"192\.0\.2\.\d{1,3}|198\.51\.100\.\d{1,3}|203\.0\.113\.\d{1,3}|"   # RFC 5737
    r"100\.64\.\d{1,3}\.\d{1,3}|"
    r"1\.2\.3\.4|5\.6\.7\.8|"                                            # canonical fillers
    r"8\.8\.8\.8|8\.8\.4\.4|1\.1\.1\.1|1\.0\.0\.1|9\.9\.9\.9"            # public resolvers
    r")$"
)

# Extensions that make a dotted token a filename, not a hostname.
NOT_A_TLD = {
    "js", "ts", "tsx", "jsx", "mjs", "cjs", "py", "rb", "go", "rs", "php",
    "java", "c", "h", "cc", "hpp", "sh", "bash", "zsh", "ps1", "bat", "md",
    "txt", "json", "yml", "yaml", "toml", "ini", "conf", "cfg", "env", "xml",
    "html", "htm", "css", "scss", "sql", "csv", "tsv", "log", "bak", "tmp",
    "lock", "map", "d", "gz", "zip", "tar", "png", "jpg", "svg", "pdf", "so",
    "dll", "exe", "jinja", "j2", "tpl", "example", "sample", "old", "new",
    "orig", "patch", "diff", "gitignore", "dockerignore", "npmrc", "nvmrc",
}

# Real top-level domains, so a bare dotted token can be told apart from a
# package name or a Java-style label. Public data, not deployment data.
KNOWN_TLDS = {
    "com", "net", "org", "io", "ai", "dev", "app", "co", "me", "cloud", "tech",
    "work", "pro", "site", "website", "online", "store", "space", "live",
    "team", "systems", "solutions", "services", "agency", "tools", "run",
    "page", "link", "host", "network", "email", "digital", "xyz", "info",
    "biz", "tv", "fm", "so", "to", "sh", "gg", "id", "my", "in", "uk", "de",
    "fr", "us", "ca", "eu", "ru", "ua", "pl", "nl", "es", "it", "ch", "at",
    "se", "no", "fi", "dk", "cz", "jp", "cn", "au", "nz", "br", "mx", "edu",
    "gov", "int", "mil", "inc", "ltd", "llc", "group", "media", "studio",
}

SECRET_PATTERNS = [
    (r"\bsk-ant-(?:api|oat|sid)[A-Za-z0-9_-]{2,}-[A-Za-z0-9_-]{24,}", "Anthropic key"),
    (r"\bsk-proj-[A-Za-z0-9_-]{24,}", "OpenAI project key"),
    (r"\bsk-[A-Za-z0-9]{32,}", "OpenAI-style key"),
    (r"\b(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{30,}", "GitHub token"),
    (r"\bgithub_pat_[A-Za-z0-9_]{40,}", "GitHub fine-grained token"),
    (r"\bglpat-[A-Za-z0-9_-]{18,}", "GitLab token"),
    (r"\bxox[baprs]-[A-Za-z0-9-]{10,}", "Slack token"),
    (r"\bAKIA[0-9A-Z]{16}\b", "AWS access key id"),
    (r"\bAIza[0-9A-Za-z_-]{35}\b", "Google API key"),
    (r"\bdckr_pat_[A-Za-z0-9_-]{20,}", "Docker Hub token"),
    (r"\bst\.[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{20,}", "Infisical service token"),
    (r"\bhf_[A-Za-z0-9]{30,}", "HuggingFace token"),
    (r"\b\d{8,10}:AA[A-Za-z0-9_-]{30,}\b", "Telegram bot token"),
    (r"\bnpm_[A-Za-z0-9]{30,}", "npm token"),
]

# --- generic secret shapes -------------------------------------------------
# The vendor-prefix table above only recognises the formats it was told about;
# a token with an unlisted prefix walked straight through it. These two rules
# close that hole and mirror the tail of the openclaw-ops redaction ladder
# (plugins/openclaw-ops/scripts/lib/redact.py): a secret-shaped NAME assigned a
# high-entropy value, then a bare high-entropy run. Both over-fire by design —
# a false positive costs one reviewed baseline line, a miss costs a credential.

RE_KV_SECRET = re.compile(
    r"(?P<key>[A-Za-z][A-Za-z0-9_.-]*"
    r"(?:PASSWORD|PASSWD|PASSPHRASE|SECRET|TOKEN|APIKEY|API[_-]?KEY|ACCESS[_-]?KEY|"
    r"CREDENTIAL|PRIVATE[_-]?KEY|CLIENT[_-]?SECRET|KEY)"
    r"[A-Za-z0-9_.-]*)"
    r"\s*[:=]\s*"
    r"(?P<q>[\"\'`]?)(?P<val>[A-Za-z0-9+/=_.-]{16,})(?P=q)",
    re.IGNORECASE)

# Mixed-case base64-ish run. Lowercase-only hex (git SHAs, image digests,
# checksums) deliberately does not match — those must stay readable.
RE_HIGH_ENTROPY = re.compile(
    r"(?<![A-Za-z0-9+/=_-])"
    r"(?=[A-Za-z0-9+/_-]*[a-z])(?=[A-Za-z0-9+/_-]*[A-Z])(?=[A-Za-z0-9+/_-]*[0-9])"
    r"[A-Za-z0-9+/_-]{40,}={0,2}(?![A-Za-z0-9+/=_-])")

# Long runs that are published, reproducible facts rather than credentials.
NOT_A_SECRET = re.compile(
    r"(?i)^(?:sha(?:256|384|512)-|sha\d+:|md5-|integrity-|data:)")


def shannon(value: str) -> float:
    """Bits of entropy per character. A word scores low, a random token high."""
    if not value:
        return 0.0
    counts = {}
    for ch in value:
        counts[ch] = counts.get(ch, 0) + 1
    n = float(len(value))
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


# Shapes that are long and mixed-case without being generated material:
# a member expression (`process.env.OPENAI_API_KEY` — the NAME of a secret, not
# one), a bare environment-variable name, and English identifiers in camel or
# kebab case (`PageBean2FieldAssociationSchemeFieldSearchResult`).
RE_MEMBER_EXPR = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*(?:\.[A-Za-z_$][A-Za-z0-9_$]*)+$")
RE_ENV_NAME = re.compile(r"^[A-Z][A-Z0-9_]*$")
RE_DIGEST_SEGMENT = re.compile(r"^[0-9a-f]{32,}$")


def word_like(v: str) -> bool:
    """English identifier rather than a token.

    A long unbroken lowercase run is what words have and what a random token
    almost never does; the uppercase share separates `…AssociationScheme…`
    (few capitals, long words) from base64 (a third of it capitals).
    """
    runs = [len(x) for x in re.findall(r"[a-z]+", v)] or [0]
    upper = sum(1 for c in v if c.isupper()) / float(len(v))
    return max(runs) >= 6 and upper < 0.30


def looks_random(value: str, min_len: int, min_entropy: float, classes_needed: int = 2) -> bool:
    """Does this value read as generated material rather than prose or a name?"""
    v = value.strip().strip("\"\'`,;")
    if len(v) < min_len:
        return False
    if PLACEHOLDER_VALUE.search(v) or PLACEHOLDER_TOKENS.search(v):
        return False
    if NOT_A_SECRET.search(v):
        return False
    if not re.fullmatch(r"[A-Za-z0-9+/=_.-]+", v):
        return False
    if looks_like_host(v):                       # an endpoint is another rule's job
        return False
    if RE_MEMBER_EXPR.match(v) or RE_ENV_NAME.match(v):
        return False                             # names a secret, is not one
    if any(RE_DIGEST_SEGMENT.match(sg) for sg in re.split(r"[-_]", v)):
        return False                             # git sha / content digest
    if word_like(v):
        return False
    if len(v) >= 40 and len(set(v)) == len(v):
        return False                             # a character alphabet, not a token
    classes = sum(bool(re.search(p, v)) for p in (r"[a-z]", r"[A-Z]", r"[0-9]"))
    if classes < classes_needed:
        return False
    return shannon(v) >= min_entropy


PLACEHOLDER_VALUE = re.compile(
    r"(?i)replace[-_]?me|your[-_]|example|placeholder|redact|dummy|change[-_]?me|"
    r"xxxx|<[^>]*>|\.\.\.|s3cret|hunter2|abc123|test[-_]?key|fake"
)

MODEL_ID = re.compile(
    r"\b(?:"
    r"claude-[a-z0-9]+-[0-9][a-z0-9.-]*|"
    r"gpt-[0-9][a-z0-9.-]*|gpt-[0-9]?o[a-z0-9.-]*|o[134](?:-[a-z]+)?\b|"
    r"gemini-[0-9][a-z0-9.-]*|grok-[0-9][a-z0-9.-]*|"
    r"llama-?[0-9][a-z0-9.-]*|mistral-[a-z0-9.-]*|deepseek-[a-z0-9.-]*|"
    r"text-embedding-[a-z0-9-]+"
    r")\b"
)

STRICT_TEXT_KINDS = ("SKILL.md", "commands", "agents", "hooks", "README.md", "LEARNINGS.md")

# Infrastructure vocabulary. The English half used to be the whole rule, which
# made a real endpoint safe to ship as long as the sentence around it was
# written in another language — and the LEARNINGS.md files here are Russian.
# The Cyrillic half is matched on stems, so declensions are covered without
# enumerating them.
INFRA_CONTEXT = re.compile(
    r"(?i)(?:\b(?:infisical|dokploy|coolify|cloudron|portainer|traefik|self-hosted|"
    r"selfhosted|on-prem|on-premise|"
    r"our (?:instance|server|host|panel|deployment)|"
    r"internal (?:host|endpoint|instance|url|panel|service))\b"
    r"|(?:инстанс|эндпоинт|энд-поинт|сервер|хост|панел|контур|стенд|"
    r"самохост|self-hosted|развёрнут|развернут|внутренн|прод(?:акшн|акшен)?\b|"
    r"домен|поддомен|адрес|деплой|воркер|инфраструктур))"
)

# Lines that talk about HTTP routes, not filesystem paths.
HTTP_ROUTE = re.compile(
    r"(?i)(?:^|[\s|`\"'(])(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/|"
    r"/api/|/rest/|\bendpoint\b|\broute\b|\bcurl\b|https?://|"
    r"\|\s*(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s*\|"
)

# Ports a deployment binds on the host. The container-side port is upstream's
# and may be named; anything else is site data.
UPSTREAM_PORTS = {"18789"}
DOC_PORTS = {"80", "443", "3000", "5000", "8000", "8080", "8443", "9000"}

CONFIG_SURFACES = (
    ".env.example", ".mcp.json", "plugin.json", "marketplace.json",
    "settings.json", "hooks.json",
)


class Finding:
    __slots__ = ("path", "line", "rule", "severity", "excerpt", "message")

    def __init__(self, path, line, rule, severity, excerpt, message):
        self.path = path
        self.line = line
        self.rule = rule
        self.severity = severity
        self.excerpt = excerpt
        self.message = message


def redact(text: str, limit: int = 90) -> str:
    """Findings are printed to CI logs — never echo the match verbatim."""
    text = text.strip()
    if len(text) > limit:
        text = text[: limit - 1] + "…"
    # keep shape, drop payload: long alphanumeric runs become a length marker
    return re.sub(r"[A-Za-z0-9_-]{40,}", lambda m: "<%d-chars>" % len(m.group(0)), text)


def looks_like_host(token: str) -> bool:
    labels = token.split(".")
    if len(labels) < 2:
        return False
    tld = labels[-1].lower()
    if tld in NOT_A_TLD or not tld.isalpha() or len(tld) < 2:
        return False
    return all(lbl and re.fullmatch(r"[A-Za-z0-9_-]+", lbl) for lbl in labels)


def host_allowed(host: str) -> bool:
    host = host.lower().rstrip(".")
    if host == "localhost" or ALLOWED_IPV4.match(host):
        return True
    for suffix in ALLOWED_HOST_SUFFIXES:
        if host == suffix.lstrip(".") or host.endswith(suffix):
            return True
    if "example" in host or "placeholder" in host:
        return True
    if re.search(r"(?:^|\.)(?:my|your|our|the)[a-z-]*\.[a-z]{2,}$", host):
        return True
    return False


class Rule:
    def __init__(self, rid, message, repo=FAIL, strict=None, check=None):
        self.rid = rid
        self.message = message
        self.repo = repo
        self.strict = repo if strict is None else strict
        self.check = check

    def severity(self, strict: bool) -> str:
        return self.strict if strict else self.repo


# ---------------------------------------------------------------------------
# Individual checks. Each yields (column_excerpt, extra_message) per line.
# ---------------------------------------------------------------------------

RE_HOST_NAME = re.compile(
    r"\b[a-z][a-z0-9]*(?:-[a-z0-9]+)*-(?:server|node|host|box|vm|worker)-\d+\b"
    r"|\b[a-z][a-z0-9]*-\d+-(?:server|node|host|box|vm|worker)\b"
)
RE_SHORT_HOST = re.compile(r"(?<![A-Za-z0-9._-])[a-z]\.[a-z0-9][a-z0-9-]{2,}\.[a-z]{2,}\b")
RE_URL_HOST = re.compile(r"https?://([A-Za-z0-9_.-]+)(?::\d+)?")
RE_BARE_HOST = re.compile(
    r"(?<![A-Za-z0-9._/-])[a-z0-9][a-z0-9-]*(?:\.[a-z0-9][a-z0-9-]*)+"
    r"\.[a-z]{2,}(?![A-Za-z0-9._-])")
RE_IPV4 = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
RE_INSTANCE = re.compile(r"\b(?:openclaw|hermes)-([a-z][a-z0-9-]*)\b")

# Words that follow the product name for reasons other than naming a instance:
# component names, skill names, roles, environments.
INSTANCE_VOCAB = {
    "ops", "configurator", "config", "gateway", "tools", "tool", "codex",
    "with-infisical", "cli", "server", "client", "worker", "workspace",
    "skills", "plugins", "plugin", "dev", "prod", "staging", "local",
    "instance", "instances", "template", "example", "demo", "test", "docs",
    "mcp", "api", "ui", "web", "bot", "agent", "agents", "sync", "hooks",
    "json", "schema", "assistant", "auditor", "fleet", "migration", "update",
    "updater", "upgrade", "auth", "core", "runtime", "image", "data", "state",
    "private", "public", "shared", "main", "name", "compose", "docker",
    "incident", "responder", "auditor", "doctor", "health", "healthcheck",
    "status", "repair", "clone", "memory", "versions", "exec", "logs", "init",
    "features", "audit", "security", "diagnostics", "report", "surgery",
    # canonical placeholder names in documentation
    "alpha", "beta", "gamma", "delta", "one", "two", "three", "first", "second",
}
RE_FLEET_PATH = re.compile(
    r"(?<![\w./~$-])/(docker|agents|projects|instances|stacks)/([A-Za-z0-9_.<>{}$*-]+)")
RE_ETC_IDENTITY = re.compile(
    r"(?<![\w./~$-])/etc/(infisical|vault|secrets|identity)/([A-Za-z0-9_.<>{}$-]+)\.env\b")
RE_HOMEDIR = re.compile(r"(?<![\w./~$-])/(?:Users|home)/([^\s/\"'`,;:)\]}]+)")
RE_UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
RE_JWT = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")
RE_PEM = re.compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----")
RE_LOCAL_PORT = re.compile(r"\b(?:127\.0\.0\.1|localhost|0\.0\.0\.0):(\d{2,5})\b")
RE_PORT_NEAR_OPENCLAW = re.compile(r"(?<![\w.:-])(1[0-9]{4})(?![\w.:-])")
RE_EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
RE_HOST_ASSIGN = re.compile(
    r"(?i:\b(?:domain|host|hostname|endpoint|url|uri|instance|server)\w*)\s*[:=]\s*"
    r"[\"'`]?([a-z0-9][a-z0-9.-]*\.[a-z]{2,})(?![A-Za-z0-9_(-])")
# UPPER_SNAKE identifier assigned a host or a URL. Environment-variable naming
# is uppercase ASCII by convention in every language, so this signal survives
# the surrounding prose being written in one the gate does not read.
RE_ENVVAR_HOST = re.compile(
    r"(?<![A-Za-z0-9_])(?:[A-Z][A-Z0-9_]{2,})\s*[:=]\s*[\"'`]?"
    r"(?:https?://)?([a-z0-9][a-z0-9.-]*\.[a-z]{2,})(?![A-Za-z0-9_(-])")
ROLE_MAILBOX = re.compile(
    r"(?i)^(?:admin|administrator|support|help|hello|info|contact|sales|billing|"
    r"noreply|no-reply|donotreply|team|dev|devs|security|abuse|postmaster|root)$")
RE_ABS_PATH = re.compile(r"(?<![\w.$~-])/(?:%s)(?:/[A-Za-z0-9_.<>${}*-]+)*" % "|".join(FS_ROOTS))
RE_EXAMPLE_OPEN = re.compile(r"<!--\s*example-only\s*-->")
RE_EXAMPLE_CLOSE = re.compile(r"<!--\s*/?\s*end example-only\s*-->|<!--\s*/example-only\s*-->")

SECRET_RE = [(re.compile(p), label) for p, label in SECRET_PATTERNS]


def check_host_name(line, ctx):
    for m in RE_HOST_NAME.finditer(line):
        lead = m.group(0).split("-", 1)[0]
        if GENERIC_SEGMENT.match(lead) or lead in ("docker", "web", "db", "api", "node"):
            continue
        yield m.group(0), "host names are discovered at runtime, never shipped"


def candidate_hosts(line, bare=False):
    """Hosts named as endpoints — not every dotted token in the line.

    Yields (host, kind) where kind is "url", "assign" or "bare". The kind is
    what lets a rule weigh a configured endpoint differently from a hostname
    that merely appears in a sentence.

    `bare` widens the net to hostnames mentioned in prose, which only makes
    sense in strict scope: outside it the false-positive rate is not worth it.
    """
    for m in RE_URL_HOST.finditer(line):
        yield m.group(1), "url"
    for rx in (RE_HOST_ASSIGN, RE_ENVVAR_HOST):
        for m in rx.finditer(line):
            host = m.group(1)
            # `post.data.url` and `org.logo` also parse as dotted tokens; a real
            # TLD is what separates a configured endpoint from a member access.
            if host.rsplit(".", 1)[-1].lower() in KNOWN_TLDS:
                yield host, "assign"
    if bare:
        for m in RE_BARE_HOST.finditer(line):
            host = m.group(0)
            if host.rsplit(".", 1)[-1].lower() in KNOWN_TLDS:
                yield host, "bare"


def check_private_host(line, ctx):
    # One host can be seen in several roles on the same line (a URL that is also
    # the value of an env var); collect every role first, so the strongest one
    # decides — otherwise whichever regex ran first silently won.
    kinds = {}
    for host, kind in candidate_hosts(line, bare=True):
        kinds.setdefault(host.rstrip("/."), set()).add(kind)
    # A bare hostname in prose is reported when anything about it or its line
    # says "deployment": a control-plane first label, the single-letter-subdomain
    # convention private deployments favour, infrastructure vocabulary on the
    # line, or a config surface. Only a dotted token with none of those signals
    # is let through — an unqualified bare host must never get a free pass
    # merely because the plugin is outside strict scope, which is how a real
    # endpoint dropped into a LEARNINGS.md sentence used to ship.
    for host, roles in kinds.items():
        if host_allowed(host) or not looks_like_host(host):
            continue
        kind = "assign" if "assign" in roles else ("url" if "url" in roles else "bare")
        if INFRA_HOST_LABEL.match(host):
            yield host, "control-plane hostname of a real deployment"
        elif kind == "assign" and ctx["published"]:
            # Language-independent signal: something in a published plugin is
            # being CONFIGURED to point at this host. Whether the sentence
            # around it is English, Russian or absent does not change that.
            yield host, ("a published plugin must be configured with ${VAR} or an "
                         "example host, never with a real one")
        elif INFRA_CONTEXT.search(line):
            yield host, "infrastructure URL must be a placeholder, not a real endpoint"
        elif ctx["config_surface"]:
            yield host, "config surfaces carry ${VAR} or an example host, never a real one"
        elif re.match(r"^[a-z]\.[a-z0-9]", host) and kind != "bare":
            yield host, "single-letter subdomain reads as a private deployment host"
        # anything left is a dotted token with no deployment signal at all —
        # `r.data.email` in a code sample, not an endpoint. Strict scope still
        # refuses it wholesale through strict-host.


def check_strict_host(line, ctx):
    seen = set()
    for host, _kind in candidate_hosts(line, bare=True):
        host = host.rstrip("/.")
        if host in seen or host_allowed(host) or not looks_like_host(host):
            continue
        seen.add(host)
        yield host, "strict scope allows only vendor, upstream and example hosts"


def check_ipv4(line, ctx):
    for m in RE_IPV4.finditer(line):
        ip = m.group(0)
        if any(int(o) > 255 for o in ip.split(".")):
            continue
        if ALLOWED_IPV4.match(ip):
            continue
        yield ip, "public IPv4 outside RFC 5737 documentation ranges"


def check_instance(line, ctx):
    for m in RE_INSTANCE.finditer(line):
        name = m.group(1)
        head = name.split("-", 1)[0]
        if head in INSTANCE_VOCAB or name in INSTANCE_VOCAB or GENERIC_SEGMENT.match(head):
            continue
        if PLACEHOLDER_TOKENS.search(name):
            continue
        yield m.group(0), "instance names come from discovery; use <instance>"


# The substrings on a line that really are HTTP, so they can be cut out of it
# instead of excusing the whole line.
RE_URL_SPAN = re.compile(
    r"(?i)https?://\S*"
    r"|(?:^|[\s|`\"'(])(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\s+/\S*"
    r"|(?<![\w./~$-])/(?:api|rest|v\d+)/\S*")


def strip_url_spans(line: str) -> str:
    """Blank out URLs and HTTP routes, preserving every other column.

    The old rule bailed out of the whole line the moment it saw `curl` or an
    http route, so a runbook sentence — one curl call, then "the config lives
    in /docker/<real-name>" — shipped the deployment path untouched. Only the
    URL is HTTP; the rest of the line is still filesystem prose.
    """
    return RE_URL_SPAN.sub(lambda m: " " * len(m.group(0)), line)


# A markdown table row whose first cell is an HTTP verb is an API route table,
# not filesystem prose. This is the ONE whole-line exemption left: it is
# unambiguous, unlike "there is a URL or the word curl somewhere on the line",
# which used to wave through the rest of a runbook sentence.
RE_ROUTE_TABLE_ROW = re.compile(
    r"^\s*\|\s*(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)"
    r"(?:\s*/\s*(?:GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS))*\s*\|")


def check_fleet_path(line, ctx):
    if RE_ROUTE_TABLE_ROW.match(line):
        return
    line = strip_url_spans(line)
    for m in RE_FLEET_PATH.finditer(line):
        segment = m.group(2)
        if PLACEHOLDER_TOKENS.search(segment) or GENERIC_SEGMENT.match(segment):
            continue
        yield m.group(0), "deployment layout path with a literal segment"


def check_etc_identity(line, ctx):
    for m in RE_ETC_IDENTITY.finditer(line):
        if PLACEHOLDER_TOKENS.search(m.group(2)) or GENERIC_SEGMENT.match(m.group(2)):
            continue
        yield m.group(0), "machine-identity file path names a real project"


def check_homedir(line, ctx):
    for m in RE_HOMEDIR.finditer(line):
        user = m.group(1)
        if PLACEHOLDER_TOKENS.search(user) or GENERIC_USER.match(user):
            continue
        yield m.group(0), "home directory names a person"


def check_uuid(line, ctx):
    for m in RE_UUID.finditer(line):
        digits = set(m.group(0).replace("-", "").lower())
        if len(digits) <= 1:          # 0000…, ffff… — a written-out placeholder
            continue
        yield m.group(0)[:8] + "-…", "UUID identifies a real workspace, project or policy"


def check_secret(line, ctx):
    for rx, label in SECRET_RE:
        for m in rx.finditer(line):
            if PLACEHOLDER_VALUE.search(m.group(0)):
                continue
            yield "<%s, %d chars>" % (label, len(m.group(0))), "secret material"
    if RE_JWT.search(line):
        yield "<jwt>", "JWT in tracked content"
    if RE_PEM.search(line):
        yield "<pem private key>", "private key material"


def check_kv_secret(line, ctx):
    """NAME_WITH_TOKEN/SECRET/KEY/PASSWORD = <high-entropy value>.

    Vendor prefixes are a list of formats somebody remembered; this is the
    shape a credential has regardless of who issued it.
    """
    for m in RE_KV_SECRET.finditer(line):
        val = m.group("val")
        if not looks_random(val, min_len=20, min_entropy=3.2):
            continue
        yield ("%s=<%d chars>" % (m.group("key"), len(val)),
               "secret-shaped name assigned a high-entropy value")


def check_high_entropy(line, ctx):
    """Bare high-entropy run — the catch-all for a token with no name on it."""
    for m in RE_HIGH_ENTROPY.finditer(line):
        run = m.group(0)
        if "/" in run:
            continue                             # a URL path or a $ref, not a token
        if not looks_random(run, min_len=40, min_entropy=4.0, classes_needed=3):
            continue
        yield "<high-entropy, %d chars>" % len(run), "unnamed high-entropy string"


def check_ports(line, ctx):
    strict = ctx["strict"]
    for m in RE_LOCAL_PORT.finditer(line):
        port = m.group(1)
        if port in UPSTREAM_PORTS or port in DOC_PORTS:
            continue
        # repo-wide only the 5-digit range a fleet publishes on; strict scope
        # refuses every literal bound port, documented or not.
        if strict or (len(port) == 5 and "openclaw" in line.lower()):
            yield m.group(0), "host port belongs to a deployment, not to the plugin"
    if "openclaw" in line.lower():
        for m in RE_PORT_NEAR_OPENCLAW.finditer(line):
            if m.group(1) in UPSTREAM_PORTS:
                continue
            yield m.group(1), "host port belongs to a deployment, not to the plugin"


def check_email(line, ctx):
    """Mailboxes, everywhere — WARN repo-wide, FAIL in strict scope.

    This used to return immediately outside strict scope and config surfaces,
    so an address in an ordinary plugin produced neither a FAIL nor a WARN
    while the rule table advertised one. Role mailboxes are still let through
    outside strict scope; a personal address never is.
    """
    for m in RE_EMAIL.finditer(line):
        addr = m.group(0)
        local, domain = addr.split("@", 1)
        if host_allowed(domain) or domain.lower().endswith((".inc", "acme.com", "company.com")):
            continue
        # a role mailbox is not a personal identifier — but a strict-scope
        # plugin still has no business naming any real mailbox.
        if not ctx["strict"] and ROLE_MAILBOX.match(local):
            continue
        yield addr, "personal or organisational address"


def check_model_id(line, ctx):
    if ctx["in_example_block"]:
        return
    for m in MODEL_ID.finditer(line):
        yield m.group(0), "model ids rot; carry the <provider>/<model-id> form instead"


def check_abs_path(line, ctx):
    for m in RE_ABS_PATH.finditer(line):
        path = m.group(0)
        if path.startswith(UPSTREAM_ABS_PREFIXES) or path in ("/etc", "/var", "/usr", "/opt", "/tmp", "/root"):
            continue
        if any(path.startswith(p) for p in ctx["extra_allowed_prefixes"]):
            continue
        if PLACEHOLDER_TOKENS.search(path):
            continue
        yield path, "absolute path is neither upstream-documented nor a placeholder"


RULES = [
    Rule("secret-material", "credential material must never be committed", FAIL, FAIL, check_secret),
    Rule("secret-kv", "secret-shaped name with a high-entropy value", FAIL, FAIL, check_kv_secret),
    Rule("high-entropy", "unnamed high-entropy string", FAIL, FAIL, check_high_entropy),
    Rule("private-key", "private key material", FAIL, FAIL, None),  # folded into secret-material
    Rule("host-name", "server or host name of a real deployment", FAIL, FAIL, check_host_name),
    Rule("private-host", "private endpoint or infrastructure host", FAIL, FAIL, check_private_host),
    Rule("strict-host", "non-vendor host in a strict-scope plugin", OFF, FAIL, check_strict_host),
    Rule("public-ip", "routable IPv4 literal", FAIL, FAIL, check_ipv4),
    Rule("instance-name", "instance name of a real deployment", FAIL, FAIL, check_instance),
    Rule("fleet-path", "deployment layout path with a literal segment", FAIL, FAIL, check_fleet_path),
    Rule("identity-path", "machine-identity file path", FAIL, FAIL, check_etc_identity),
    Rule("home-path", "home directory naming a person", FAIL, FAIL, check_homedir),
    Rule("uuid", "internal identifier", FAIL, FAIL, check_uuid),
    Rule("host-port", "deployment host port", FAIL, FAIL, check_ports),
    Rule("personal-id", "personal identifier", WARN, FAIL, check_email),
    Rule("model-id", "hardcoded model id", OFF, FAIL, check_model_id),
    Rule("abs-path", "undocumented absolute path", OFF, FAIL, check_abs_path),
]
RULES = [r for r in RULES if r.check is not None]
RULES_BY_ID = {r.rid: r for r in RULES}


# ---------------------------------------------------------------------------


def excerpt_matches(selector, excerpt):
    """Does one finding's excerpt fall under an exception's value selector?

    A selector is optional. Without one the exception covers the whole file for
    that rule, which is the blunt instrument that let a credential-bearing URL
    hide behind a permit written for four harmless ones. With one, only the
    named value is excused and the next real endpoint on the same surface still
    fails.

    Two forms:
      sha256-<hex prefix>   digest of the excerpt exactly as the gate prints it,
                            so the exception names no host, path or address —
                            the same reason the rules themselves are shapes.
      <fnmatch glob>        for a value whose shape is safe to write down.
    """
    if not selector:
        return True
    value = excerpt.strip().lower()
    if selector.startswith("sha256-"):
        want = selector[len("sha256-"):].lower()
        if len(want) < 8:
            return False
        return hashlib.sha256(value.encode("utf-8")).hexdigest().startswith(want)
    return fnmatch.fnmatch(value, selector.lower())


def load_baseline(path):
    """path:rule-id[#value-selector]:reason — one intentional exception per line.

    A rule id of '*' exempts the whole file; use it only for vendor payloads.
    A '#value-selector' narrows the exception to findings whose excerpt matches
    (see excerpt_matches) instead of the whole file.
    """
    entries = []
    if not os.path.exists(path):
        return entries
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        for lineno, raw in enumerate(fh, 1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split(":", 2)
            if len(parts) != 3:
                sys.stderr.write(
                    "%s:%d: expected 'path:rule-id[#value-selector]:reason'\n"
                    % (path, lineno))
                sys.exit(1)
            glob, rule, reason = (p.strip() for p in parts)
            selector = None
            if "#" in rule:
                rule, selector = (p.strip() for p in rule.split("#", 1))
                if not selector:
                    sys.stderr.write(
                        "%s:%d: empty value selector after '#'\n" % (path, lineno))
                    sys.exit(1)
            if not reason:
                sys.stderr.write("%s:%d: reason is mandatory\n" % (path, lineno))
                sys.exit(1)
            if rule != "*" and rule not in RULES_BY_ID:
                sys.stderr.write("%s:%d: unknown rule '%s'\n" % (path, lineno, rule))
                sys.exit(1)
            if rule == "*" and selector:
                sys.stderr.write(
                    "%s:%d: '*' exempts a whole file and takes no value selector\n"
                    % (path, lineno))
                sys.exit(1)
            entries.append((glob, rule, selector))
    return entries


def baselined(entries, path, rule, excerpt):
    for glob, allowed_rule, selector in entries:
        if allowed_rule not in ("*", rule):
            continue
        if path == glob or fnmatch.fnmatch(path, glob):
            if excerpt_matches(selector, excerpt):
                return True
    return False


def tracked_files(target):
    """Everything the publication would carry: tracked files AND files not yet
    added to git.

    `git ls-files` alone is a blind spot: at the repository root it returns a
    non-empty list, so a brand-new plugin that has not been `git add`ed yet is
    never walked and the whole tree reports clean. The union with
    `--others --exclude-standard` scans it while still honouring .gitignore.
    """
    files, seen = [], set()
    for extra in ((), ("--others", "--exclude-standard")):
        try:
            out = subprocess.run(
                ["git", "-C", REPO_ROOT, "ls-files", "-z", *extra, "--", target],
                capture_output=True, check=True,
            ).stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            continue
        for f in out.decode("utf-8", "replace").split("\0"):
            if f and f not in seen:
                seen.add(f)
                files.append(f)
    if files:
        return files
    # no git, or a target git does not know (an ignored tree) — walk it
    files = []
    root = target if os.path.isabs(target) else os.path.join(REPO_ROOT, target)
    if os.path.isfile(root):
        return [os.path.relpath(root, REPO_ROOT)]
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIR_NAMES]
        for name in filenames:
            files.append(os.path.relpath(os.path.join(dirpath, name), REPO_ROOT))
    return files


def strict_plugins():
    plugins_dir = os.path.join(REPO_ROOT, "plugins")
    marked = set()
    if not os.path.isdir(plugins_dir):
        return marked
    for name in os.listdir(plugins_dir):
        if os.path.exists(os.path.join(plugins_dir, name, STRICT_MARKER)):
            marked.add("plugins/%s" % name)
    return marked


# Rules that still mean something when all you have is the printable strings
# pulled out of a binary. A compiled artefact carries source paths, embedded
# constants and, when somebody was careless, credentials; it does not carry
# prose, so the context-dependent rules are left out rather than guessed at.
BINARY_RULE_IDS = ("secret-material", "secret-kv", "home-path", "identity-path")

RE_PRINTABLE_RUN = re.compile(rb"[\x20-\x7e]{6,}")


def printable_runs(raw: bytes):
    """Printable ASCII runs of a binary, in file order — `strings(1)` inline."""
    for m in RE_PRINTABLE_RUN.finditer(raw):
        yield m.group(0).decode("ascii", "replace")


def scan_binary(rel_path, raw, ctx):
    """Binaries are not exempt; they are read through their strings.

    A committed .pyc published the absolute source path of the machine that
    built it while the gate reported the file clean, because the extension was
    on a skip list. A rule that is FAIL everywhere cannot have an exception
    carved out by file extension, so a binary is scanned — with the reduced
    ruleset that survives the loss of context.
    """
    findings = []
    rules = [RULES_BY_ID[rid] for rid in BINARY_RULE_IDS if rid in RULES_BY_ID]
    for idx, run in enumerate(printable_runs(raw), 1):
        for rule in rules:
            severity = rule.severity(ctx["strict"])
            if severity == OFF:
                continue
            for excerpt, detail in rule.check(run, ctx) or ():
                findings.append(Finding(
                    rel_path, idx, rule.rid, severity, redact(excerpt),
                    detail + " (in the printable strings of a binary file)"))
    return findings


def scan_file(rel_path, strict_roots, force_strict):
    abs_path = os.path.join(REPO_ROOT, rel_path)
    if not os.path.isfile(abs_path):
        return []
    if os.path.basename(rel_path) in SKIP_BASENAMES:
        return []
    parts = rel_path.split("/")
    if any(p in SKIP_DIR_NAMES for p in parts[:-1]):
        return []
    if os.path.getsize(abs_path) > MAX_BYTES:
        return []

    with open(abs_path, "rb") as fh:
        raw = fh.read()
    binary = rel_path.endswith(BINARY_SUFFIXES) or b"\0" in raw[:4096]
    text = "" if binary else raw.decode("utf-8", "replace")

    plugin_root = None
    strict = force_strict
    for root in strict_roots:
        if rel_path == root or rel_path.startswith(root + "/"):
            strict = True
            plugin_root = root
            break
    if force_strict and plugin_root is None and rel_path.startswith("plugins/"):
        plugin_root = "/".join(parts[:2])

    extra_allowed = []
    if plugin_root:
        plugin_name = plugin_root.split("/")[-1]
        # a plugin owns /etc/<its own name>/ as its operator config namespace
        extra_allowed.append("/etc/%s" % plugin_name)

    base = os.path.basename(rel_path)
    ctx = {
        "strict": strict,
        "config_surface": base in CONFIG_SURFACES,
        "extra_allowed_prefixes": extra_allowed,
        "in_example_block": False,
        "published": rel_path.startswith("plugins/"),
    }

    if binary:
        return scan_binary(rel_path, raw, ctx)

    findings = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if RE_EXAMPLE_OPEN.search(line):
            ctx["in_example_block"] = True
        for rule in RULES:
            severity = rule.severity(strict)
            if severity == OFF:
                continue
            for excerpt, detail in rule.check(line, ctx) or ():
                findings.append(Finding(
                    rel_path, lineno, rule.rid, severity, redact(excerpt), detail))
        if RE_EXAMPLE_CLOSE.search(line) or (ctx["in_example_block"] and line.strip() == "-->"):
            ctx["in_example_block"] = False
    return findings


def main(argv=None):
    ap = argparse.ArgumentParser(
        prog="scrub-check.sh",
        description="Publication gate for the public plugin marketplace.")
    ap.add_argument("targets", nargs="*", default=None,
                    help="paths to scan (default: the whole repository)")
    ap.add_argument("--strict", action="store_true",
                    help="apply the strict ruleset regardless of the %s marker" % STRICT_MARKER)
    ap.add_argument("--baseline", default=DEFAULT_BASELINE,
                    help="baseline file of intentional exceptions")
    ap.add_argument("--no-baseline", action="store_true", help="ignore the baseline")
    ap.add_argument("--format", choices=("text", "json"), default="text")
    args = ap.parse_args(argv)

    targets = args.targets or ["."]
    entries = [] if args.no_baseline else load_baseline(args.baseline)
    strict_roots = strict_plugins()

    seen, files = set(), []
    for target in targets:
        for f in tracked_files(target):
            if f not in seen:
                seen.add(f)
                files.append(f)

    findings, suppressed = [], 0
    for rel_path in sorted(files):
        for finding in scan_file(rel_path, strict_roots, args.strict):
            if baselined(entries, finding.path, finding.rule, finding.excerpt):
                suppressed += 1
                continue
            findings.append(finding)

    fails = [f for f in findings if f.severity == FAIL]
    warns = [f for f in findings if f.severity == WARN]

    if args.format == "json":
        import json
        print(json.dumps({
            "files_scanned": len(files),
            "suppressed": suppressed,
            "fail": len(fails), "warn": len(warns),
            "findings": [{"path": f.path, "line": f.line, "rule": f.rule,
                          "severity": f.severity, "excerpt": f.excerpt,
                          "message": f.message} for f in findings],
        }, indent=2))
    else:
        for group, label in ((fails, "FAIL"), (warns, "WARN")):
            for f in group:
                print("%s %s:%d [%s] %s — %s"
                      % (label, f.path, f.line, f.rule, f.excerpt, f.message))
        print("\nscrub-check: %d files, %d fail, %d warn, %d baselined"
              % (len(files), len(fails), len(warns), suppressed))
        if fails:
            print("Replace each finding with a placeholder (<instance>, <data-root>, "
                  "example.com, 203.0.113.10) or add a justified line to "
                  + os.path.relpath(args.baseline, REPO_ROOT))

    if fails:
        return 1
    return 2 if warns else 0


if __name__ == "__main__":
    sys.exit(main())
