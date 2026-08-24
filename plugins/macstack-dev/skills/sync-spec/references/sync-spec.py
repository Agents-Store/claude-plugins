#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconcile the BUSINESS half of macstack.json against the client's authored tables.

The inversion, made concrete. client/ROLES-AND-TASKS.md and client/SCREENS.md are written by
a human and corrected by the client; this reads their tables and reports exactly where the
spec disagrees.

WILL change — names and gates it can match unambiguously.
Will NOT   — create or delete anything. A new row needs an id, and an id is a decision:
             workflows, tests and prose reference it, so a machine that invents one is a
             machine that silently orphans a reference on the next rename. New and missing
             rows are REPORTED for a human to resolve.

Columns are read by POSITION. The header row follows docs.language and is never parsed —
that is what lets one script serve documents written in Russian, German or English.

Usage: sync-spec.py <macstack-dir> [--apply]
"""
import sys, os, io, re, json

def rows_after(text, anchor):
    out, lines = [], text.split('\n')
    for i, ln in enumerate(lines):
        if ln.strip() != '<!-- macstack:table=%s -->' % anchor:
            continue
        j, sep = i + 1, False
        while j < len(lines) and lines[j].startswith('|'):
            cells = [c.strip() for c in lines[j].strip().strip('|').split('|')]
            if set(''.join(cells)) <= set('-: '):
                sep = True
            elif sep:
                out.append(cells)
            j += 1
    return out

def role_blocks(text):
    out, parts = [], re.split(r'^### .*?—\s*`([a-z0-9-]+)`\s*$', text, flags=re.M)
    for k in range(1, len(parts) - 1, 2):
        out.append((parts[k], rows_after(parts[k + 1], 'tasks')))
    return out

def norm(s):
    return re.sub(r'\s+', ' ', re.sub(r'`|\*\*|\\', '', s or '')).strip().lower()

GATES = {'ввод': 'input', 'исполнение': 'execute', 'решение': 'approve',
         'input': 'input', 'execute': 'execute', 'approve': 'approve'}
SCREENISH = {'web', 'admin_ui', 'dashboard', 'approval_center', 'form'}

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    root = args[0] if args else 'macstack'
    apply_ = '--apply' in sys.argv
    spec_p = os.path.join(root, 'macstack.json')
    spec = json.load(io.open(spec_p, encoding='utf-8'))
    raw = io.open(spec_p, encoding='utf-8').read()

    rt_p = os.path.join(root, 'client', 'ROLES-AND-TASKS.md')
    if not os.path.exists(rt_p):
        print('нет %s — сначала seed.py' % rt_p); return 1
    rt = io.open(rt_p, encoding='utf-8').read()
    add, gone, chg = [], [], []

    doc_roles = [r for r, _ in role_blocks(rt)]
    spec_roles = [r['id'] for r in (spec.get('roles') or [])]
    add += ['роль `%s` — есть в документе, нет в спеке' % r for r in doc_roles if r not in spec_roles]
    gone += ['роль `%s` — есть в спеке, нет в документе' % r for r in spec_roles if r not in doc_roles]

    spec_tasks = {}
    for p in (spec.get('processes') or []):
        for t in (p.get('tasks') or []):
            h = t.get('human') or {}
            if h.get('role'):
                spec_tasks.setdefault(h['role'], []).append((t, p))

    for role, rws in role_blocks(rt):
        doc = {norm(c[0]): c for c in rws if c and c[0]}
        spc = {norm(t.get('name', t['id'])): (t, p) for t, p in spec_tasks.get(role, [])}
        for k, cells in doc.items():
            if k not in spc:
                add.append('задача роли `%s`: «%s» — нет в спеке, нужен id' % (role, cells[0][:60])); continue
            t, _ = spc[k]
            want = GATES.get(norm(cells[2]) if len(cells) > 2 else '')
            have = (t.get('human') or {}).get('gate')
            if want and want != have:
                chg.append(('gate', t['id'], have, want, cells[0][:50]))
        for k, (t, _) in spc.items():
            if k not in doc:
                gone.append('задача `%s` роли `%s` — есть в спеке, нет в документе' % (t['id'], role))

    doc_tr = rows_after(rt, 'triggers')
    doc_tr_names = {norm(c[0]) for c in doc_tr if c and c[0]}
    for cells in doc_tr:
        if cells and cells[0] and norm(cells[0]) not in {norm(g.get('name', g['id'])) for g in (spec.get('triggers') or [])}:
            add.append('триггер «%s» — нет в спеке, нужен id' % cells[0][:60])
    for g in (spec.get('triggers') or []):
        if norm(g.get('name', g['id'])) not in doc_tr_names:
            gone.append('триггер `%s` — есть в спеке, нет в документе' % g['id'])

    sc_p = os.path.join(root, 'client', 'SCREENS.md')
    if os.path.exists(sc_p):
        sc = rows_after(io.open(sc_p, encoding='utf-8').read(), 'screens')
        paths = {c[1].replace('`', '').strip() for c in sc if len(c) > 1}
        for i in (spec.get('interfaces') or []):
            if i.get('type') in SCREENISH and i.get('path') and i['path'] not in paths:
                gone.append('экран `%s` (%s) — есть в спеке, нет в SCREENS.md' % (i['path'], i['id']))

    print('=== СПЕКА ОТСТАЁТ ОТ ДОКУМЕНТА (%d) ===' % len(add))
    for x in add: print('  +', x)
    print('\n=== ДОКУМЕНТ ОТСТАЁТ ОТ СПЕКИ (%d) ===' % len(gone))
    for x in gone: print('  −', x)
    print('\n=== РАЗОШЛИСЬ ЗНАЧЕНИЯ (%d) ===' % len(chg))
    for what, tid, have, want, name in chg:
        print('  ~ %s задачи `%s`: спека «%s» → документ «%s»  (%s)' % (what, tid, have, want, name))

    if apply_ and chg:
        for what, tid, have, want, _ in chg:
            pat = re.compile(r'("id":\s*"%s".*?"gate":\s*")%s(")' % (re.escape(tid), re.escape(have or '')), re.S)
            raw2, n = pat.subn(r'\g<1>%s\g<2>' % want, raw, count=1)
            if n: raw = raw2
        json.loads(raw)
        io.open(spec_p, 'w', encoding='utf-8').write(raw)
        print('\nприменено значений: %d' % len(chg))
    elif chg:
        print('\nСухой прогон. Повторите с --apply.')
    if add or gone:
        print('\nДобавления и удаления НЕ применяются машинно: новой строке нужен id, а id —')
        print('решение, на которое ссылаются workflow, тесты и проза.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
