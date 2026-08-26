# -*- coding: utf-8 -*-
"""Group 12, "content and truth" half: hygiene, staleness, language. 12.7, 12.8,
12.9, 12.10, 12.17, 12.18, 12.25 — the checks that ask not "does this parse" but
"is this still true, and is it still safe to hand to a client."

Everything here reads files under macstack/ or shells out to render.py; nothing
here edits lint_folder.py, another rules_*.py, the contract or the schema.
"""
import datetime, glob, io, os, re, subprocess, sys

from lint_folder import rule, Finding, ERROR, WARNING

import lint_folder as _lf                 # only to reach _lf.DOCS, _lf.HERE
import mdblocks                           # v2 parser + the language-ratio regexes
import i18n                               # render.py's own output catalogue


# ---------------------------------------------------------------- shared walk
def _walk_files(root, exts):
    """Every file under `root` whose extension is in `exts`, dot-dirs and
    dot-files skipped — .git and .DS_Store are the filesystem's litter, not the
    folder's content, and a rule that trips on them teaches people to ignore it
    (12.1's own reasoning for the six-entries check, reused here)."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if not d.startswith('.')]
        for fn in sorted(filenames):
            if fn.startswith('.'):
                continue
            if os.path.splitext(fn)[1] in exts:
                yield os.path.join(dirpath, fn)


def _read(path):
    try:
        return io.open(path, encoding='utf-8').read()
    except (IOError, OSError, UnicodeDecodeError):
        return None


# ================================================================== 12.7
@rule('12.7', 'Inbox hygiene')
def r_12_7(c):
    inbox = os.path.join(c.root, 'inbox')
    if not os.path.isdir(inbox):
        return []                         # a fresh folder legitimately lacks intake
    out = []
    names = sorted(f for f in os.listdir(inbox)
                    if not f.startswith('.') and os.path.isfile(os.path.join(inbox, f)))
    files = [f for f in names if f != 'README.md']

    # ---- ASCII-only filenames — a non-ASCII byte greps as absent the same way
    # a homoglyph id does (12.3's argument, extended to the filesystem).
    for f in files:
        try:
            f.encode('ascii')
        except UnicodeEncodeError:
            out.append(Finding('12.7', ERROR, c.rel(os.path.join(inbox, f)), 0,
                               'inbox filename is not ASCII: %r' % f))

    # ---- every file has a manifest entry. inbox/README.md is v2-format (no
    # `format: v3` in the contract), so it is read with mdblocks, not v3.
    manifest_raw = _read(os.path.join(inbox, 'README.md'))
    if manifest_raw is not None:
        _, blocks = mdblocks.parse(manifest_raw)
        named = {e.id for e in mdblocks.entities(blocks, kind='intake') if e.id}
        for f in files:
            if f not in named:
                out.append(Finding('12.7', ERROR, c.rel(os.path.join(inbox, f)), 0,
                                   '%s has no entry in inbox/README.md — the manifest '
                                   'is silent about a file that exists' % f))
    elif files:
        out.append(Finding('12.7', ERROR, c.rel(os.path.join(inbox, 'README.md')), 0,
                           'inbox/ holds %d file(s) but README.md does not exist or '
                           'could not be read — nothing says what they are' % len(files)))

    # ---- content-modifying commits after the add commit. README.md is exempt:
    # it is "the ONLY writable file under inbox/" by the contract's own words, so
    # it is SUPPOSED to gain modifying commits as the manifest grows.
    if files:
        out.extend(_r_12_7_git(c, inbox, files))
    return out


def _r_12_7_git(c, inbox, files):
    try:
        probe = subprocess.run(['git', '-C', c.root, 'rev-parse', '--is-inside-work-tree'],
                               capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return []                         # no git binary — this leg cannot run, skip it
    if probe.returncode != 0 or probe.stdout.strip() != 'true':
        return []                         # not a git repo — legitimate, e.g. a scratch copy
    out = []
    for f in files:
        rel = os.path.join('inbox', f)
        try:
            r = subprocess.run(['git', '-C', c.root, 'log', '--follow',
                                '--diff-filter=M', '--format=%H %ad', '--date=short',
                                '--', rel],
                               capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.SubprocessError):
            continue                      # this one file's history is unreadable; move on
        rows = [ln for ln in r.stdout.splitlines() if ln.strip()]
        if rows:
            out.append(Finding('12.7', ERROR, c.rel(os.path.join(inbox, f)), 0,
                               'modified after it was added (%s) — inbox/ is immutable; '
                               'the edit belongs in README.md\'s manifest, never in the '
                               'file itself' % rows[0]))
    return out


# ================================================================== 12.8
# `[A-Za-z0-9_./-]+\.[a-z]{2,4}:[0-9]+` is the contract's own `line-pointers`
# prohibition (doc-contracts.json). It also matches a URL:port — "api.host.com:3000"
# parses identically to "src/foo.py:42" — so both guards below exist to keep this at
# zero false positives without excluding a real citation like `config.yaml:118`.
LINE_POINTER = re.compile(r'([A-Za-z0-9_./-]+)\.([a-z]{2,4}):([0-9]+)')
_SCHEME_BEFORE = re.compile(r'[A-Za-z][A-Za-z0-9+.-]*:$')
_HOST_LIKE_TLD = frozenset(('com', 'org', 'net', 'io', 'co', 'ai', 'dev', 'app',
                           'gov', 'edu', 'info', 'biz', 'me', 'tv'))
LINK = re.compile(r'\[[^\]]*\]\(([^)\s]+)(?:\s+"[^"]*")?\)')


@rule('12.8', 'No rotting pointers')
def r_12_8(c):
    out = []
    for path in _walk_files(c.root, ('.md', '.json')):
        text = _read(path)
        if text is None:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for m in LINE_POINTER.finditer(line):
                stem, ext, _num = m.group(1), m.group(2), m.group(3)
                if _SCHEME_BEFORE.search(line[:m.start()]) and line[m.start():].startswith('//'):
                    continue               # scheme://host:port — not a citation
                if ext in _HOST_LIKE_TLD and '/' not in stem:
                    continue               # bare host.tld:port — not a citation
                out.append(Finding('12.8', ERROR, c.rel(path), n,
                                   'a line-number citation that will rot on the next '
                                   'edit: %s — name a symbol or a title instead'
                                   % m.group(0)))
    out.extend(_r_12_8_links(c))
    return out


def _r_12_8_links(c):
    try:
        top = subprocess.run(['git', '-C', c.root, 'rev-parse', '--show-toplevel'],
                             capture_output=True, text=True, timeout=10)
        repo_root = top.stdout.strip() if top.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        repo_root = None
    if not repo_root:
        return []                         # cannot say what "outside the repo" means here
    repo_root = os.path.realpath(repo_root)
    out = []
    for path in _walk_files(c.root, ('.md',)):
        text = _read(path)
        if text is None:
            continue
        for n, line in enumerate(text.splitlines(), 1):
            for m in LINK.finditer(line):
                target = m.group(1)
                if re.match(r'^[a-zA-Z][a-zA-Z0-9+.-]*:', target) or target.startswith('#'):
                    continue               # a scheme (http:, mailto:) or an in-page anchor
                frag = target.split('#', 1)[0]
                if not frag:
                    continue
                base = c.root if frag.startswith('/') else os.path.dirname(path)
                resolved = os.path.realpath(os.path.join(base, frag.lstrip('/')))
                if resolved != repo_root and not resolved.startswith(repo_root + os.sep):
                    out.append(Finding('12.8', ERROR, c.rel(path), n,
                                       'link target resolves outside the repository: %s'
                                       % target))
    return out


# ================================================================== 12.9
# Names of env keys are the spec's business on purpose (they are what a deploy needs
# to set) — only VALUES that look like real credentials are the violation. Every
# pattern below was run against the live corpus (78 cases, 37 screens, the full
# macstack.json) with the results in the module's own report; each produced zero
# hits, which is what keeps this at zero false positives rather than a rule that
# cries wolf and gets switched off.
_AWS_KEY = re.compile(r'\bAKIA[0-9A-Z]{16}\b')
_GH_TOKEN = re.compile(r'\bgh[pousr]_[A-Za-z0-9]{20,}\b')
_SK_KEY = re.compile(r'\bsk-[A-Za-z0-9_-]{20,}\b')
_PEM = re.compile(r'-----BEGIN [A-Z ]*PRIVATE KEY-----')
_URL_CRED = re.compile(r'[a-zA-Z][a-zA-Z0-9+.-]*://[^\s/:@]+:[^\s/:@]+@')
_HEX_RUN = re.compile(r'\b[0-9a-fA-F]{32,}\b')
# base64 candidate: no '/' (a path separator in every false positive measured — see
# the report), and either padded with '=' or mixing case AND a digit, because a
# naturalistic lowercase word run never does both at once.
_B64_RUN = re.compile(
    r'\b[A-Za-z0-9+]{16,}={1,2}(?!\w)'
    r'|\b(?=[A-Za-z0-9+]{32,}\b)(?=[A-Za-z0-9+]*[a-z])(?=[A-Za-z0-9+]*[A-Z])'
    r'(?=[A-Za-z0-9+]*[0-9])[A-Za-z0-9+]{32,}\b')
_ENV_ASSIGN = re.compile(r'^[ \t]*([A-Z][A-Z0-9_]{2,})\s*=\s*(\S.*)$')
_PLACEHOLDER_RHS = re.compile(
    r'^(["\']?)(<.*>|\.\.\.|x{3,}|\*{3,}|-|—|change[_-]?me|your[_-].*|'
    r'replace[_-]?me|todo|tbd|example.*|placeholder.*)\1$', re.I)


def _secret_findings(path, text, rel):
    # The matched VALUE is never put into the message — a finding that quotes the
    # secret it caught just relocates the leak into the lint output (and from there
    # into CI logs, terminal scrollback, this very report). Kind, line and length
    # are enough to act on; the payload is not reproduced.
    out = []
    for n, line in enumerate(text.splitlines(), 1):
        for pat, why in ((_AWS_KEY, 'an AWS access key id'),
                         (_GH_TOKEN, 'a GitHub token'),
                         (_SK_KEY, 'an sk- style API key'),
                         (_PEM, 'a PEM private key block'),
                         (_URL_CRED, 'a URL carrying user:password@')):
            m = pat.search(line)
            if m:
                out.append(Finding('12.9', ERROR, rel, n,
                                   '%s (%d characters) — value withheld from this '
                                   'finding on purpose' % (why, len(m.group(0)))))
        for pat, why in ((_HEX_RUN, 'a long hex run'), (_B64_RUN, 'a long base64-shaped run')):
            m = pat.search(line)
            if m:
                out.append(Finding('12.9', ERROR, rel, n,
                                   '%s that reads like a credential (%d characters) — '
                                   'value withheld from this finding on purpose'
                                   % (why, len(m.group(0)))))
        m = _ENV_ASSIGN.match(line)
        if m and not _PLACEHOLDER_RHS.match(m.group(2).strip()):
            out.append(Finding('12.9', ERROR, rel, n,
                               '%s is assigned a value that is not an obvious '
                               'placeholder (%d characters) — value withheld from '
                               'this finding on purpose'
                               % (m.group(1), len(m.group(2).strip()))))
    return out


@rule('12.9', 'No secrets anywhere under macstack/')
def r_12_9(c):
    out = []
    for path in _walk_files(c.root, ('.md', '.json')):
        text = _read(path)
        if text is None:
            continue
        out.extend(_secret_findings(path, text, c.rel(path)))
    return out


# ================================================================== 12.10
_APPLIED = re.compile(r'<!--\s*macstack:applied\s*-->')
_SUPERSEDED = re.compile(
    r'(?i)supersed|за[м]ен[её]н|устаре[лвш]|ersetzt|застаріл|заміне[нн]')


def _delta_settled(text):
    m = _APPLIED.search(text)
    if m:
        for line in text[m.end():].strip().splitlines()[:5]:
            line = line.strip()
            if not line:
                continue
            return not line.startswith('_TODO')      # the seed/migration placeholder marker
        return False                                  # anchor present, body still empty
    return bool(_SUPERSEDED.search(text))


@rule('12.10', 'No parallel spec', WARNING)
def r_12_10(c):
    deltas = os.path.join(c.root, 'history', 'deltas')
    if not os.path.isdir(deltas):
        return []
    out = []
    today = datetime.date.today()
    for name in sorted(os.listdir(deltas)):
        m = re.match(r'^(\d{4})-(\d{2})-(\d{2})-', name)
        if not name.endswith('.md') or not m:
            continue                      # not this rule's business — 12.3/naming owns that
        try:
            age = (today - datetime.date(int(m.group(1)), int(m.group(2)),
                                         int(m.group(3)))).days
        except ValueError:
            continue
        if age <= 30:
            continue
        text = _read(os.path.join(deltas, name))
        if text is None or _delta_settled(text):
            continue
        out.append(Finding('12.10', WARNING, c.rel(os.path.join(deltas, name)), 0,
                           'a %d-day-old delta with neither an applied banner nor a '
                           'superseded note — it is read as a second specification, '
                           'not a settled proposal' % age))
    return out


# ================================================================== 12.17
_REVIEW_DATE = re.compile(r'^(\d{4}-\d{2}-\d{2})-.*-conformance\.md$')


def _latest_conformance_date(root):
    """The newest history/reviews/<date>-*-conformance.md date, or None. The
    contract gives this ONE global meaning ("counts as the check") rather than
    scoping it per document, so it is applied the same way here — a project-wide
    audit moves every document's clock forward together, not one at a time."""
    reviews = os.path.join(root, 'history', 'reviews')
    if not os.path.isdir(reviews):
        return None
    best = None
    for name in os.listdir(reviews):
        m = _REVIEW_DATE.match(name)
        if not m:
            continue
        try:
            d = datetime.date(*(int(x) for x in m.group(1).split('-')))
        except ValueError:
            continue
        if best is None or d > best:
            best = d
    return best


@rule('12.17', 'Documents have a shelf life')
def r_12_17(c):
    if not c.files:
        return []
    out = []
    today = datetime.date.today()
    fresh_days = (c.spec.get('docs') or {}).get('freshness_days') or 30
    latest_review = _latest_conformance_date(c.root)
    for key in sorted(c.files):
        meta = c.files.get(key) or {}
        path = c.path_of(key)
        rel = c.rel(path) if path else 'macstack.json'
        reviewed = meta.get('reviewed')
        if not reviewed:
            out.append(Finding('12.17', ERROR, rel, 0,
                               'docs.files.%s carries no `reviewed` date — nobody has '
                               'ever recorded checking it against the code, which is '
                               'worse than being stale' % key))
            continue
        try:
            d = datetime.date(*(int(x) for x in reviewed.split('-')))
        except (ValueError, TypeError):
            out.append(Finding('12.17', ERROR, rel, 0,
                               'docs.files.%s.reviewed is not a YYYY-MM-DD date: %r'
                               % (key, reviewed)))
            continue
        if latest_review and latest_review > d:
            d = latest_review
        age = (today - d).days
        if age <= fresh_days:
            continue
        sev = ERROR if age > fresh_days * 2 else WARNING
        out.append(Finding('12.17', sev, rel, 0,
                           '%s was last checked against the code %d days ago '
                           '(budget %d) — reviewed=%s' % (key, age, fresh_days,
                                                          d.isoformat())))
    return out


# ================================================================== 12.18
_RENDER_JOB = {'architecture': os.path.join('generated', 'ARCHITECTURE.md'),
              'index': os.path.join('generated', 'INDEX.md'),
              'readme': 'README.md'}


@rule('12.18', "A generated document equals its source")
def r_12_18(c):
    docs = c.contract.get('documents') or {}
    gen_keys = sorted(k for k, d in docs.items() if d.get('generated'))
    if not gen_keys:
        return []
    out = []
    uncovered = [k for k in gen_keys if k not in _RENDER_JOB]
    for k in uncovered:
        # This is exactly the historical README.md failure: a contract entry says
        # `generated` and no generator exists for it, so the rule was unsatisfiable
        # and silently reported nothing for three releases. The gap itself is the
        # finding now, not a green rule that never actually looked.
        out.append(Finding('12.18', ERROR, docs[k].get('path') or k, 0,
                           'the contract marks `%s` generated but render.py has no '
                           '--only job for it — this rule cannot verify it' % k))
    checked = [k for k in gen_keys if k in _RENDER_JOB]
    if not checked:
        return out
    render_py = os.path.join(_lf.DOCS, 'render.py')
    if not os.path.exists(render_py):
        out.append(Finding('12.18', ERROR, 'render.py', 0,
                           'the renderer is missing at %s — cannot verify %s'
                           % (render_py, ', '.join(checked))))
        return out
    try:
        proc = subprocess.run([sys.executable, render_py, c.root, '--check'],
                              capture_output=True, text=True, timeout=90)
    except (OSError, subprocess.SubprocessError) as e:
        out.append(Finding('12.18', ERROR, 'render.py', 0,
                           'could not run the renderer: %s: %s' % (type(e).__name__, e)))
        return out
    lines = set((proc.stdout or '').splitlines())
    for k in checked:
        path = os.path.join(c.root, _RENDER_JOB[k])
        drift = i18n.msg(c.lang, 'drift', path=path)
        insync = i18n.msg(c.lang, 'in_sync', path=path)
        if drift in lines:
            out.append(Finding('12.18', ERROR, c.rel(path), 0,
                               '%s no longer matches a fresh render of `%s` — either it '
                               'was hand-edited or the source moved and nobody '
                               're-rendered; re-render it, never hand-fix it'
                               % (_RENDER_JOB[k], docs[k].get('generated'))))
        elif insync not in lines:
            out.append(Finding('12.18', ERROR, c.rel(path), 0,
                               'render.py --check gave no verdict for %s — cannot '
                               'confirm it is in sync (stderr: %s)'
                               % (_RENDER_JOB[k], (proc.stderr or '').strip()[:200])))
    return out


# ================================================================== 12.25
# mdblocks.CYR / LAT / IDTOK are reused as-is — simple character classes and token
# patterns, no pairing risk. mdblocks.STRIP is NOT reused: it is compiled with
# re.S and applied to the WHOLE document in one `sub`, so its single-backtick
# alternative `` `[^`]*` `` pairs across line breaks exactly the way strip_fences'
# own docstring warns triple-backtick pairing does. Measured on the live corpus:
# history/TASKS.md carries one stray unmatched backtick (153 in the file, an odd
# count), and mdblocks.STRIP's cross-line pairing then swallows several headings
# and a table as one giant "code span" — mostly Cyrillic, so the ratio it leaves
# behind reads as 27% foreign. A per-line stripper on the same file (never letting
# a backtick pair reach past its own line, since a code span in this format is
# never written to span one) gives 5.3%. render.py never calls foreign_ratio, but
# migrate.py does, so this is not a hypothetical — it is a live bug upstream in
# mdblocks.py, out of scope here to fix (not this module), and worked around
# locally by never crossing a newline while stripping.
_INLINE_CODE = re.compile(r'`[^`\n]*`')
_ANCHOR_LINE = re.compile(r'<!--[^\n]*-->')
_MD_LINK_LINE = re.compile(r'\[[^\]\n]*\]\([^)\n]*\)')
_MIN_LETTERS = 200          # mdblocks.foreign_ratio's own floor: too short to mean anything
_MIN_LINE_LETTERS = 8       # a worst LINE below this is one stray word, not a finding


def _strip_for_language(text):
    """The same exclusions mdblocks.STRIP names — code spans, anchors, links —
    applied per line so a stray or odd-numbered backtick can never pair across a
    line break and eat unrelated prose."""
    body = mdblocks.strip_fences(text)
    out = []
    for line in body.splitlines():
        line = _ANCHOR_LINE.sub(' ', line)
        line = _MD_LINK_LINE.sub(' ', line)
        line = _INLINE_CODE.sub(' ', line)
        out.append(line)
    return '\n'.join(out)


def _foreign_ratio(text, lang):
    body = mdblocks.IDTOK.sub(' ', _strip_for_language(text))
    cyr, lat = len(mdblocks.CYR.findall(body)), len(mdblocks.LAT.findall(body))
    total = cyr + lat
    if total < _MIN_LETTERS:
        return None
    wrong = lat if lang in ('ru', 'uk') else cyr
    return wrong / float(total)


def _worst_line(text, lang):
    stripped_lines = _strip_for_language(text).splitlines()
    raw_lines = text.splitlines()
    best_n, best_ratio = 0, -1.0
    for n, sline in enumerate(stripped_lines, 1):
        body = mdblocks.IDTOK.sub(' ', sline)
        cyr, lat = len(mdblocks.CYR.findall(body)), len(mdblocks.LAT.findall(body))
        total = cyr + lat
        if total < _MIN_LINE_LETTERS:
            continue
        ratio = (lat if lang in ('ru', 'uk') else cyr) / float(total)
        if ratio > best_ratio:
            best_ratio, best_n = ratio, n
    if best_n and best_n <= len(raw_lines):
        return best_n, raw_lines[best_n - 1].strip()[:80]
    return 0, ''


def _lang_for(c, key, decl, text):
    override = (c.files.get(key) or {}).get('language')
    if override:
        return override
    if not decl.get('format') == 'v3':
        # A dated instance (delta/rulings/review) has no docs.files entry of its own;
        # its v2 header can carry its own `lang=`, and a document that says so
        # honestly should not be measured against a default it never claimed.
        header, _ = mdblocks.parse(text)
        if header.get('lang'):
            return header['lang']
    return c.lang


@rule('12.25', 'The document is written in its declared language')
def r_12_25(c):
    out = []
    docs = c.contract.get('documents') or {}
    seen_paths = set()
    for key, decl in sorted(docs.items()):
        if decl.get('generated'):
            continue                      # the standard that forbids translating ids
        p = decl.get('path') or ''
        if not p or '<' in p:
            continue                      # a dated-instance pattern, walked separately below
        text = c.text.get(key)
        path = c.path_of(key)
        if text is None:
            if not path or not os.path.exists(path):
                continue
            text = _read(path)
            if text is None:
                continue
        seen_paths.add(os.path.realpath(path))
        out.extend(_r_12_25_one(c, key, decl, path, text))

    # dated instances: real files behind a `<placeholder>` path in the contract.
    # None of the three (delta, rulings, review) is `generated`, so all are in scope.
    for subdir, key in (('deltas', 'delta'), (os.path.join('decisions'), 'rulings'),
                        ('reviews', 'review')):
        decl = docs.get(key) or {}
        for path in sorted(glob.glob(os.path.join(c.root, 'history', subdir, '*.md'))):
            if os.path.realpath(path) in seen_paths:
                continue
            text = _read(path)
            if text is None:
                continue
            out.extend(_r_12_25_one(c, key, decl, path, text))
    return out


def _r_12_25_one(c, key, decl, path, text):
    lang = _lang_for(c, key, decl, text)
    ratio = _foreign_ratio(text, lang)
    if ratio is None or ratio <= 0.15:
        return []
    n, snippet = _worst_line(text, lang)
    sev = ERROR if decl.get('audience') in ('client', 'both') else WARNING
    return [Finding('12.25', sev, c.rel(path), n,
                    '%.0f%% of its letters are outside the %s alphabet (budget 15%%) — '
                    'worst line: %s' % (ratio * 100, lang, snippet or '(no single line '
                    'carries enough letters to blame)'))]
