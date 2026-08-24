#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seed the two AUTHORED client documents once, from macstack.json.

client/ROLES-AND-TASKS.md and client/SCREENS.md are written by a human and read by the
client — they are the source of the spec's business half, not its output. But a blank page
is a bad start when the spec already knows the roles, the tasks and the interfaces, so this
seeds a FIRST version and then never touches it again.

REFUSES to overwrite. If the file exists, say so and stop: overwriting an authored document
with a machine guess is how a client's correction disappears.

Tables carry the content. Columns are read by POSITION — the header row follows
docs.language and is for the human only, so a project writing in German parses the same.

Usage: seed.py <macstack-dir> [--force]
"""
import sys, os, io, json

L = {
 'ru': dict(
  rt_title="Роли, их задачи и что эти задачи запускает",
  rt_howto="Как читать и как править",
  rt_howto_body=(
   "**Этот документ пишете вы, а не платформа.** Из него собирается машинная часть спецификации:\n"
   "какие есть роли, какие у них задачи, что эти задачи запускает и какой процесс на это отвечает.\n\n"
   "Строки таблиц можно править, добавлять и удалять — это и есть способ изменить продукт.\n"
   "**Порядок колонок менять нельзя:** их читают по позиции, а не по названию.\n\n"
   "«Ворота» говорят, что делает человек: `ввод` — вносит данные, `исполнение` — совершает\n"
   "действие, `решение` — утверждает чужую работу. Прочерк значит, что задачу делает платформа\n"
   "сама, и тогда в последней колонке назван процесс, который её выполняет."),
  rt_roles="Роли", rt_trig="Триггеры",
  rt_sees="Что видит", rt_can="Что может",
  c_task="задача", c_start="что запускает", c_gate="ворота", c_wf="что выполняет",
  c_trig="триггер", c_type="тип", c_when="когда", c_raise="что поднимает",
  by_person="действие человека", none="—",
  gate={'input':'ввод','execute':'исполнение','approve':'решение'},
  sc_title="Экраны — что на какой странице видно",
  sc_howto="Как читать и как править",
  sc_howto_body=(
   "**Этот документ пишете вы.** Одна строка — один экран. Последняя колонка — самая важная:\n"
   "там написано, чего на этом экране быть НЕ должно. Запрет, записанный против конкретного\n"
   "экрана, проверяется тем, что экран открывают; тот же запрет, записанный один раз в общем\n"
   "документе, приходится держать в голове на каждой странице.\n\n"
   "**Заготовка ниже — по одной строке на область интерфейса, а не на страницу.** Платформа знает\n"
   "области, а страницы знаете вы: разбейте строки на реальные экраны и заполните последние три\n"
   "колонки."),
  sc_screens="Экраны",
  s_screen="экран", s_addr="адрес", s_who="кто видит", s_what="что на нём",
  s_can="что можно сделать", s_not="чего быть не должно",
  journal="Журнал документа", j_date="дата", j_what="что изменилось",
  j_seed="заготовка собрана из `macstack.json`; дальше документ ведётся руками"),
 'en': dict(
  rt_title="Roles, their tasks, and what starts them",
  rt_howto="How to read and how to edit",
  rt_howto_body=(
   "**You write this document, not the platform.** The machine half of the specification is built\n"
   "from it: which roles exist, what their tasks are, what starts each one, and which process answers.\n\n"
   "Table rows may be edited, added and removed — that is how the product is changed.\n"
   "**Column order must not change:** they are read by position, not by heading.\n\n"
   "The gate says what the person does: `input` supplies data, `execute` performs the act,\n"
   "`approve` signs off somebody else's work. A dash means the platform does it by itself, and then\n"
   "the last column names the process that runs it."),
  rt_roles="Roles", rt_trig="Triggers",
  rt_sees="Sees", rt_can="Can",
  c_task="task", c_start="what starts it", c_gate="gate", c_wf="what runs it",
  c_trig="trigger", c_type="type", c_when="when", c_raise="what it raises",
  by_person="a person acts", none="—",
  gate={'input':'input','execute':'execute','approve':'approve'},
  sc_title="Screens — what is visible where",
  sc_howto="How to read and how to edit",
  sc_howto_body=(
   "**You write this document.** One row, one screen. The last column is the important one: it says\n"
   "what must NOT be visible there. A prohibition written against a screen is checked by opening that\n"
   "screen; the same prohibition written once in a general document has to be remembered on every page.\n\n"
   "**The seed below has one row per interface AREA, not per page.** The platform knows the areas; you\n"
   "know the pages. Split the rows into real screens and fill the last three columns."),
  sc_screens="Screens",
  s_screen="screen", s_addr="address", s_who="who sees it", s_what="what is on it",
  s_can="what can be done", s_not="what must NOT be visible",
  journal="Document journal", j_date="date", j_what="what changed",
  j_seed="seeded from `macstack.json`; from here the document is maintained by hand"),
}

def esc(x):
    return str(x if x is not None else '').replace('|','\\|').replace('\n',' ').strip()

def journal(t, date):
    return ('\n<!-- macstack:section=journal -->\n## %s\n\n| %s | %s |\n|---|---|\n| %s | %s |\n'
            % (t['journal'], t['j_date'], t['j_what'], date, t['j_seed']))

def seed_roles(spec, t, lang, date):
    procs = spec.get('processes') or []
    wfs = {w['id']: w for w in (spec.get('workflows') or [])}
    trgs = {g['id']: g for g in (spec.get('triggers') or [])}
    o = ['<!-- macstack:doc=roles_tasks lang=%s version=1 -->' % lang, '# ' + t['rt_title'], '',
         '<!-- macstack:section=howto -->', '## ' + t['rt_howto'], '', t['rt_howto_body'], '',
         '<!-- macstack:section=roles -->', '## ' + t['rt_roles'], '']
    for r in (spec.get('roles') or []):
        o.append('### %s — `%s`' % (r.get('name', r['id']), r['id']))
        o.append('')
        if r.get('sees'): o.append('**%s:** %s' % (t['rt_sees'], r['sees']))
        if r.get('can'):  o.append('**%s:** %s' % (t['rt_can'], r['can']))
        o.append('')
        o.append('<!-- macstack:table=tasks -->')
        o.append('| %s | %s | %s | %s |' % (t['c_task'], t['c_start'], t['c_gate'], t['c_wf']))
        o.append('|---|---|---|---|')
        for p in procs:
            for task in (p.get('tasks') or []):
                h = task.get('human') or {}
                if h.get('role') != r['id']:
                    continue
                start = t['by_person']
                if task.get('workflow'):
                    w = wfs.get(task['workflow'])
                    names = [trgs[x]['name'] for x in (w.get('triggers') or []) if x in trgs] if w else []
                    start = ' · '.join(names) or t['by_person']
                o.append('| %s | %s | %s | %s |' % (
                    esc(task.get('name', task['id'])), esc(start),
                    t['gate'].get(h.get('gate',''), esc(h.get('gate')) or t['none']),
                    esc(p.get('name', p['id']))))
        o.append('')
    o += ['<!-- macstack:section=triggers -->', '## ' + t['rt_trig'], '',
          '<!-- macstack:table=triggers -->',
          '| %s | %s | %s | %s |' % (t['c_trig'], t['c_type'], t['c_when'], t['c_raise']),
          '|---|---|---|---|']
    for gid in sorted(trgs):
        g = trgs[gid]; cfg = g.get('config') or {}
        raised = [w.get('name', w['id']) for w in (spec.get('workflows') or []) if gid in (w.get('triggers') or [])]
        o.append('| %s | %s | %s | %s |' % (
            esc(g.get('name', gid)), esc(g.get('type')),
            esc(cfg.get('schedule') or cfg.get('event') or t['none']),
            esc(' · '.join(raised) or t['none'])))
    o.append('')
    return '\n'.join(o) + journal(t, date)

def seed_screens(spec, t, lang, date):
    o = ['<!-- macstack:doc=screens lang=%s version=1 -->' % lang, '# ' + t['sc_title'], '',
         '<!-- macstack:section=howto -->', '## ' + t['sc_howto'], '', t['sc_howto_body'], '',
         '<!-- macstack:section=screens -->', '## ' + t['sc_screens'], '',
         '<!-- macstack:table=screens -->',
         '| %s | %s | %s | %s | %s | %s |' % (t['s_screen'], t['s_addr'], t['s_who'],
                                              t['s_what'], t['s_can'], t['s_not']),
         '|---|---|---|---|---|---|']
    # только то, что человек ОТКРЫВАЕТ. Канал (почта), выгрузка и API — не экраны:
    # у них нет страницы, на которую можно посмотреть и проверить, что на ней видно.
    SCREENISH = {'web', 'admin_ui', 'dashboard', 'approval_center', 'form'}
    for i in (spec.get('interfaces') or []):
        if i.get('type') not in SCREENISH:
            continue
        if i.get('mode') and i['mode'] != 'ui':
            continue
        if i.get('audience') not in (None, 'human'):
            continue
        o.append('| %s | `%s` | %s | | | |' % (
            esc(i.get('name', i['id'])), esc(i.get('path') or t['none']),
            esc(' · '.join(i.get('roles') or []) or t['none'])))
    o.append('')
    return '\n'.join(o) + journal(t, date)

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    root = args[0] if args else 'macstack'
    force = '--force' in sys.argv
    date = None
    for i, a in enumerate(sys.argv):
        if a == '--date' and i + 1 < len(sys.argv): date = sys.argv[i + 1]
    if not date:
        import datetime; date = datetime.date.today().isoformat()
    spec = json.load(io.open(os.path.join(root, 'macstack.json'), encoding='utf-8'))
    lang = ((spec.get('docs') or {}).get('language')) or 'en'
    t = L.get(lang, L['en'])
    os.makedirs(os.path.join(root, 'client'), exist_ok=True)
    rc = 0
    for name, fn in (('ROLES-AND-TASKS.md', seed_roles), ('SCREENS.md', seed_screens)):
        p = os.path.join(root, 'client', name)
        if os.path.exists(p) and not force:
            print('%s: уже существует — НЕ трогаю (авторский документ)' % p); rc = 1; continue
        io.open(p, 'w', encoding='utf-8').write(fn(spec, t, lang, date))
        print('%s: заготовка создана' % p)
    return 0 if rc == 0 else 0

if __name__ == '__main__':
    sys.exit(main())
