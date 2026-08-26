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

TWO SHAPES, NOT ONE. An earlier draft of this module read the anchored shape and
only that, which is the shape `migrate.py` leaves behind. But the contract's own
`heading` for a log entry is `## [<YYYY-MM-DD>] <kind> | <title>` and every
example in `skills/journal/SKILL.md` — the skill that tells an author how to
write one — is unanchored. A log written the way the plugin documents was
therefore invisible: a `work` entry with a nonsense kind went unreported, and,
worse, a CORRECT document was reported broken (12.20 announced an unrecorded
handoff file, 12.26 a done task with no `work` entry, both of which the log named
in plain sight). So `_entities` recognises an entity by its anchor OR by a heading
whose leading token matches that entity's `id_space` pattern from the contract —
never by guessing at a shape neither of those two declares.

BODIES END. The same draft ended an entity's body only at the next anchor of the
same kind, so bullets belonging to a LATER entry silenced a required-field
finding on an EARLIER one: appending a `work` entry that happened to carry
`source:` dropped 12.13 from 19 findings to 18. A body now ends at the next
entity, at a `section=` anchor, and at any heading no deeper than the entity's
own — which is where a reader would end it too.

FIELD BLOCKS ARE ADDRESSED. `field_body` keeps each `<!-- macstack:<field> -->`
block's own lines, because "the milestone has a bullet somewhere" is not the
question 12.16 asks: an empty `done_when` beside a chatty `notes` passed, and a
`не выполнено` written in `notes` about something else failed a done milestone.

Rewiring note for whoever restructures `history/`: 12.13, 12.19, 12.20 and
12.26 all read `log.md`'s `entries` section directly; 12.14, 12.16 and 12.26
read `TASKS.md`'s `milestones`/`tasks` sections; 12.15 reads both `log.md` and
`CHANGELOG.md`'s `releases` section. Whatever replaces `log.md` with a machine
ledger needs equivalents of `_log_entries()` and of `_fields()`'s bold/plain/yaml
union — nothing here assumes markdown past that one call site per rule.
"""
import datetime, os, re

from lint_folder import rule, Finding, ERROR, WARNING
import mdblocks

# Only for the catalogue of journal headings, per language — the renderer owns
# that list, and a second copy of it here would be the thing rule 12.5 forbids.
try:
    import render as _render
except Exception:                                                 # noqa: BLE001
    _render = None

BOLD_FIELD = re.compile(r'^\s*[-*]\s+\*\*([A-Za-z][A-Za-z_]*):\*\*\s*(.*)$')
PLAIN_FIELD = re.compile(r'^\s*[-*]\s+([A-Za-z][A-Za-z_]*):\s*(.*)$')
BULLET = re.compile(r'^\s*[-*]\s+\S')
STRUCK = re.compile(r'^~~(.+?)~~\s*(.*)$')
DATE = re.compile(r'^\d{4}-\d{2}-\d{2}$')
ISO = re.compile(r'\d{4}-\d{2}-\d{2}')
# The contract's own heading for a log entry, and the one every example in the
# `journal` skill writes: `## [2026-08-24] work | M11 — split the export run`.
# The brackets are optional because the corpus has them off as often as on.
ENTRY_HEAD = re.compile(
    r'^#{2,6}\s+\[?(\d{4}-\d{2}-\d{2})\]?\s+([A-Za-z][A-Za-z0-9_-]*)\s*[|·—–-]\s*\S')
ID_HEAD = re.compile(r'^#{2,6}\s+(\S+)')
JOURNAL_ITEM = re.compile(r'^\s*[-*]\s+\*\*(\d{4}-\d{2}-\d{2})\*\*\s*[—–-]?\s*(.*)$')
SEP = re.compile(r'^\s*[|·—–-]\s*')
DECOR = u'~*`'
# "не выполнено" is the literal marker the live corpus uses on M15's checks (see
# the lint brief); the English forms are the same idea for a document that never
# switches alphabets. Not exhaustive by design — a marker this rule does not
# know about is a marker it says nothing about, which is the honest failure mode.
UNMET = re.compile(r'не\s+выполнен\w*|\bnot\s+met\b|\bnot\s+fulfilled\b|\bunmet\b|[✗❌]', re.I)


# ---------------------------------------------------------------- shared reading
def _head_entity(raw, id_pattern, dated_head):
    """(id, {extra fields}) when this heading STARTS an entity, else None.

    Recognition is by the contract, never by shape alone: a dated head must carry
    an ISO date and a kind, and an id head's leading token must match the
    `id_spaces` pattern of the entity being looked for. `## Вехи` is not a
    milestone because `Вехи` does not match `^M[0-9]+$`, and that is the only
    reason it is not — no heading is excluded by a list of words.
    """
    if dated_head:
        m = ENTRY_HEAD.match(raw)
        return (m.group(2), {'date': m.group(1)}) if m else None
    if not id_pattern:
        return None
    m = ID_HEAD.match(raw)
    if not m:
        return None
    tok = m.group(1).strip(DECOR)
    return (tok, {}) if re.match(id_pattern, tok) else None


def _entities(text, anchor_kind, section=None, id_pattern=None, dated_head=False,
              siblings=()):
    """Every entity of one kind in `text`, in order, with a line on every piece.

    Each item: `id` (the anchor's ident or the heading's leading token, unstruck),
    `heading` (raw heading text, struck marker and all), `yaml` (the one fenced
    block, if any), `body` ([(1-indexed line, raw line), ...]), `field_body`
    ({`<!-- macstack:<field> -->` name: its own [(line, raw)]}), `blocks` (those
    field names in order), `line` (the heading's 1-indexed line, 0 when the entity
    carried no heading), `level`, `struck` and `why` (whether a struck heading
    names a reason after an em dash, per `TASKS.md`'s `struck_form`).

    `section` restricts to entities whose nearest enclosing `section=` anchor has
    that id — `log.md` anchors its own section titles as stray `entry` entities,
    and without this a `howto` heading would be graded as a malformed journal
    entry. A document carrying no `section=` anchor at all is not filtered: the
    anchors are a migration artefact, and demanding one would make every rule
    here silent on a hand-written file, which is the failure this module exists
    to stop being.
    """
    lines = text.splitlines()
    sectioned = any(mdblocks.ANCHOR.match(l) and mdblocks.ANCHOR.match(l).group(1) == 'section'
                    for l in lines)
    if not sectioned:
        section = None
    out, cur_section, cur, field = [], None, None, None
    in_fence, fence_lines, fence_lang = False, [], None

    def keep(pairs):
        cur['body'].extend(pairs)
        if field is not None:
            cur['field_body'].setdefault(field, []).extend(pairs)

    def begin(ident, lineno, heading, level, extra=None):
        if section is not None and cur_section != section:
            return None
        e = {'id': ident, 'heading': heading, 'level': level, 'yaml': {}, 'body': [],
             'field_body': {}, 'blocks': [], 'line': lineno, 'extra': extra or {}}
        out.append(e)
        return e

    for i, raw in enumerate(lines):
        n = i + 1
        fm = mdblocks.FENCE.match(raw)
        if in_fence:
            if fm and fm.group(1) is None:
                if fence_lang == 'yaml' and cur is not None and not cur['yaml']:
                    cur['yaml'] = mdblocks.parse_yaml('\n'.join(t for _, t in fence_lines))
                elif cur is not None:
                    keep(fence_lines)
                in_fence = False
            else:
                fence_lines.append((n, raw))
            continue
        if fm:
            in_fence, fence_lines, fence_lang = True, [], fm.group(1)
            continue
        am = mdblocks.ANCHOR.match(raw)
        if am:
            kind, ident = am.group(1), am.group(2)
            if kind == 'section':
                cur_section, cur, field = ident, None, None
            elif kind == anchor_kind:
                cur, field = begin(ident, None, None, None), None
            elif kind in siblings:
                cur, field = None, None          # a neighbouring entity starts here
            elif cur is not None:
                field = kind                     # a field block inside this entity
                cur['blocks'].append(kind)
                cur['field_body'].setdefault(kind, [])
            continue
        hm = mdblocks.HEADING.match(raw)
        if hm:
            level, title = len(hm.group(1)), hm.group(2)
            if cur is not None and cur['line'] is None:
                cur['heading'], cur['line'], cur['level'] = title, n, level
                continue
            new = _head_entity(raw, id_pattern, dated_head)
            if new is not None:
                cur, field = begin(new[0], n, title, level, new[1]), None
            elif cur is not None and cur['level'] is not None and level <= cur['level']:
                cur, field = None, None          # an unrelated heading ends the entity
            continue
        if cur is not None and raw.strip():
            keep([(n, raw)])
    if in_fence and cur is not None:              # unterminated fence — don't lose the tail
        if fence_lang == 'yaml' and not cur['yaml']:
            cur['yaml'] = mdblocks.parse_yaml('\n'.join(t for _, t in fence_lines))
        else:
            keep(fence_lines)
    for e in out:
        if e['line'] is None:
            e['line'] = 0
        m = STRUCK.match((e['heading'] or '').strip())
        e['struck'] = bool(m)
        e['why'] = bool(m and '—' in (m.group(2) or ''))
    return out


def _fields(e):
    """{lowercase key: value} — the yaml block first (how `TASKS.md` stores
    `status`/`tracker`), then anything the heading itself declared (an unanchored
    log entry carries its date there and nowhere else), then any bold
    (`- **key:** …`) or plain (`- key: …`) bullet of the same shape (how
    `log.md`'s `handoff`/`work`/`release` fields are written per the `journal`
    skill's own examples) — whichever the entity actually used, a rule asking
    "does it have `key`" gets one answer."""
    out = {}
    for k, v in (e.get('yaml') or {}).items():
        out[str(k).lower()] = v
    for k, v in (e.get('extra') or {}).items():
        out.setdefault(str(k).lower(), v)
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


def _id_pattern(c, decl):
    """The `id_spaces` pattern this entity's ids live in, or None.

    Read off the entity's own `id_space` rather than hard-coded, so a renamed or
    re-patterned space moves both the writer and this reader at once."""
    space = (decl or {}).get('id_space')
    return ((c.contract.get('id_spaces') or {}).get(space) or {}).get('pattern')


def _relpath(c, key, fallback):
    p = c.path_of(key)
    return c.rel(p) if p else fallback


def _log_entries(c):
    """Every `log.md` journal entry, anchored or written the documented way."""
    text = c.text.get('log')
    if text is None:
        return []
    return _entities(text, 'entry', section='entries', dated_head=True)


# ---------------------------------------------------------------- 12.13
@rule('12.13', 'The journal is typed')
def r_12_13(c):
    text = c.text.get('log')
    decl = _entity_decl(c, 'log', 'log_entry')
    if text is None or decl is None:
        return []
    required = decl.get('bullets_required_when') or {}
    blocks_when = decl.get('sections_required_when') or {}
    kinds = set(required) | set(blocks_when)
    if not kinds:
        return []                          # contract dropped the table — nothing to check against
    p = _relpath(c, 'log', 'history/log.md')
    out = []
    for e in _log_entries(c):
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
        # A required prose block counts as carried whether it was written as an
        # anchored block or as a bullet of the same name: the contract asks for
        # `what` and `notes` on a `work` entry, and the `journal` skill's own
        # example writes both as bullets.
        for blk in blocks_when.get(kind) or []:
            if blk in e['blocks'] or blk in have:
                continue
            near = [b for b in e['blocks'] if b.rstrip('s') == blk.rstrip('s')]
            out.append(Finding('12.13', ERROR, p, e['line'],
                               '%s entry carries no %r block — required by '
                               'documents.log.entities[0].sections_required_when.%s%s'
                               % (kind, blk, kind,
                                  ('; it carries %r, so one of the two spellings is a typo'
                                   % near[0]) if near else '')))
    return out


# ---------------------------------------------------------------- 12.14
@rule('12.14', 'Every task is tracked in both places')
def r_12_14(c):
    text = c.text.get('tasks')
    decl = _entity_decl(c, 'tasks', 'task')
    if text is None:
        return []
    p = _relpath(c, 'tasks', 'history/TASKS.md')
    statuses = set(((c.contract.get('documents') or {}).get('tasks') or {}).get('statuses') or {})
    out = []
    for e in _entities(text, 'task', section='tasks', id_pattern=_id_pattern(c, decl),
                       siblings=('milestone', 'backlog')):
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

    log_releases = [(_as_text(_fields(e).get('release')), e['line'])
                    for e in _log_entries(c) if e['id'] == 'release']

    chg_releases = []
    if chg_text is not None:
        decl = _entity_decl(c, 'changelog', 'release')
        for e in _entities(chg_text, 'release', section='releases',
                           id_pattern=_id_pattern(c, decl)):
            chg_releases.append((e['id'], e['line'], _as_text(_fields(e).get('date'))))

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
        if not (isinstance(date, str) and DATE.match(date)):
            # Silence here would let a document reorder itself simply by dropping
            # a date, which is the one thing the ordering clause cannot survive.
            out.append(Finding('12.15', ERROR, chg_p, ln,
                               'release %s declares no date — newest-first cannot be checked' % rid))
            continue
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
    decl = _entity_decl(c, 'tasks', 'milestone')
    if text is None:
        return []
    p = _relpath(c, 'tasks', 'history/TASKS.md')
    want = ((decl or {}).get('prose_required') or ['done_when'])[0]
    out = []
    for e in _entities(text, 'milestone', section='milestones',
                       id_pattern=_id_pattern(c, decl), siblings=('task', 'backlog')):
        block = e['field_body'].get(want)
        # No block at all: the milestone may be written without anchors, so every
        # bullet it carries is a candidate check. With a block, only its own lines
        # count — an empty `done_when` beside a chatty `notes` is still empty.
        source = e['body'] if block is None else block
        checks = [(ln, raw) for ln, raw in source if BULLET.match(raw)]
        if not checks:
            out.append(Finding('12.16', ERROR, p, e['line'],
                               '%s declares no %s checks%s'
                               % (e['id'], want,
                                  ' — the block is there and empty' if block is not None else '')))
            continue
        if _as_text(_fields(e).get('status')) == 'done':
            for ln, raw in checks:
                if UNMET.search(raw):
                    out.append(Finding('12.16', ERROR, p, ln,
                                       '%s is status: done but a check is recorded unmet: %s'
                                       % (e['id'], raw.strip()[:120])))
    return out


# ---------------------------------------------------------------- 12.19
def _journal_heads():
    """Every spelling of the journal heading the renderer knows, lowercased."""
    heads = set()
    for table in ((getattr(_render, 'HEAD', None) or {}).values()):
        j = (table or {}).get('journal')
        if j:
            heads.add(j.strip().lower())
    return heads or {u'журнал документа',
                     'document journal'}


def _journal(text, columns):
    """(1-indexed line of the journal heading or None, [(line, date, what)]).

    Rows come in two shapes and both are live: a table (`TASKS.md`,
    `CHANGELOG.md`, `DECISIONS.md`, `TEST-CASES.md`) and the list the renderer
    now writes (`README.md`, `INDEX.md`, `ARCHITECTURE.md`). The date column is
    located through the contract's `journal_columns` rather than assumed first —
    `TEST-CASES.md` puts `version` there, and a reader that assumes would call
    its journal empty.
    """
    heads = _journal_heads()
    lines = text.split('\n')
    start = None
    for i, l in enumerate(lines):
        am = mdblocks.ANCHOR.match(l)
        if am and am.group(1) == 'section' and am.group(2) == 'journal':
            start = i
        elif l.startswith('## ') and l[3:].strip().lower() in heads:
            start = i
    if start is None:
        return None, []
    cols = [str(x).strip().lower() for x in (columns or [])]
    di = cols.index('date') if 'date' in cols else 0
    wi = cols.index('what changed') if 'what changed' in cols else -1
    rows = []
    for j in range(start + 1, len(lines)):
        l = lines[j]
        am = mdblocks.ANCHOR.match(l)
        if (am and am.group(1) == 'section') or l.startswith('## '):
            break
        m = JOURNAL_ITEM.match(l)
        if m:
            rows.append((j + 1, m.group(1), m.group(2).strip()))
            continue
        if l.strip().startswith('|') and not re.match(r'^\s*\|[\s:|-]+\|\s*$', l):
            cells = [x.strip() for x in l.strip().strip('|').split('|')]
            date = cells[di] if di < len(cells) and DATE.match(cells[di]) else None
            if date is None:
                date = next((x for x in cells if DATE.match(x)), None)
            if date is None:
                continue                       # a header row, or a row with no date
            what = cells[wi] if -len(cells) <= wi < len(cells) else ''
            rows.append((j + 1, date, what))
    return start + 1, rows


@rule('12.19', 'The journal is not empty', WARNING)
def r_12_19(c):
    """Two halves, both of them the rule's own words.

    SKILL.md: "a document whose contract declares a `journal` section has at
    least one row in it, and no row is dated later than the document's
    `updated`." That half had never been written as code, so nothing checked the
    seven documents that declare one. The `log.md` half below is the same
    sentence read against the document that IS a journal: an entries section with
    nothing in it, or nothing in it lately, says the same thing about the project.
    """
    out = []
    text = c.text.get('log')
    if text is not None:
        p = _relpath(c, 'log', 'history/log.md')
        ents = _log_entries(c)
        if not ents:
            out.append(Finding('12.19', WARNING, p, 0, 'history/log.md records no entry'))
        else:
            dates = sorted(d for d in (_as_text(_fields(e).get('date')) for e in ents)
                           if isinstance(d, str) and DATE.match(d))
            freshness = (c.spec.get('docs') or {}).get('freshness_days', 30)
            if dates:
                try:
                    y, m, d = (int(x) for x in dates[-1].split('-'))
                    age = (datetime.date.today() - datetime.date(y, m, d)).days
                except ValueError:
                    age = 0
                if age > freshness:
                    out.append(Finding('12.19', WARNING, p, 0,
                                       'newest entry is %s, %d days old — past the %d-day '
                                       'freshness budget' % (dates[-1], age, freshness)))

    for key in sorted(c.contract.get('documents') or {}):
        decl = (c.contract.get('documents') or {})[key]
        if 'journal' not in (decl.get('sections') or []):
            continue
        txt = c.text.get(key)
        path = c.path_of(key)
        if txt is None or not path:
            continue                       # templated path or absent file — 12.1 owns that
        p = c.rel(path)
        start, rows = _journal(txt, decl.get('journal_columns'))
        if start is None:
            out.append(Finding('12.19', WARNING, p, 0,
                               'the contract declares a journal section for this document '
                               'and it carries none'))
            continue
        if not rows:
            out.append(Finding('12.19', WARNING, p, start,
                               'the journal section carries no row — an edit nobody recorded '
                               'reaches the next reader as if it had always said this'))
            continue
        updated = _as_text((c.files.get(key) or {}).get('updated')) or ''
        if DATE.match(updated):
            for ln, d, what in rows:
                if d > updated:
                    out.append(Finding('12.19', WARNING, p, ln,
                                       'journal row dated %s is later than docs.files.%s.updated '
                                       '(%s): %s' % (d, key, updated, (what or '')[:60])))
    return out


# ---------------------------------------------------------------- 12.20
@rule('12.20', 'Every handoff is recorded')
def r_12_20(c):
    log_p = _relpath(c, 'log', 'history/log.md')
    handoffs_dir = os.path.join(c.root, 'history', 'handoffs')
    on_disk = set()
    if os.path.isdir(handoffs_dir):
        on_disk = {f for f in os.listdir(handoffs_dir) if not f.startswith('.')}

    named = {}
    out = []
    for e in _log_entries(c):
        if e['id'] != 'handoff':
            continue
        f = _as_text(_fields(e).get('file'))
        if not f:
            out.append(Finding('12.20', ERROR, log_p, e['line'], 'handoff entry names no file'))
            continue
        named.setdefault(os.path.basename(f.strip('` ')), e['line'])

    for base, ln in sorted(named.items()):
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
    decl = _entity_decl(c, 'tasks', 'task')
    if tasks_text is None:
        return []
    p = _relpath(c, 'tasks', 'history/TASKS.md')
    done = [(e['id'], e['line'])
            for e in _entities(tasks_text, 'task', section='tasks',
                               id_pattern=_id_pattern(c, decl),
                               siblings=('milestone', 'backlog'))
            if _as_text(_fields(e).get('status')) == 'done']
    if not done:
        return []

    named = set()
    for e in _log_entries(c):
        if e['id'] == 'work':
            named.update(_as_list(_fields(e).get('tasks')))

    return [Finding('12.26', ERROR, p, ln,
                    '%s is done but no `work` entry in log.md names it' % tid)
            for tid, ln in done if tid not in named]
