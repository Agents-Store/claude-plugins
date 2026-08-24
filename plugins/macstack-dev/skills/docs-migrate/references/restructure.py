#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Move a flat macstack/ folder into the four-folder layout.

  macstack/
  ├── README.md · macstack.json
  ├── client/      what a human writes and a client reads — the source of truth
  ├── generated/   what the plugin builds
  ├── inbox/       what the client sent
  └── history/     journals, decisions, deltas, reviews, handoffs, the plan of work

Two jobs, and the second is the one that goes wrong quietly:

1. `git mv` each file, so history follows it.
2. Re-point every reference. Documents move one level DEEPER, so a link that read
   `../docs/architecture.md` from the root must read `../../docs/architecture.md` from
   client/. Doing that by pattern breaks links that merely look alike; this resolves every
   reference to a repo path against its OLD location and re-expresses it against the NEW
   one. A reference that does not resolve is REPORTED, never guessed at.

Usage: restructure.py <repo-root> [--apply]   (dry run by default)
"""
import sys, os, io, re, subprocess, posixpath

MOVES = [
    ('USER-CASES.md',     'client/USER-CASES.md'),
    ('BUSINESS-LOGIC.md', 'client/BUSINESS-LOGIC.md'),
    ('OPEN-QUESTIONS.md', 'client/OPEN-QUESTIONS.md'),
    ('ARCHITECTURE.md',   'generated/ARCHITECTURE.md'),
    ('TEST-CASES.md',     'generated/TEST-CASES.md'),
    ('TASKS.md',          'history/TASKS.md'),
    ('DECISIONS.md',      'history/DECISIONS.md'),
    ('CHANGELOG.md',      'history/CHANGELOG.md'),
    ('log.md',            'history/log.md'),
    ('decisions',         'history/decisions'),
    ('deltas',            'history/deltas'),
    ('reviews',           'history/reviews'),
    ('handoffs',          'history/handoffs'),
]
DROP = ['ROLES.md']

REF = re.compile(r'(?P<open>\]\(|`)(?P<path>(?:\.\.?/)*[A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:md|json|html|pdf))(?P<close>\)|`)')

def sh(a, cwd): return subprocess.run(a, cwd=cwd, capture_output=True, text=True)

def remap(p, m):
    if p in m: return m[p]
    for o, n in m.items():
        if p.startswith(o + '/'): return n + p[len(o):]
    return p

def main():
    root = sys.argv[1] if len(sys.argv) > 1 else '.'
    apply_ = '--apply' in sys.argv
    mroot = os.path.join(root, 'macstack')
    if not os.path.isdir(mroot):
        print('нет папки macstack/ в %s' % root); return 1

    moves = [(o, n) for o, n in MOVES if os.path.exists(os.path.join(mroot, o))]
    m = dict(moves)
    print('=== ПЕРЕЕЗДЫ (%d) ===' % len(moves))
    for o, n in moves: print('  macstack/%-22s → macstack/%s' % (o, n))
    for d in DROP:
        if os.path.exists(os.path.join(mroot, d)):
            print('  macstack/%-22s → УДАЛЯЕТСЯ (заменён client/ROLES-AND-TASKS.md)' % d)

    if apply_:
        for sub in ('client', 'generated', 'history'):
            os.makedirs(os.path.join(mroot, sub), exist_ok=True)
        for o, n in moves:
            os.makedirs(os.path.dirname(os.path.join(mroot, n)), exist_ok=True)
            r = sh(['git', 'mv', 'macstack/' + o, 'macstack/' + n], root)
            if r.returncode: print('  ! git mv %s: %s' % (o, r.stderr.strip()))
        for d in DROP:
            if os.path.exists(os.path.join(mroot, d)):
                sh(['git', 'rm', '-q', 'macstack/' + d], root)

    files = [f for f in sh(['git', 'ls-files'], root).stdout.split('\n')
             if f and f.endswith(('.md', '.ts', '.tsx', '.json', '.example'))]
    nf = nr = 0; bad = []
    for f in files:
        old_f = f
        if f.startswith('macstack/'):
            inner = f[len('macstack/'):]
            for o, n in m.items():
                if inner == n or inner.startswith(n + '/'):
                    old_f = 'macstack/' + o + inner[len(n):]; break
        p = os.path.join(root, f)
        if not os.path.exists(p): continue
        try: txt = io.open(p, encoding='utf-8').read()
        except Exception: continue
        od, nd = posixpath.dirname(old_f), posixpath.dirname(f)
        cnt = [0]

        def fix(mt):
            ref = mt.group('path')
            if not ref.startswith('.'):
                if not ref.startswith('macstack/'): return mt.group(0)
                tgt = 'macstack/' + remap(ref[len('macstack/'):], m)
                if tgt == ref: return mt.group(0)
                cnt[0] += 1
                return mt.group('open') + tgt + mt.group('close')
            a_old = posixpath.normpath(posixpath.join(od, ref))
            a_new = ('macstack/' + remap(a_old[len('macstack/'):], m)) if a_old.startswith('macstack/') else a_old
            # существование проверяем по СТАРОМУ пути: в сухом прогоне файл ещё не переехал,
            # а в режиме --apply уже переехал — проверка по новому дала бы ложь в первом случае
            # и молчание во втором. Старый путь истинен до перекладки в обоих.
            if not (os.path.exists(os.path.join(root, a_old)) or os.path.exists(os.path.join(root, a_new))):
                bad.append('%s → %s' % (f, ref)); return mt.group(0)
            rel = posixpath.relpath(a_new, nd or '.')
            if rel == ref: return mt.group(0)
            cnt[0] += 1
            return mt.group('open') + rel + mt.group('close')

        out = REF.sub(fix, txt)
        if cnt[0]:
            nf += 1; nr += cnt[0]
            if apply_: io.open(p, 'w', encoding='utf-8').write(out)

    print('\n=== ССЫЛКИ ===')
    print('  файлов: %d · ссылок: %d%s' % (nf, nr, '' if apply_ else '  (сухой прогон)'))
    if bad:
        print('  НЕ РАЗРЕШИЛИСЬ (%d) — проверить руками:' % len(bad))
        for u in sorted(set(bad))[:15]: print('    ' + u)
    if not apply_: print('\nСухой прогон. Повторите с --apply.')
    return 0

if __name__ == '__main__':
    sys.exit(main())
