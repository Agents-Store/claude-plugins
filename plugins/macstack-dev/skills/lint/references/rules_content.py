# -*- coding: utf-8 -*-
"""Group 12, content and truth: 12.11, 12.12, 12.22, 12.23, 12.27, 12.32, 12.35.

Everything here checks that a document's CLAIMS are backed by something — a test,
the spec, another document, git history — not just that its shape parses. Shape is
rule group 12.21 and friends; this module is the half that can be right in form and
still be lying.
"""
import io
import os
import re
import subprocess

from lint_folder import rule, Finding, ERROR, WARNING
import v3

HEADING = re.compile(r'^#{1,6}\s')
BOLD_HEAD = re.compile(r'^\*\*(.+?)[.:]?\*\*\s*$')

# v3.READ speaks every field label the client documents use; 'covers' and 'kind'
# are two of them, so borrow the translation instead of hand-copying the words a
# second time and letting them drift the way the shipped `gate` labels once did.
_TC_LABELS = {}
for _tbl in (v3.READ.get('ru') or {}, v3.READ.get('en') or {}):
    for _lab, _key in _tbl.items():
        if _key in ('covers', 'kind'):
            _TC_LABELS[_lab] = _key

# 'preconditions', 'steps', 'evidence' and 'expected' are not in doc-contracts.json's
# `prose` catalogue at all — they were never given a label there, in either language.
# This is a real gap in shared data this module does not own; these four words are a
# local stand-in, taken from TEST-CASES.md's own "как читать" paragraph ("предусловия
# и шаги", "улику", "что должно получиться"), not invented from nothing.
_TC_PROSE = {
    'ru': {u'предусловия': 'preconditions', u'шаги': 'steps', u'улика': 'evidence',
           u'что должно получиться': 'expected'},
    'en': {'preconditions': 'preconditions', 'steps': 'steps', 'evidence': 'evidence',
           'expected': 'expected'},
}

_BARE_FILE = re.compile(
    r'^[\w./-]+\.(ts|tsx|js|jsx|mjs|cjs|py|go|rb|java|kt|swift)$', re.I)


# ---------------------------------------------------------------- shared readers
def _acceptance_bullets(lines, start, end, label):
    """Top-level bullets under the acceptance prose header, read off the document's
    OWN lines rather than through v3's per-item `.sections` dict.

    v3.read() only appends a line to the current prose section when neither BULLET
    nor PROSE claims it first — and nine live acceptance bullets in USER-CASES.md
    read "- **<word>:** ..." (a role name in bold, colon and all, e.g. "- **коуч**
    делает..." has no colon so it's fine, but several DO: "- **счёт OHAWO:**
    выставляется..."). BULLET claims those as an unknown field bullet and they
    silently vanish from `.sections`. Counted through `.sections`: 369. Counted
    off the lines directly, the way a person reading the file would: 378 — the
    number this rule and 12.32 both need to be right, not approximately right.
    """
    norm = label.strip().rstrip('.:').lower()
    out = []
    in_acc = False
    for n in range(start, min(end, len(lines))):
        line = lines[n]
        stripped = line.strip()
        m = BOLD_HEAD.match(stripped)
        if m:
            in_acc = m.group(1).strip().rstrip('.:').lower() == norm
            continue
        if HEADING.match(line):
            in_acc = False
            continue
        if not in_acc:
            continue
        if not stripped:
            in_acc = False
            continue
        indent = len(line) - len(line.lstrip(' '))
        if indent == 0 and stripped[:1] == '-':
            out.append((n, stripped))
    return out


def _case_acceptance_counts(lines, items, label):
    counts = {}
    for it in items:
        if it.level == 3 and it.id:
            counts[it.id] = len(_acceptance_bullets(lines, it.head_line, it.span[1], label))
    return counts


def _testcase_pattern(c):
    pat = ((c.contract.get('id_spaces') or {}).get('testcase') or {}).get('pattern')
    return re.compile(pat) if pat else re.compile(r'^[A-Za-z]-\d{2}\.T\d+$')


def _tc_split(text):
    """'~~C-04.T2~~ · DROPPED …' / 'C-06.T3 · Something' -> (id, title, struck)."""
    text = text.strip()
    if text.startswith('~~'):
        m = re.match(r'^~~(.+?)~~\s*·\s*(.*)$', text)
        if m:
            return m.group(1).strip(), m.group(2).strip(), True
        return None, text, True
    m = re.match(r'^(\S+)\s*·\s*(.*)$', text)
    if m:
        return m.group(1).strip(), m.group(2).strip(), False
    return None, text, False


def _read_testcases(text, id_pattern):
    """Walk TEST-CASES.md by hand for the one heading shape v3.py cannot see.

    v3._split_heading() recognises case / open_item / milestone / Z-case id shapes
    — none of them is `<case>.T<n>`, the testcase id this document's contract
    heading form actually uses (`### C-06.T3 · …`). That regex lives in shared
    infra this module does not own (`documents/references/v3.py`); rather than
    edit it, this reuses v3's BULLET/PROSE line grammar and supplies the one
    missing heading match locally.
    """
    lines = text.split('\n')
    items, cur = [], None
    for n, line in enumerate(lines):
        hm = v3.HEADING.match(line)
        if hm and len(hm.group(1)) == 3:
            ident, title, struck = _tc_split(hm.group(2))
            if cur is not None:
                cur['end'] = n
            if ident and id_pattern.match(ident):
                cur = dict(id=ident, title=title, struck=struck, head_line=n,
                           fields={}, field_lines={}, sections={}, end=len(lines))
                items.append(cur)
            else:
                cur = None
            continue
        if cur is None:
            continue
        bm = v3.BULLET.match(line)
        if bm:
            key = _TC_LABELS.get(bm.group(1).strip().lower())
            if key:
                cur['fields'][key] = v3._value(bm.group(2), 'ru')
                cur['field_lines'][key] = n
            continue
        pm = v3.PROSE.match(line.strip())
        if pm:
            label = pm.group(1).strip().rstrip('.:').lower()
            sec = cur['sections'].setdefault(label, {'line': n, 'body': []})
            if pm.group(2).strip():
                sec['body'].append(pm.group(2))
            continue
        if cur['sections']:
            last = list(cur['sections'])[-1]
            cur['sections'][last]['body'].append(line)
    return items


def _tc_section(t, key, lang):
    labels = _TC_PROSE.get(lang) or _TC_PROSE['en']
    want = None
    for word, k in labels.items():
        if k == key:
            want = word
    for lab, sec in t['sections'].items():
        if lab == want or lab == key:
            return sec
    return None


def _tc_section_text(t, key, lang):
    sec = _tc_section(t, key, lang)
    if not sec:
        return ''
    return ' '.join(b.strip() for b in sec['body'] if b.strip()).strip()


def _looks_like_bare_filename(text):
    """'a bare filename is not evidence' — a `file.ts:NNN` pointer is already
    banned everywhere by 12.8; this catches the filename ALONE, with the line
    number stripped off, which 12.8's pattern does not match."""
    text = text.strip().strip('`')
    if ' ' in text or not text:
        return False
    return bool(_BARE_FILE.match(text)) or ('/' in text and '.' in text.rsplit('/', 1)[-1])


def _covered_acceptance_ids(c):
    text = c.text.get('test_cases')
    if not text:
        return set()
    tests = _read_testcases(text, _testcase_pattern(c))
    out = set()
    for t in tests:
        if t['struck']:
            continue
        v = t['fields'].get('covers')
        if isinstance(v, list):
            out.update(x for x in v if x)
        elif v:
            out.add(v)
    return out


# ---------------------------------------------------------------- 12.11
@rule('12.11', 'Every acceptance bullet is verified')
def r_12_11(c):
    doc = c.docs.get('user_cases')
    if doc is None:
        return []
    lang = doc.header.get('lang') or c.lang
    label = c.prose_label('acceptance', lang)
    covered = _covered_acceptance_ids(c)
    _, cases = c.entities_of('user_cases', 'case')
    out = []
    for it in cases:
        bullets = _acceptance_bullets(doc.lines, it.head_line, it.span[1], label)
        for i, (n, text) in enumerate(bullets, 1):
            aid = '%s.a%d' % (it.id, i)
            if aid not in covered:
                out.append(Finding('12.11', ERROR, c.rel(doc.path), n + 1,
                                   '%s has no test in generated/TEST-CASES.md covering '
                                   'it: %s' % (aid, text[:70])))
    return out


# ---------------------------------------------------------------- 12.12
@rule('12.12', 'Test cases are well formed')
def r_12_12(c):
    text = c.text.get('test_cases')
    if not text:
        return []
    hdr = v3.header(text)
    lang = hdr.get('lang') or c.lang
    tests = _read_testcases(text, _testcase_pattern(c))
    p = c.path_of('test_cases')
    path = c.rel(p) if p else 'generated/TEST-CASES.md'
    out = []
    for t in tests:
        ln = t['head_line'] + 1
        if t['struck']:
            if not re.search(u'—\\s*\\S', t['title']):
                out.append(Finding('12.12', ERROR, path, ln,
                                   '%s is struck but names no reason after —' % t['id']))
            continue
        if 'covers' not in t['fields']:
            out.append(Finding('12.12', ERROR, path,
                               t['field_lines'].get('kind', t['head_line']) + 1,
                               '%s: no covers' % t['id']))
        if 'kind' not in t['fields']:
            out.append(Finding('12.12', ERROR, path, ln, '%s: no kind' % t['id']))
            continue
        kind = t['fields']['kind']
        kln = t['field_lines']['kind'] + 1
        if kind == 'manual':
            for key in ('preconditions', 'steps'):
                if not _tc_section_text(t, key, lang):
                    out.append(Finding('12.12', ERROR, path, kln,
                                       '%s: a manual test must declare %s'
                                       % (t['id'], key)))
        elif kind == 'auto':
            sec = _tc_section(t, 'evidence', lang)
            evln = sec['line'] + 1 if sec else kln
            body = _tc_section_text(t, 'evidence', lang)
            if not body:
                out.append(Finding('12.12', ERROR, path, evln,
                                   '%s: an auto test must name the test title that '
                                   'proves it' % t['id']))
            elif _looks_like_bare_filename(body):
                out.append(Finding('12.12', ERROR, path, evln,
                                   '%s: evidence is a bare filename, not a test title '
                                   'that can be found and run: %s' % (t['id'], body)))
        else:
            out.append(Finding('12.12', ERROR, path, kln,
                               '%s: kind %r is neither auto nor manual' % (t['id'], kind)))
    return out


# ---------------------------------------------------------------- 12.22
@rule('12.22', "The spec agrees with AUTOMATION.md")
def r_12_22(c):
    doc = c.docs.get('automation')
    if doc is None:
        return []
    out = []
    path = c.rel(doc.path)

    _, role_items = c.entities_of('automation', 'role')
    doc_roles = dict((it.id, it) for it in role_items if it.id)
    spec_roles = set(r.get('id') for r in (c.spec.get('roles') or []) if r.get('id'))
    for rid in sorted(spec_roles - set(doc_roles)):
        out.append(Finding('12.22', ERROR, path, 0,
                           'role %s is in the spec, named by no document' % rid))
    for rid in sorted(set(doc_roles) - spec_roles):
        it = doc_roles[rid]
        out.append(Finding('12.22', ERROR, path, (it.head_line or 0) + 1,
                           'role %s is in the document, not in the spec' % rid))

    # Only a task with a `human` block is AUTOMATION.md's business — a workflow-only
    # task is the machine half, and the document explicitly does not own it (see the
    # entity's own note: "never a vague both").
    _, task_items = c.entities_of('automation', 'role_task')
    doc_tasks = dict((it.id, it) for it in task_items if it.id)
    spec_human = {}
    for proc in c.spec.get('processes') or []:
        for t in proc.get('tasks') or []:
            if t.get('human') and t.get('id'):
                spec_human[t['id']] = t['human']
    for tid in sorted(set(spec_human) - set(doc_tasks)):
        out.append(Finding('12.22', ERROR, path, 0,
                           'task %s has a human gate in the spec, named by no document'
                           % tid))
    for tid in sorted(set(doc_tasks) - set(spec_human)):
        it = doc_tasks[tid]
        out.append(Finding('12.22', ERROR, path, (it.head_line or 0) + 1,
                           'task %s is in the document, but the spec has no human '
                           'gate for it' % tid))
    for tid in sorted(set(doc_tasks) & set(spec_human)):
        it = doc_tasks[tid]
        want = spec_human[tid].get('gate')
        got = it.fields.get('gate')
        if got != want:
            out.append(Finding('12.22', ERROR, path, (it.head_line or 0) + 1,
                               'task %s: document says gate %r, spec says %r'
                               % (tid, got, want)))

    _, trig_items = c.entities_of('automation', 'trigger')
    doc_trigs = dict((it.id, it) for it in trig_items if it.id)
    spec_trigs = set(t.get('id') for t in (c.spec.get('triggers') or []) if t.get('id'))
    for tid in sorted(spec_trigs - set(doc_trigs)):
        out.append(Finding('12.22', ERROR, path, 0,
                           'trigger %s is in the spec, named by no document' % tid))
    for tid in sorted(set(doc_trigs) - spec_trigs):
        it = doc_trigs[tid]
        out.append(Finding('12.22', ERROR, path, (it.head_line or 0) + 1,
                           'trigger %s is in the document, not in the spec' % tid))
    return out


# ---------------------------------------------------------------- 12.23
_OPENABLE = set(['web', 'admin_ui', 'dashboard', 'approval_center', 'form'])
_SCREEN_REF = re.compile(r'^interfaces\[id=([^\]]+)\]$')


@rule('12.23', 'Every screen is declared')
def r_12_23(c):
    doc = c.docs.get('ux_ui')
    if doc is None:
        return []
    out = []
    path = c.rel(doc.path)
    _, screens = c.entities_of('ux_ui', 'screen')

    bound = set()
    by_path = {}
    for it in screens:
        m = _SCREEN_REF.match(it.ref or '')
        if m:
            bound.add(m.group(1))
        p = it.fields.get('path')
        if p:
            by_path.setdefault(p, []).append(it)

    ifaces = dict((i.get('id'), i) for i in (c.spec.get('interfaces') or []))
    for iid in sorted(ifaces):
        i = ifaces[iid]
        if i.get('type') in _OPENABLE and iid not in bound:
            out.append(Finding('12.23', ERROR, path, 0,
                               'interfaces[id=%s] (%s) — a person opens it, and no '
                               'screen in UX-UI.md resolves to it' % (iid, i.get('type'))))

    for p in sorted(by_path):
        its = by_path[p]
        if len(its) > 1:
            ids = ', '.join(sorted(it.id for it in its))
            for it in its:
                out.append(Finding('12.23', ERROR, path, (it.head_line or 0) + 1,
                                   'address %s is shared by %d screens: %s'
                                   % (p, len(its), ids)))

    lang = doc.header.get('lang') or c.lang
    forb_label = c.prose_label('forbidden', lang)
    for it in screens:
        body = None
        for lab in it.sections:
            if lab.rstrip('.:').strip() == forb_label:
                body = it.sections[lab]
        nb = sum(1 for l in (body or []) if l.strip().startswith('-'))
        if nb == 0:
            out.append(Finding('12.23', ERROR, path, (it.head_line or 0) + 1,
                               '%s: "%s" is empty — a screen with nothing forbidden is '
                               'a prohibition nobody checked' % (it.id, forb_label)))
    return out


# ---------------------------------------------------------------- 12.27
def _index_runs(c, doc, min_run=3):
    ids = set(it.id for it in doc.items if it.id)
    if not ids:
        return []
    head_line_of = {}
    for it in doc.items:
        if it.id and it.id not in head_line_of:
            head_line_of[it.id] = it.head_line
    pat = re.compile(r'(?<![\w-])(?:' +
                     '|'.join(re.escape(i) for i in sorted(ids, key=len, reverse=True)) +
                     r')(?![\w-])')
    out, run = [], []

    def flush():
        if len(run) >= min_run:
            n0, ident0, text0 = run[0]
            out.append(Finding('12.27', ERROR, c.rel(doc.path), n0 + 1,
                               'a run of %d lines each naming an id that is also a '
                               'heading further down this document (starting at %s: '
                               '%s) — a hand-written index; generate it into '
                               'generated/INDEX.md instead' % (len(run), ident0, text0)))
        del run[:]

    for n, line in enumerate(doc.lines):
        s = line.strip()
        structural = s.startswith('|') or bool(re.match(r'^[-*]\s', s))
        if not structural:
            flush()
            continue
        m = pat.search(line)
        if not m or head_line_of.get(m.group(0), -1) <= n:
            flush()
            continue
        run.append((n, m.group(0), s[:60]))
    flush()
    return out


@rule('12.27', 'No hand-written index')
def r_12_27(c):
    out = []
    for key in sorted(c.docs):
        out.extend(_index_runs(c, c.docs[key]))
    return out


# ---------------------------------------------------------------- 12.32
def _run_git(cwd, args):
    try:
        r = subprocess.run(['git'] + args, cwd=cwd, capture_output=True,
                           text=True, timeout=15)
    except Exception:
        return None
    if r.returncode != 0:
        return None
    return r.stdout


def _latest_tag(root):
    out = _run_git(root, ['describe', '--tags', '--abbrev=0'])
    return out.strip() if out else None


def _git_root(root):
    out = _run_git(root, ['rev-parse', '--show-toplevel'])
    return out.strip() if out else None


def _git_show(root, tag, rel_path):
    rel_path = rel_path.replace(os.sep, '/')
    return _run_git(root, ['show', '%s:%s' % (tag, rel_path)])


@rule('12.32', 'Acceptance ids are stable', WARNING)
def r_12_32(c):
    doc = c.docs.get('user_cases')
    if doc is None:
        return []
    tag = _latest_tag(c.root)
    if not tag:
        return []                       # no tag reachable — nothing to compare against
    groot = _git_root(c.root)
    if not groot:
        return []
    rel = os.path.relpath(doc.path, groot)
    old_text = _git_show(c.root, tag, rel)
    if not old_text:
        return []                       # file did not exist at that tag — nothing to compare
    lang = doc.header.get('lang') or c.lang
    label = c.prose_label('acceptance', lang)
    old_hdr = v3.header(old_text)
    if (old_hdr.get('version') or None) != (doc.header.get('version') or None):
        return []                       # version bumped — the drop, if any, was declared
    old_doc = v3.read_doc(old_text)
    old_counts = _case_acceptance_counts(old_doc.lines, old_doc.items, label)
    now_counts = _case_acceptance_counts(doc.lines, doc.items, label)
    out = []
    for cid in sorted(old_counts):
        was, now = old_counts[cid], now_counts.get(cid, 0)
        if now < was:
            it = doc.item(cid)
            ln = (it.head_line + 1) if it else 0
            out.append(Finding('12.32', WARNING, c.rel(doc.path), ln,
                               '%s had %d acceptance bullets at %s, has %d now, and '
                               'the document version was not bumped (still %s)'
                               % (cid, was, tag, now, doc.header.get('version'))))
    return out


# ---------------------------------------------------------------- 12.35
@rule('12.35', 'Generated carries everything client says')
def r_12_35(c):
    req_path = os.path.join(c.root, 'generated', 'REQUIREMENTS.md')
    if not os.path.exists(req_path):
        return [Finding('12.35', ERROR, 'generated/REQUIREMENTS.md', 0,
                        'does not exist — every id named in client/*.md must appear '
                        'here once it is generated; right now none of them can be')]
    try:
        req_text = io.open(req_path, encoding='utf-8').read()
    except IOError:
        return []
    out = []
    for key in c.client_keys():
        doc = c.docs[key]
        for it in doc.items:
            if not it.id:
                continue
            if not re.search(r'(?<![\w-])' + re.escape(it.id) + r'(?![\w-])', req_text):
                out.append(Finding('12.35', ERROR, c.rel(doc.path), (it.head_line or 0) + 1,
                                   '%s: named here, absent from generated/REQUIREMENTS.md'
                                   % it.id))
    return out
