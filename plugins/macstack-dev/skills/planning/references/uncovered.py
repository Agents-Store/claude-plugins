#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Which client requirements have no plan yet — and which already passed a check.

Sits between `client/USER-CASES.md` (what the client agreed must be true) and
`history/TASKS.md` (what will be done about it). Answers three questions a person cannot
answer by reading either file alone:

  1. Which cases nobody scheduled AND no audit has confirmed — the real work list.
  2. Which cases an audit already found implemented — planning those wastes everyone's time.
  3. Which cases are blocked, because an open question they depend on is still open.
  4. Which tasks point at a case that no longer exists — a plan for a requirement withdrawn.

The third input is the newest `history/reviews/*-conformance.md`. Without it the report says
"N cases with no plan" on a project where nearly all of them are built, which is true and
useless: a work list nobody believes is a work list nobody reads.

v2 change: documents are entity+yaml blocks, not table columns. Parsing goes through
`mdblocks` (the shared v2 parser) instead of a private regex grid. A case's `spec` pointer
is now a yaml field on a task entity, not a list-item string; a review's verdict is a yaml
`verdict` enum on a `finding` entity, closed to `implemented | partial | absent |
externally-blocked`. Old table-shaped conformance files (verdict as free text in a column)
are still read as a FALLBACK — the yaml reading takes priority where both exist for the
same case id.

WHAT IT DOES NOT DO: decide which files a task touches or what proves it done. That is
judgement over the codebase, and a machine that guesses it produces a plan nobody can
trust. It emits the SKELETON — id, name, the pointer back to the case — and the agent or
the human fills `files` and `acceptance` by reading the code.

Usage: uncovered.py <macstack-dir> [--emit]   (--emit prints ready v2 task skeletons)
"""
import sys, os, io, re

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'documents', 'references')))
from mdblocks import parse, entities, dump_yaml  # noqa: E402
from i18n import doc_lang, msg  # noqa: E402

CASE_ID = re.compile(r'\b([A-Z]-\d{2})\b')
OPEN_ID = re.compile(r'\b([AB]\d+)\b')
# Fallback for the v1 table format: | C-01 | Implemented | evidence... |
LEGACY_ROW = re.compile(r'^\|\s*\*?\*?([A-Z]-\d+)\*?\*?\s*\|\s*([^|]+?)\s*\|', re.M)
DONE_SYNONYMS = ('implemented', 'выполнено', 'реализовано', 'passes', 'ok')
PRIORITY_ORDER = ('critical', 'important', 'nice-to-have')


def read(path):
    with io.open(path, encoding='utf-8') as f:
        return f.read()


def title_of(block):
    """'<id> · Title' -> 'Title'. Struck headings ('~~id~~ · DROPPED ...') survive too."""
    h = (block.heading or '').strip()
    if '·' in h:  # ·
        return h.split('·', 1)[1].strip()
    return h


def case_full_text(block):
    return '\n'.join(line for c in block.children for line in c.body)


def acceptance_count(block):
    acc = block.field('acceptance')
    if acc is None:
        return 0
    return sum(1 for line in acc.body if line.strip().startswith('- '))


def live_open_ids(oq_path):
    """Open-item ids from OPEN-QUESTIONS.md that are not struck (closed/promoted)."""
    if not os.path.exists(oq_path):
        return set()
    _, blocks = parse(read(oq_path))
    out = set()
    for b in entities(blocks, 'open'):
        h = (b.heading or '').strip()
        if not h.startswith('~~'):
            out.add(b.id)
    return out


def read_verdicts(path):
    """-> (yaml_verdicts, legacy_verdicts), both {case_id: raw value/text}.

    yaml_verdicts comes from `finding` entities' yaml `verdict` field (closed enum).
    legacy_verdicts comes from the old table format and is only a fallback — the
    caller prefers yaml_verdicts for any id present in both.
    """
    raw = read(path)
    legacy = {}
    for m in LEGACY_ROW.finditer(raw):
        cid, text = m.group(1), m.group(2).strip()
        if cid not in legacy:
            legacy[cid] = text
    _, blocks = parse(raw)
    yml = {}
    for b in entities(blocks, 'finding'):
        v = b.yaml.get('verdict')
        if v:
            yml[b.id] = v
    return yml, legacy


def classify(cid, covered, yml, legacy):
    """-> (state, verdict_text) — state in ('planned', 'done', 'partial', 'todo')."""
    if cid in covered:
        return 'planned', None
    if cid in yml:
        v = yml[cid]
        if v == 'implemented':
            return 'done', v
        if v in ('partial', 'externally-blocked'):
            return 'partial', v
        return 'todo', v            # 'absent' — nobody built it; this IS the work
    if cid in legacy:
        v = legacy[cid]
        if any(d in v.lower() for d in DONE_SYNONYMS):
            return 'done', v
        return 'partial', v
    return 'todo', None


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    root = args[0] if args else 'macstack'
    emit = '--emit' in sys.argv
    lang = doc_lang(root)

    uc_p = os.path.join(root, 'client', 'USER-CASES.md')
    tk_p = os.path.join(root, 'history', 'TASKS.md')
    oq_p = os.path.join(root, 'client', 'OPEN-QUESTIONS.md')
    for p in (uc_p, tk_p):
        if not os.path.exists(p):
            print('missing: %s' % p)
            return 1

    _, uc_blocks = parse(read(uc_p))
    cases = entities(uc_blocks, 'case')

    _, tk_blocks = parse(read(tk_p))
    tasks = entities(tk_blocks, 'task')
    milestones = entities(tk_blocks, 'milestone')

    live_a = live_open_ids(oq_p)

    rdir = os.path.join(root, 'history', 'reviews')
    revs = sorted(f for f in os.listdir(rdir) if f.endswith('conformance.md')) if os.path.isdir(rdir) else []
    yml, legacy, rev_name = {}, {}, None
    if revs:
        rev_name = revs[-1]
        yml, legacy = read_verdicts(os.path.join(rdir, rev_name))

    covered = {}
    for t in tasks:
        spec = str(t.yaml.get('spec') or '')
        for cid in CASE_ID.findall(spec):
            covered.setdefault(cid, []).append((t.id, t.yaml.get('status')))

    known = {c.id for c in cases}
    orphan = []
    for t in tasks:
        spec = str(t.yaml.get('spec') or '')
        for cid in CASE_ID.findall(spec):
            if cid not in known:
                orphan.append((t.id, spec))

    blocked = {}
    for c in cases:
        hits = sorted({a for a in OPEN_ID.findall(case_full_text(c)) if a in live_a})
        if hits:
            blocked[c.id] = hits

    rows = [(c,) + classify(c.id, covered, yml, legacy) for c in cases]
    planned = [r for r in rows if r[1] == 'planned']
    done = [r for r in rows if r[1] == 'done']
    partial = [r for r in rows if r[1] == 'partial']
    unc = [r for r in rows if r[1] == 'todo']

    print(msg(lang, 'cases_total', n=len(cases)))
    print('  ' + msg(lang, 'cases_planned', n=len(planned)))
    print('  ' + msg(lang, 'cases_audited', n=len(done)) + (' (%s)' % rev_name if rev_name else ''))
    print('  ' + msg(lang, 'cases_partial', n=len(partial)))
    print('  ' + msg(lang, 'cases_open', n=len(unc)))

    if partial:
        print('\n=== audit found partial or blocked (%d) ===' % len(partial))
        for c, st, v in partial:
            print('    %-7s %-52s %s' % (c.id, title_of(c)[:52], (v or '')[:34]))

    print('\n=== not planned and not checked ===')
    by_pri = {}
    for c, st, v in unc:
        pri = c.yaml.get('priority') or '—'
        by_pri.setdefault(pri, []).append(c)
    order = list(PRIORITY_ORDER) + [p for p in by_pri if p not in PRIORITY_ORDER]
    for pri in order:
        if pri not in by_pri:
            continue
        group = by_pri[pri]
        print('\n  [%s] %d' % (pri, len(group)))
        for c in group:
            mark = '  ⏸ ' + ','.join(blocked[c.id]) if c.id in blocked else ''
            print('    %-7s %s%s' % (c.id, title_of(c)[:66], mark))
            print('        spec: client/USER-CASES.md %s — %d пункт(ов) приёмки' % (c.id, acceptance_count(c)))

    if orphan:
        print('\n=== tasks pointing at a missing case (%d) ===' % len(orphan))
        for tid, spec in orphan:
            print('    %-10s -> %s' % (tid, spec[:60]))

    if emit and unc:
        print('\n' + '=' * 72)
        print('TASK SKELETONS — files and acceptance are filled in by reading the code, never by the machine\n')
        mil = milestones[-1].id if milestones else 'M1'
        tpat = re.compile(r'^%s-T\d+$' % re.escape(mil))
        n = len([t for t in tasks if tpat.match(t.id)])
        for c, st, v in unc:
            n += 1
            task_id = '%s-T%d' % (mil, n)
            yaml_fields = {
                'status': 'todo',
                'tracker': None,
                'milestone': mil,
                'spec': 'client/USER-CASES.md#%s' % c.id,
                'files': [],
                'acceptance': None,
                'blocked_by': blocked.get(c.id, []),
            }
            print('<!-- macstack:task=%s -->' % task_id)
            print('### %s · %s' % (task_id, title_of(c)))
            print()
            print('```yaml')
            print(dump_yaml(yaml_fields))
            print('```')
            print()
            print('<!-- macstack:notes -->')
            print()
    elif unc:
        print()
        print(msg(lang, 'emit_hint'))

    return 0


if __name__ == '__main__':
    sys.exit(main())
