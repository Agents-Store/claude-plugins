#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сверка документов и macstack.json в обе стороны.

Отвечает на два вопроса, на которые до сих пор не отвечал никто:

  1. Есть ли у каждой сущности документа адрес в машинной спецификации?
  2. Есть ли у каждой записи спецификации место хоть в одном документе?

Второй вопрос важнее и его никогда не задавали. Проверка «метка разрешается»
ловит враньё документа; она не ловит молчание — раздел спеки, о котором ни один
документ не сказал ни слова. На живом проекте так молчали цели, результаты и
интеграции: одиннадцать записей, которых клиент не видел никогда.

Usage: reconcile.py <macstack-dir>      выход 1, если есть дыры
"""
import sys, os, io, re, json

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'documents', 'references')))
import v3                                              # noqa: E402

RESERVED = ('X', 'S', 'Z')          # сквозное, сценарии, запреты — ничьи по определению
NOT_SCREENS = ('channel', 'api_portal', 'report')      # интерфейсы, которые человек не открывает

HOLE, INFO, OK = 'ДЫРА', 'инфо', 'ок'


def run(root):
    spec = json.load(io.open(os.path.join(root, 'macstack.json'), encoding='utf-8'))
    C = os.path.join(root, 'client')
    G = os.path.join(root, 'generated')
    rep = []

    def say(mark, text):
        rep.append((mark, text))

    def docs_text():
        t = []
        for f in sorted(os.listdir(C)):
            if f.endswith('.md'):
                t.append(io.open(os.path.join(C, f), encoding='utf-8').read())
        return u'\n'.join(t)

    def ids_of(fname, coll):
        return [i for i in v3.load(os.path.join(C, fname))
                if i.id and (i.ref or '').startswith(coll)]

    all_client = docs_text()

    # ── документ -> спека
    def ref_target(item):
        """id, на который указывает метка: `interfaces[id=coach-portal]` -> coach-portal.

        Сверять надо АДРЕС В МЕТКЕ, а не id сущности документа. Экранов в UX-UI.md
        тридцать семь, а interfaces[] намеренно держится на уровне областей: у двадцати
        восьми из них собственной записи в спеке нет и не будет, и метка честно ведёт на
        область. Сравнение по id объявляло все двадцать восемь дырами."""
        m = re.search(r'\[id=([^\]]+)\]', item.ref or '')
        return m.group(1) if m else None

    for coll, fname, label in (('roles', 'AUTOMATION.md', u'роли'),
                               ('triggers', 'AUTOMATION.md', u'триггеры'),
                               ('interfaces', 'UX-UI.md', u'экраны')):
        sids = set(x['id'] for x in (spec.get(coll) or []))
        items = ids_of(fname, coll + '[id=')
        dids = set(i.id for i in items)
        targets = set(x for x in (ref_target(i) for i in items) if x)
        extra = set(t for t in targets if t not in sids)     # метка ведёт в никуда
        missing = sids - targets                             # запись спеки ничем не названа
        say(OK, u'%s: в спеке %d, в документе %d' % (label, len(sids), len(dids)))
        for x in sorted(extra):
            say(HOLE, u'метка ведёт на `%s`, а такой записи в спеке нет' % x)
        for x in sorted(missing):
            kind = next((i.get('type') for i in (spec.get(coll) or []) if i['id'] == x), None)
            if coll == 'interfaces' and kind in NOT_SCREENS:
                say(INFO, u'`%s` (%s) — не экран, описания в UX-UI.md не нужно' % (x, kind))
            else:
                say(HOLE, u'`%s` есть в спеке, в документе нет' % x)

    # задачи процессов
    stasks = {}
    for p in (spec.get('processes') or []):
        for t in (p.get('tasks') or []):
            stasks[t['id']] = bool((t.get('human') or {}).get('role'))
    dtasks = set()
    for i in ids_of('AUTOMATION.md', 'processes['):
        m = re.search(r'\.tasks\[id=([^\]]+)\]', i.ref or '')
        dtasks.add(m.group(1) if m else i.id)
    human = set(k for k, v in stasks.items() if v)
    say(OK, u'задачи: в спеке %d (человеческих %d), в документе %d'
        % (len(stasks), len(human), len(dtasks)))
    for x in sorted(human - dtasks):
        say(HOLE, u'`%s` — человеческая задача, в документе нет' % x)
    for x in sorted(dtasks - set(stasks)):
        say(HOLE, u'`%s` есть в документе, в спеке нет' % x)

    # кейсы и роли
    cases = [i.id for i in v3.load(os.path.join(C, 'USER-CASES.md'))
             if i.id and re.match(r'^[A-Z]-\d{2}$', i.id)]
    declared = {}
    for r in (spec.get('roles') or []):
        for pat in (r.get('cases') or []):
            declared[pat.split('-')[0]] = r['id']
    orphan = [c for c in cases
              if c.split('-')[0] not in declared and c.split('-')[0] not in RESERVED]
    say(OK, u'кейсы: %d, из них ничьих по определению (%s) — %d'
        % (len(cases), u'/'.join(RESERVED),
           sum(1 for c in cases if c.split('-')[0] in RESERVED)))
    if orphan:
        say(HOLE, u'%d кейсов не покрыты ни одним roles[].cases: %s'
            % (len(orphan), u', '.join(orphan[:10])))

    # открытые вопросы — витрина только живых
    lc = spec.get('lifecycle') or {}
    nf = [x for x in (lc.get('needs_from_client') or []) if isinstance(x, dict)]
    closed = [x['id'] for x in nf if x.get('status') != 'open']
    if closed:
        say(HOLE, u'needs_from_client — витрина живых пунктов, а держит закрытые: %s'
            % u', '.join(closed))
    else:
        say(OK, u'needs_from_client: %d записей, все живые' % len(nf))

    # ── спека -> документы: о чём не сказано нигде
    for key, label in (('goals', u'цели'), ('results', u'результаты'),
                       ('processes', u'процессы'), ('integrations', u'интеграции'),
                       ('workflows', u'workflow'), ('entities', u'сущности данных'),
                       ('software', u'софт')):
        ids = [i.get('id') for i in (spec.get(key) or []) if isinstance(i, dict) and i.get('id')]
        miss = [i for i in ids if i not in all_client]
        if not ids:
            continue
        if len(miss) == len(ids):
            say(HOLE, u'%s: НИ ОДНА из %d записей не упомянута ни в одном клиентском документе'
                % (label, len(ids)))
        elif miss:
            say(INFO, u'%s: упомянуто %d из %d · нет: %s'
                % (label, len(ids) - len(miss), len(ids), u', '.join(miss[:6])))
        else:
            say(OK, u'%s: все %d упомянуты' % (label, len(ids)))

    # ── generated
    arch = io.open(os.path.join(G, 'ARCHITECTURE.md'), encoding='utf-8').read() \
        if os.path.exists(os.path.join(G, 'ARCHITECTURE.md')) else u''
    for key, label in (('software', u'софт'), ('entities', u'сущности'),
                       ('workflows', u'workflow'), ('interfaces', u'интерфейсы')):
        ids = [i.get('id') for i in (spec.get(key) or []) if isinstance(i, dict)]
        hit = [i for i in ids if i and i in arch]
        say(OK if len(hit) == len(ids) else HOLE,
            u'ARCHITECTURE.md: %s %d из %d' % (label, len(hit), len(ids)))
    tc = os.path.join(G, 'TEST-CASES.md')
    tests = [i for i in v3.load(tc) if i.id and re.match(r'^[A-Z]-\d{2}\.T\d+$', i.id)] \
        if os.path.exists(tc) else []
    say(OK if tests else HOLE,
        u'TEST-CASES.md: тестов %d на %d кейсов' % (len(tests), len(cases)))

    holes = sum(1 for m, _ in rep if m == HOLE)
    for m, txt in rep:
        print(u'  %-5s %s' % (m, txt))
    print(u'\n  дыр: %d' % holes)
    return 1 if holes else 0


if __name__ == '__main__':
    sys.exit(run(sys.argv[1] if len(sys.argv) > 1 else 'macstack'))
