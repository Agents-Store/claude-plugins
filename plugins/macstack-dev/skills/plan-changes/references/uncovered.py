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
"63 cases with no plan" on a project where nearly all of them are built, which is true and
useless: a work list nobody believes is a work list nobody reads.

WHAT IT DOES NOT DO: decide which files a task touches or what proves it done. That is
judgement over the codebase, and a machine that guesses it produces a plan nobody can
trust. It emits the SKELETON — id, name, the pointer back to the case — and the agent or
the human fills `files` and `acceptance` by reading the code.

Usage: uncovered.py <macstack-dir> [--emit]   (--emit prints ready task skeletons)
"""
import sys, os, io, re, json

def cases(text):
    """-> [(id, title, priority, [acceptance bullets])] в порядке документа."""
    out, cur, lines = [], None, text.split('\n')
    i = 0
    while i < len(lines):
        h = re.match(r'^### ([A-Z]-\d+) · (.+?)(?:\s{2,}\[(.+?)\])?\s*$', lines[i])
        if h:
            cur = (h.group(1), h.group(2).strip(), (h.group(3) or '').strip(), [])
            out.append(cur); i += 1; continue
        if cur is not None and lines[i].strip().startswith('**') and lines[i].strip().endswith(':**'):
            j = i + 1
            while j < len(lines) and lines[j].strip():
                if lines[j].startswith('- '): cur[3].append(lines[j][2:].rstrip())
                elif lines[j].startswith('  ') and cur[3]: cur[3][-1] += ' ' + lines[j].strip()
                j += 1
            i = j; continue
        i += 1
    return out

def tasks(text):
    """-> [(id, name, status, spec_pointer, blocked_by)]"""
    out = []
    for m in re.finditer(r'^### (~~)?([A-Z]?\w*-?T?\d+[\w-]*)(~~)? · (.+?)\s{2,}(\w+)', text, re.M):
        tid, name, st = m.group(2), m.group(4), m.group(5)
        blk = text[m.end():m.end() + 700]
        spec = re.search(r'^\s*-\s*spec:\s*(.+)$', blk, re.M)
        bb = re.search(r'^\s*-\s*blocked_by:\s*(.+)$', blk, re.M)
        out.append((tid, name, st, spec.group(1).strip() if spec else '', bb.group(1).strip() if bb else ''))
    return out

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    root = args[0] if args else 'macstack'
    emit = '--emit' in sys.argv

    uc_p = os.path.join(root, 'client', 'USER-CASES.md')
    tk_p = os.path.join(root, 'history', 'TASKS.md')
    oq_p = os.path.join(root, 'client', 'OPEN-QUESTIONS.md')
    for p in (uc_p, tk_p):
        if not os.path.exists(p):
            print('нет %s' % p); return 1

    cs = cases(io.open(uc_p, encoding='utf-8').read())
    tk_text = io.open(tk_p, encoding='utf-8').read()
    ts = tasks(tk_text)
    oq = io.open(oq_p, encoding='utf-8').read() if os.path.exists(oq_p) else ''
    live_a = set(re.findall(r'^\| (A\d+) \|', oq, re.M))

    # вердикты последнего аудита: | X-01 | Implemented | улика...
    verdict, rev_name = {}, None
    rdir = os.path.join(root, 'history', 'reviews')
    revs = sorted(f for f in os.listdir(rdir) if f.endswith('conformance.md')) if os.path.isdir(rdir) else []
    if revs:
        rev_name = revs[-1]
        for m in re.finditer(r'^\|\s*\*?\*?([A-Z]-\d+)\*?\*?\s*\|\s*([^|]+?)\s*\|',
                             io.open(os.path.join(rdir, rev_name), encoding='utf-8').read(), re.M):
            verdict[m.group(1)] = m.group(2).strip()
    DONE = ('implemented', 'выполнено', 'реализовано', 'passes', 'ok')

    covered = {}
    for tid, name, st, spec, bb in ts:
        for cid in re.findall(r'\b([A-Z]-\d+)\b', spec):
            covered.setdefault(cid, []).append((tid, st))

    known = {c[0] for c in cs}
    orphan = [(tid, spec) for tid, _, _, spec, _ in ts
              for cid in re.findall(r'\b([A-Z]-\d+)\b', spec) if cid not in known]

    # чем заблокирован кейс: A-пункт, упомянутый в его пунктах приёмки
    blocked = {}
    for cid, title, pri, bullets in cs:
        hits = sorted({a for b in bullets for a in re.findall(r'\b(A\d+)\b', b) if a in live_a})
        if hits: blocked[cid] = hits

    def state(cid):
        if cid in covered: return 'task'
        v = verdict.get(cid)
        if v and any(d in v.lower() for d in DONE): return 'done'
        if v: return 'partial'
        return 'todo'

    unc = [(cid, t, p, b) for cid, t, p, b in cs if state(cid) == 'todo']
    part = [c for c in cs if state(c[0]) == 'partial']
    done = [c for c in cs if state(c[0]) == 'done']
    print('=== КЕЙСОВ %d ===' % len(cs))
    print('  задача заведена     : %d' % len(covered))
    print('  аудит: сделано      : %d%s' % (len(done), ('  (%s)' % rev_name) if rev_name else ''))
    print('  аудит: не до конца  : %d' % len(part))
    print('  НИ ТОГО НИ ДРУГОГО  : %d   ← это и есть работа' % len(unc))
    if part:
        print('\n=== АУДИТ НАШЁЛ НЕДОДЕЛКИ (%d) ===' % len(part))
        for cid, title, pri, _ in part:
            print('    %-7s %-52s %s' % (cid, title[:52], verdict.get(cid, '')[:34]))
    print('\n=== БЕЗ ПЛАНА И БЕЗ ПРОВЕРКИ ===')
    by_pri = {}
    for cid, title, pri, _ in unc:
        by_pri.setdefault(pri or '—', []).append((cid, title))
    for pri in ('критично', 'critical', 'важно', 'important', 'желательно', 'nice-to-have', '—'):
        if pri not in by_pri: continue
        print('\n  [%s] %d' % (pri, len(by_pri[pri])))
        for cid, title in by_pri[pri]:
            mark = '  ⏸ ' + ','.join(blocked[cid]) if cid in blocked else ''
            print('    %-7s %s%s' % (cid, title[:66], mark))
    if orphan:
        print('\n=== ЗАДАЧИ НА НЕСУЩЕСТВУЮЩИЙ КЕЙС (%d) ===' % len(orphan))
        for tid, spec in orphan: print('    %-10s → %s' % (tid, spec[:60]))

    if emit and unc:
        print('\n' + '=' * 72)
        print('ЗАГОТОВКИ ЗАДАЧ — files и acceptance заполняются по коду, не машиной\n')
        ms = re.findall(r'^\| \*\*(M\d+)\*\*', tk_text, re.M)
        mil = ms[-1] if ms else 'M1'
        n = len([t for t in ts if t[0].startswith(mil + '-')])
        for cid, title, pri, bullets in unc:
            n += 1
            print('### %s-T%d · %s   todo ·' % (mil, n, title))
            print()
            print('- tracker: ')
            print('- spec: `client/USER-CASES.md` %s — %d пункт(ов) приёмки' % (cid, len(bullets)))
            print('- files: ')
            print('- acceptance: ')
            print('- blocked_by: %s' % (', '.join(blocked.get(cid, [])) or '—'))
            print()
    elif unc:
        print('\nПовторите с --emit, чтобы получить заготовки задач.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
