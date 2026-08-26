# -*- coding: utf-8 -*-
"""Rule group 12, `history/` half — the journal, the task list, the releases.

None of the three documents here are `format: v3` (see `doc-contracts.json`):
`log.md`, `TASKS.md` and `CHANGELOG.md` are still the anchored-yaml shape
`mdblocks` reads, and `Ctx` only puts a `v3.Doc` in `c.docs` for a `v3` contract
entry — these three live in `c.text` as raw strings instead.

`mdblocks.parse()` gets the nesting, the section grouping and the one fenced
`yaml` block right, but it tracks a line number for an anchor's OWN line and for
nothing else — no heading line, nothing inside a body. Every rule below needs a
line to report, so `_entities()` re-walks the same anchor/heading/fence grammar
(`mdblocks.ANCHOR`, `.HEADING`, `.FENCE`, `.parse_yaml` — the same primitives,
not a second guess at them) keeping a line number on every piece it keeps. This
is the local workaround the brief for this module allows: `lint_folder.py` and
`mdblocks.py` are not mine to change, and the gap was real.

Known corpus quirk worth naming once, here: `migrate.py`'s v1->v2 converter
anchors *any* `## <word> · <rest>`-shaped heading in `log.md` as an `entry`,
`id_re=r'\\w+'` — which also matches a SECTION's own heading (`## Как · читать
этот документ`, `## Записи · Записи`). `_entities()` still finds these when
asked for `entry` inside the `entries` section (the `howto` ones are outside it
and never appear), and 12.13 rightly reports the one that lands there: a
migrated-over section title is not a journal entry, and a rule that only checks
things that already look like entries would never say so.

Rewiring note for whoever restructures `history/`: 12.13, 12.19, 12.20 and
12.26 all read `log.md`'s `entries` section directly; 12.14, 12.16 and 12.26
read `TASKS.md`'s `milestones`/`tasks` sections; 12.15 reads both `log.md` and
`CHANGELOG.md`'s `releases` section. Whatever replaces `log.md` with a machine
ledger needs equivalents of `_entities(text, 'entry', section='entries')` and
of `_fields()`'s bold/plain/yaml union — nothing here assumes markdown past
that one call site per rule.
"""
import datetime, os, re

from lint_folder import rule, Finding, ERROR, WARNING
import mdblocks

BOLD_FIELD = re.compile(r'^\s*[-*]\s+\*\*([A-Za-z][A-Za-z_]*):\*\*\s*(.*)$')
PLAIN_FIELD = re.compile(r'^\s*[-*]\s+([A-Za-z][A-Za-z_]*):\s*(.*)$')
BULLET = re.compile(r'^\s*[-*]\s+\S')
STRUCK = re.compile(r'^~~(.+?)~~\s*(.*)$')
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
# "не выполнено" is the literal marker the live corpus uses on M15's checks (see
# the lint brief); the English forms are the same idea for a document that never
# switches alphabets. Not exhaustive by design — a marker this rule does not
# know about is a marker it says nothing about, which is the honest failure mode.
UNMET = re.compile(r'не\s+выполнен\w*|\bnot\s+met\b|\bnot\s+fulfilled\b|\bunmet\b|[✗❌]', re.I)


# ---------------------------------------------------------------- shared reading
def _entities(text, anchor_kind, section=None):
    """Every `<!-- macstack:<anchor_kind>=<id> -->` entity in `text`, in order.

    Each item: `id` (the anchor's own ident, unstruck — cross-references use
    this), `heading` (raw heading text, struck marker and all), `yaml` (the one
    fenced block, if any), `body` ([(1-indexed line, raw line), ...] — every
    child anchor's content folded in, since a rule here only ever needs "does
    this entity carry field X", never which of its named sub-blocks holds it),
    `line` (the heading's 1-indexed line, 0 if the anchor carried no heading),
    `struck` and `why` (whether a struck heading names a reason after an em
    dash, per `TASKS.md`'s `struck_form`).

    `section`, given, restricts to entities whose nearest enclosing `section=`
    anchor has that id — `log.md` anchors its section titles themselves as
    stray `entry` entities (see the module docstring), and without this an
    unrelated `howto` heading would be graded as a malformed journal entry.
    """
    lines = text.splitlines()
    out = []
    cur_section = None
    cur = None
    in_fence = False
    fence_lines = None
    fence_lang = None
    for i, raw in enumerate(lines):
        fm = mdblocks.FENCE.match(raw)
        if in_fence:
            if fm and fm.group(1) is None:
                if fence_lang == 'yaml' and cur is not None and not cur['yaml']:
                    cur['yaml'] = mdblocks.parse_yaml('\n'.join(t for _, t in fence_lines))
                elif cur is not None:
                    cur['body'].extend(fence_lines)
                in_fence = False
            else:
                fence_lines.append((i + 1, raw))
            continue
        if fm:
            in_fence, fence_lines, fence_lang = True, [], fm.group(1)
            continue
        am = mdblocks.ANCHOR.match(raw)
        if am:
            kind, ident = am.group(1), am.group(2)
            if kind == 'section':
                cur_section = ident
                cur = None
            elif kind == anchor_kind and (section is None or cur_section == section):
                cur = {'id': ident, 'heading': None, 'yaml': {}, 'body': [], 'line': None}
                out.append(cur)
            # any other anchor (`notes`, `done_when`, ...) is a field inside
            # whatever `cur` already is — it does not start a new entity
            continue
        hm = mdblocks.HEADING.match(raw)
        if hm and cur is not None and cur['line'] is None:
            cur['heading'] = hm.group(2)
            cur['line'] = i + 1
            continue
        if cur is not None and raw.strip():
            cur['body'].append((i + 1, raw))
    if in_fence and cur is not None:              # unterminated fence — don't lose the tail
        if fence_lang == 'yaml' and not cur['yaml']:
            cur['yaml'] = mdblocks.parse_yaml('\n'.join(t for _, t in fence_lines))
        else:
            cur['body'].extend(fence_lines)
    for e in out:
        if e['line'] is None:
            e['line'] = 0
        m = STRUCK.match((e['heading'] or '').strip())
        e['struck'] = bool(m)
        e['why'] = bool(m and '—' in (m.group(2) or ''))
    return out


def _fields(e):
    """{lowercase key: value} — the yaml block first (how `TASKS.md` stores
    `status`/`tracker`), then any bold (`- **key:** …`) or plain (`- key: …`)
    bullet of the same shape (how `log.md`'s `handoff`/`work`/`release` fields
    are written per the `journal` skill's own examples) — whichever the entity
    actually used, a rule asking "does it have `key`" gets one answer."""
    out = {}
    for k, v in (e.get('yaml') or {}).items():
        out[str(k).lower()] = v
    for _, raw in e.get('body') or []:
        m = BOLD_FIELD.match(raw) or PLAIN_FIELD.match(raw)
        if m:
            out.setdefault(m.group(1).lower(), m.group(2).strip())
    return out


def _as_list(v):
    """A field's value as flat string tokens, whichever shape it was written in:
    a plain bullet (`- tasks: M11-T42, M11-T43`, a comma/space string) or a YAML
    `tasks: [M11-T42, M11-T43]` inside the fence — `parse_yaml` already turns the
    second into a real list, so treating both alike here is what keeps a caller
    from having to know which one a given entry happened to use."""
    if v is None:
        return []
    if isinstance(v, (list, tuple)):
        return [str(x).strip('` ') for x in v if str(x).strip('` ')]
    return [t.strip('` ') for t in re.split(r'[,\s]+', str(v)) if t.strip('` ')]


def _as_text(v):
    """A field's value as one string — guards a `.strip()`/regex call against a
    value that came back as a YAML list or number instead of the plain scalar
    the field is documented to be."""
    if v is None:
        return None
    if isinstance(v, (list, tuple)):
        return str(v[0]) if v else None
    return str(v)


def _entity_decl(c, doc_key, kind):
    for e in ((c.contract.get('documents') or {}).get(doc_key) or {}).get('entities') or []:
        if e.get('kind') == kind:
            return e
    return None


def _relpath(c, key, fallback):
    p = c.path_of(key)
    return c.rel(p) if p else fallback


# ---------------------------------------------------------------- 12.13
@rule('12.13', 'The journal is typed')
def r_12_13(c):
    text = c.text.get('log')
    decl = _entity_decl(c, 'log', 'log_entry')
    if text is None or decl is None:
        return []
    required = decl.get('bullets_required_when') or {}
    kinds = set(required)
    if not kinds:
        return []                          # contract dropped the table — nothing to check against
    p = _relpath(c, 'log', 'history/log.md')
    out = []
    for e in _entities(text, 'entry', section='entries'):
        kind = e['id']
        if kind not in kinds:
            out.append(Finding('12.13', ERROR, p, e['line'],
                               'entry declares kind %r, not one of %s'
                               % (kind, ', '.join(sorted(kinds)))))
            continue
        have = _fields(e)
        for key in required.get(kind) or []:
            if key not in have:
                out.append(Finding('12.13', ERROR, p, e['line'],
                                   '%s entry carries no %r — required by '
                                   'documents.log.entities[0].bullets_required_when.%s'
                                   % (kind, key, kind)))
    return out


# ---------------------------------------------------------------- 12.14
@rule('12.14', 'Every task is tracked in both places')
def r_12_14(c):
    text = c.text.get('tasks')
    if text is None:
        return []
    p = _relpath(c, 'tasks', 'history/TASKS.md')
    statuses = set(((c.contract.get('documents') or {}).get('tasks') or {}).get('statuses') or {})
    out = []
    for e in _entities(text, 'task', section='tasks'):
        fields = _fields(e)
        if not fields.get('tracker'):
            out.append(Finding('12.14', ERROR, p, e['line'],
                               '%s declares no tracker id' % e['id']))
        status = fields.get('status')
        if not status:
            out.append(Finding('12.14', ERROR, p, e['line'],
                               '%s declares no status' % e['id']))
        elif statuses and status not in statuses:
            out.append(Finding('12.14', ERROR, p, e['line'],
                               '%s status %r is not one of %s'
                               % (e['id'], status, ', '.join(sorted(statuses)))))
        if e['struck'] and not e['why']:
            out.append(Finding('12.14', ERROR, p, e['line'],
                               '%s is struck but its heading states no reason after an '
                               'em dash — struck_form: %s'
                               % (e['id'], (c.contract.get('documents') or {})
                                  .get('tasks', {}).get('struck_form', ''))))
    return out


# ---------------------------------------------------------------- 12.15
@rule('12.15', 'A release is paired')
def r_12_15(c):
    log_text = c.text.get('log')
    chg_text = c.text.get('changelog')
    if log_text is None and chg_text is None:
        return []
    log_p = _relpath(c, 'log', 'history/log.md')
    chg_p = _relpath(c, 'changelog', 'history/CHANGELOG.md')
    out = []

    log_releases = []
    if log_text is not None:
        for e in _entities(log_text, 'entry', section='entries'):
            if e['id'] == 'release':
                log_releases.append((_as_text(_fields(e).get('release')), e['line']))

    chg_releases = []
    if chg_text is not None:
        for e in _entities(chg_text, 'release', section='releases'):
            chg_releases.append((e['id'], e['line'], _fields(e).get('date')))

    chg_ids = {rid for rid, _, _ in chg_releases}
    log_ids = {rid for rid, _ in log_releases if rid}

    for rid, ln in log_releases:
        if not rid:
            out.append(Finding('12.15', ERROR, log_p, ln, 'release entry names no release id'))
        elif rid not in chg_ids:
            out.append(Finding('12.15', ERROR, log_p, ln,
                               'release %s has no CHANGELOG.md entry of the same id' % rid))
    for rid, ln, _ in chg_releases:
        if rid not in log_ids:
            out.append(Finding('12.15', ERROR, chg_p, ln,
                               'CHANGELOG.md entry %s has no `release` entry in log.md' % rid))

    prev = None
    for rid, ln, date in chg_releases:                 # file order, not sorted — that IS the check
        if isinstance(date, str) and DATE.match(date):
            if prev and date > prev[1]:
                out.append(Finding('12.15', ERROR, chg_p, ln,
                                   'CHANGELOG.md is not newest-first: %s (%s) sits after %s (%s)'
                                   % (rid, date, prev[0], prev[1])))
            prev = (rid, date)
    return out


# ---------------------------------------------------------------- 12.16
@rule('12.16', 'Milestones are falsifiable')
def r_12_16(c):
    text = c.text.get('tasks')
    if text is None:
        return []
    p = _relpath(c, 'tasks', 'history/TASKS.md')
    out = []
    for e in _entities(text, 'milestone', section='milestones'):
        checks = [(ln, raw) for ln, raw in e['body'] if BULLET.match(raw)]
        if not checks:
            out.append(Finding('12.16', ERROR, p, e['line'],
                               '%s declares no done_when checks' % e['id']))
            continue
        if (e['yaml'] or {}).get('status') == 'done':
            for ln, raw in checks:
                if UNMET.search(raw):
                    out.append(Finding('12.16', ERROR, p, ln,
                                       '%s is status: done but a check is recorded unmet: %s'
                                       % (e['id'], raw.strip()[:120])))
    return out


# ---------------------------------------------------------------- 12.19
@rule('12.19', 'The journal is not empty', WARNING)
def r_12_19(c):
    text = c.text.get('log')
    if text is None:
        return []
    p = _relpath(c, 'log', 'history/log.md')
    ents = _entities(text, 'entry', section='entries')
    if not ents:
        return [Finding('12.19', WARNING, p, 0, 'history/log.md has no entries')]
    dates = sorted(d for d in (_fields(e).get('date') for e in ents)
                   if isinstance(d, str) and DATE.match(d))
    if not dates:
        return []                          # no dated entry — nothing to measure freshness from
    newest = dates[-1]
    freshness = (c.spec.get('docs') or {}).get('freshness_days', 30)
    try:
        y, m, d = (int(x) for x in newest.split('-'))
        age = (datetime.date.today() - datetime.date(y, m, d)).days
    except ValueError:
        return []
    if age > freshness:
        return [Finding('12.19', WARNING, p, 0,
                        'newest entry is %s, %d days old — past the %d-day freshness budget'
                        % (newest, age, freshness))]
    return []


# ---------------------------------------------------------------- 12.20
@rule('12.20', 'Every handoff is recorded')
def r_12_20(c):
    text = c.text.get('log')
    log_p = _relpath(c, 'log', 'history/log.md')
    handoffs_dir = os.path.join(c.root, 'history', 'handoffs')
    on_disk = set()
    if os.path.isdir(handoffs_dir):
        on_disk = {f for f in os.listdir(handoffs_dir) if not f.startswith('.')}

    named = {}
    out = []
    if text is not None:
        for e in _entities(text, 'entry', section='entries'):
            if e['id'] != 'handoff':
                continue
            f = _as_text(_fields(e).get('file'))
            if not f:
                out.append(Finding('12.20', ERROR, log_p, e['line'], 'handoff entry names no file'))
                continue
            named.setdefault(os.path.basename(f.strip('`')), e['line'])

    for base, ln in named.items():
        if base not in on_disk:
            out.append(Finding('12.20', ERROR, log_p, ln,
                               'handoff entry names %s — not in history/handoffs/' % base))
    for base in sorted(on_disk - set(named)):
        out.append(Finding('12.20', ERROR, os.path.join('history', 'handoffs', base), 0,
                           'exists in history/handoffs/ but no handoff entry in log.md names it'))
    return out


# ---------------------------------------------------------------- 12.26
@rule('12.26', 'A finished task left a trace')
def r_12_26(c):
    tasks_text = c.text.get('tasks')
    if tasks_text is None:
        return []
    p = _relpath(c, 'tasks', 'history/TASKS.md')
    done = [(e['id'], e['line']) for e in _entities(tasks_text, 'task', section='tasks')
            if _fields(e).get('status') == 'done']
    if not done:
        return []

    named = set()
    log_text = c.text.get('log')
    if log_text is not None:
        for e in _entities(log_text, 'entry', section='entries'):
            if e['id'] != 'work':
                continue
            named.update(_as_list(_fields(e).get('tasks')))

    return [Finding('12.26', ERROR, p, ln,
                    '%s is done but no `work` entry in log.md names it' % tid)
            for tid, ln in done if tid not in named]
