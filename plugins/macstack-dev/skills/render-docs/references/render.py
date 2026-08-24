#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the generated documents of a macstack/ folder from macstack.json.

Deterministic BY DESIGN. Lint rule 12.18 re-renders and compares, so a renderer whose
output varies between runs would make that rule permanently red. Everything here is a
pure function of the spec — no timestamps in the body, no dict iteration that depends on
hash order, no prose invented at render time.

The ONE exception is the journal: those rows are human history and must survive a
rebuild. They are read back out of the existing file and carried forward. A new row is
appended only when the rendered body actually changed, which is what keeps a second run
byte-identical to the first.

Usage:  render.py <macstack-dir> [--date YYYY-MM-DD] [--check]
        --check   render into memory and report differences without writing (12.18)
"""
import sys, os, io, json, datetime, difflib

# ---------------------------------------------------------------- i18n
L = {
 'ru': dict(
   banner_note="Собран из `{src}`. Правки руками теряются при следующей сборке — правьте источник.",
   roles_title="Роли, их задачи и что эти задачи запускает",
   roles_howto="Как читать этот документ",
   roles_howto_body=(
     "По каждой роли — что она делает и **что приводит её задачу в движение**. Задача с «воротами» —\n"
     "это работа человека: `ввод` он вносит данные, `исполнение` он совершает действие, `решение` он\n"
     "утверждает чужую работу. Задача без ворот исполняется платформой, и тогда названо, какой\n"
     "workflow её делает, что его поднимает и где он в коде.\n\n"
     "Под ролью перечислено только то, что делает ЧЕЛОВЕК. Что платформа делает сама — в разделе\n"
     "«Триггеры»: обратный индекс расписание или событие → что оно поднимает → чьи задачи сдвигает.\n"
     "Так сделано намеренно: workflow процесса не принадлежит роли, и подшивать выпуск счетов под\n"
     "коуча только потому, что он работает в том же процессе, — значит врать о его обязанностях."),
   roles_sec="Роли", triggers_sec="Триггеры",
   arch_title="Архитектура — как здесь строят",
   arch_howto="Как читать этот документ",
   arch_howto_body=(
     "Машинная половина спецификации, разложенная для человека и для агента, которому предстоит\n"
     "здесь строить: чем собрано, что хранится и где, что исполняется и в каком файле.\n\n"
     "Этот документ **не заменяет** `../docs/architecture.md`. Там — то, чего в спеке не выразить:\n"
     "измеренные ловушки, аргументы за решения, грабли, на которые уже наступали. Здесь — только\n"
     "то, что можно пересобрать из `macstack.json`, и потому оно всегда актуально."),
   stack_sec="Чем собрано", entities_sec="Сущности и где они лежат",
   wf_sec="Что исполняется", integ_sec="Интеграции и контекст",
   journal_sec="Журнал документа",
   col_date="дата", col_what="что изменилось",
   rebuilt="пересобран из `{src}`", created="создан",
   gate={'input':'ввод','execute':'исполнение','approve':'решение'},
   t_task="задача", t_proc="процесс", t_gate="ворота", t_start="что запускает",
   t_wf="workflow", t_where="где в коде", t_status="статус",
   by_person="действие человека", none="—",
   t_trigger="триггер", t_type="тип", t_cfg="настройка", t_raises="что поднимает", t_moves="чьи задачи двигает",
   t_soft="софт", t_layers="слои", t_role="роль", t_entity="сущность", t_master="мастер", t_stores="хранится в",
   t_engine="движок", t_iface="интерфейс", t_plugin="плагин", t_covers="покрывает", t_mcp="MCP",
   no_roles="В спецификации нет ни одной роли.", no_trig="В спецификации нет ни одного триггера."),
 'en': dict(
   banner_note="Generated from `{src}`. Hand edits are lost on the next render — edit the source.",
   roles_title="Roles, their tasks, and what starts them",
   roles_howto="How to read this",
   roles_howto_body=(
     "Per role: what it does and **what sets its task in motion**. A task with a gate is a person's\n"
     "work — `input` they supply data, `execute` they perform the act, `approve` they sign off\n"
     "somebody else's. A task without a gate is run by the platform, and then the workflow, its\n"
     "trigger and its place in the code are named.\n\n"
     "A role lists only what a PERSON does. What the platform does by itself is the Triggers section:\n"
     "the reverse index of schedule or event → what it raises → whose tasks move. Deliberately so — a\n"
     "process workflow does not belong to a role, and filing invoice issuance under the coach because\n"
     "he works in the same process would misstate his duties."),
   roles_sec="Roles", triggers_sec="Triggers",
   arch_title="Architecture — how this is built",
   arch_howto="How to read this",
   arch_howto_body=(
     "The machine half of the spec laid out for a human and for the agent that has to build here:\n"
     "what it is made of, what is stored and where, what runs and in which file.\n\n"
     "This does **not** replace `../docs/architecture.md`. That one holds what the spec cannot\n"
     "express — measured traps, the argument behind a decision, the rake already stepped on. This\n"
     "holds only what can be rebuilt from `macstack.json`, which is why it is always current."),
   stack_sec="What it is made of", entities_sec="Entities and where they live",
   wf_sec="What runs", integ_sec="Integrations and context",
   journal_sec="Document journal",
   col_date="date", col_what="what changed",
   rebuilt="rebuilt from `{src}`", created="created",
   gate={'input':'input','execute':'execute','approve':'approve'},
   t_task="task", t_proc="process", t_gate="gate", t_start="what starts it",
   t_wf="workflow", t_where="in the code", t_status="status",
   by_person="a person acts", none="—",
   t_trigger="trigger", t_type="type", t_cfg="config", t_raises="raises", t_moves="moves tasks of",
   t_soft="software", t_layers="layers", t_role="role", t_entity="entity", t_master="master", t_stores="stored in",
   t_engine="engine", t_iface="interface", t_plugin="plugin", t_covers="covers", t_mcp="MCP",
   no_roles="The spec declares no roles.", no_trig="The spec declares no triggers."),
}

def esc(s):
    return str(s).replace('|', '\\|').replace('\n', ' ').strip() if s is not None else ''

def anchor(key):
    return '<!-- macstack:section=%s -->' % key

# ---------------------------------------------------------------- ROLES.md
def render_roles(spec, t, src):
    roles = spec.get('roles') or []
    procs = spec.get('processes') or []
    wfs = {w['id']: w for w in (spec.get('workflows') or [])}
    trgs = {g['id']: g for g in (spec.get('triggers') or [])}

    out = []
    out.append('# ' + t['roles_title'])
    out.append('')
    out.append(anchor('howto'))
    out.append('## ' + t['roles_howto'])
    out.append('')
    out.append(t['roles_howto_body'])
    out.append('')
    out.append(anchor('roles'))
    out.append('## ' + t['roles_sec'])
    out.append('')
    if not roles:
        out.append('_%s_' % t['no_roles']); out.append('')
    for r in roles:
        out.append('### %s — `%s`' % (r.get('name', r['id']), r['id']))
        out.append('')
        if r.get('sees'): out.append('**sees:** %s' % r['sees'])
        if r.get('can'): out.append('**can:** %s' % r['can'])
        if r.get('isolation'): out.append('**isolation:** %s' % r['isolation'])
        if r.get('sees') or r.get('can') or r.get('isolation'): out.append('')
        rows = []
        for p in procs:
            for task in (p.get('tasks') or []):
                h = task.get('human') or {}
                if h.get('role') != r['id']:
                    continue
                rows.append((task, p, h))
        if rows:
            out.append('| %s | %s | %s | %s |' % (t['t_task'], t['t_proc'], t['t_gate'], t['t_start']))
            out.append('|---|---|---|---|')
            for task, p, h in rows:
                start = t['by_person']
                if task.get('workflow'):
                    w = wfs.get(task['workflow'])
                    names = [trgs[x]['name'] for x in (w.get('triggers') or []) if x in trgs] if w else []
                    start = ' · '.join(names) if names else t['by_person']
                out.append('| %s | %s | %s | %s |' % (
                    esc(task.get('name', task['id'])), esc(p.get('name', p['id'])),
                    t['gate'].get(h.get('gate', ''), esc(h.get('gate'))), esc(start)))
            out.append('')
    out.append(anchor('triggers'))
    out.append('## ' + t['triggers_sec'])
    out.append('')
    if not trgs:
        out.append('_%s_' % t['no_trig']); out.append('')
    else:
        out.append('| %s | %s | %s | %s | %s |' % (
            t['t_trigger'], t['t_type'], t['t_cfg'], t['t_raises'], t['t_moves']))
        out.append('|---|---|---|---|---|')
        for gid in sorted(trgs):
            g = trgs[gid]
            raised = [w for w in (spec.get('workflows') or []) if gid in (w.get('triggers') or [])]
            movers = set()
            for w in raised:
                for p in procs:
                    tids = {x.get('workflow') for x in (p.get('tasks') or [])}
                    if w['id'] not in tids:
                        continue
                    # роль двигается, если в ТОМ ЖЕ процессе у неё есть человеческая задача
                    for task in (p.get('tasks') or []):
                        h = task.get('human') or {}
                        if h.get('role'):
                            movers.add(h['role'])
            cfg = g.get('config') or {}
            cfgs = cfg.get('schedule') or cfg.get('event') or cfg.get('path') or t['none']
            out.append('| %s | %s | %s | %s | %s |' % (
                esc(g.get('name', gid)), esc(g.get('type')), esc(cfgs),
                esc(' · '.join(w.get('name', w['id']) for w in raised) or t['none']),
                esc(' · '.join(sorted(movers)) or t['none'])))
        out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'

# ---------------------------------------------------------------- ARCHITECTURE.md
def render_arch(spec, t, src):
    out = []
    out.append('# ' + t['arch_title'])
    out.append('')
    out.append(anchor('howto'))
    out.append('## ' + t['arch_howto'])
    out.append('')
    out.append(t['arch_howto_body'])
    out.append('')

    out.append(anchor('stack'))
    out.append('## ' + t['stack_sec'])
    out.append('')
    prof = spec.get('profile') or {}
    pats = prof.get('architecture_patterns') or []
    if pats:
        out.append('**patterns:** ' + ' · '.join('`%s`' % p for p in pats))
        out.append('')
    sw = spec.get('software') or []
    if sw:
        out.append('| %s | %s | %s |' % (t['t_soft'], t['t_layers'], t['t_role']))
        out.append('|---|---|---|')
        for s in sw:
            out.append('| `%s` | %s | %s |' % (
                esc(s['id']), esc(' · '.join(s.get('layers') or []) or t['none']),
                esc(s.get('type') or t['none'])))
        out.append('')

    out.append(anchor('entities'))
    out.append('## ' + t['entities_sec'])
    out.append('')
    ents = spec.get('entities') or []
    if ents:
        out.append('| %s | %s | %s |' % (t['t_entity'], t['t_master'], t['t_stores']))
        out.append('|---|---|---|')
        for e in ents:
            stores = ' · '.join('`%s`' % (st.get('software') or '?') for st in (e.get('stores') or []))
            out.append('| `%s` | %s | %s |' % (
                esc(e['id']), esc(e.get('master') or t['none']), stores or t['none']))
        out.append('')

    out.append(anchor('workflows'))
    out.append('## ' + t['wf_sec'])
    out.append('')
    wfs = spec.get('workflows') or []
    if wfs:
        out.append('| %s | %s | %s | %s |' % (t['t_wf'], t['t_engine'], t['t_where'], t['t_status']))
        out.append('|---|---|---|---|')
        for w in wfs:
            out.append('| %s | %s | `%s` | %s |' % (
                esc(w.get('name', w['id'])), esc(w.get('engine') or t['none']),
                esc(w.get('location') or t['none']), esc(w.get('status') or t['none'])))
        out.append('')

    out.append(anchor('integrations'))
    out.append('## ' + t['integ_sec'])
    out.append('')
    ifs = spec.get('interfaces') or []
    if ifs:
        out.append('| %s | %s | %s |' % (t['t_iface'], t['t_type'], t['t_soft']))
        out.append('|---|---|---|')
        for i in ifs:
            out.append('| `%s` | %s | `%s` |' % (
                esc(i['id']), esc(i.get('type') or t['none']), esc(i.get('software') or t['none'])))
        out.append('')
    mcp = ((spec.get('connections') or {}).get('mcp')) or []
    if mcp:
        out.append('**%s:** %s' % (t['t_mcp'], ' · '.join('`%s`' % (m.get('software') or m.get('id')) for m in mcp)))
        out.append('')
    plugins = ((spec.get('context') or {}).get('plugins')) or {}
    flat = []
    if isinstance(plugins, dict):
        for host, lst in plugins.items():
            if isinstance(lst, list):
                for p in lst:
                    flat.append((host, p))
    if flat:
        out.append('| %s | %s |' % (t['t_plugin'], t['t_covers']))
        out.append('|---|---|')
        for host, p in flat:
            name = p.get('name') if isinstance(p, dict) else str(p)
            covers = ' · '.join(p.get('covers') or []) if isinstance(p, dict) else ''
            out.append('| `%s` | %s |' % (esc(name), esc(covers or t['none'])))
        out.append('')
    return '\n'.join(out).rstrip('\n') + '\n'

# ---------------------------------------------------------------- журнал
def split_journal(text, t):
    """Возвращает (тело_без_журнала, [строки_журнала])."""
    a = anchor('journal')
    if a not in text:
        return text, []
    body, _, jr = text.partition(a)
    rows = [ln for ln in jr.split('\n')
            if ln.startswith('|') and not ln.startswith('|---') and t['col_date'] not in ln]
    return body, rows

def with_journal(body, rows, t, src, date, changed):
    if changed:
        rows = rows + ['| %s | %s |' % (date, t['rebuilt'].format(src=src))]
    if not rows:
        rows = ['| %s | %s |' % (date, t['created'])]
    j = [anchor('journal'), '## ' + t['journal_sec'], '',
         '| %s | %s |' % (t['col_date'], t['col_what']), '|---|---|'] + rows
    return body.rstrip('\n') + '\n\n' + '\n'.join(j) + '\n'

# ---------------------------------------------------------------- main
def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    root = args[0] if args else 'macstack'
    check = '--check' in sys.argv
    date = None
    for i, a in enumerate(sys.argv):
        if a == '--date' and i + 1 < len(sys.argv):
            date = sys.argv[i + 1]
    date = date or datetime.date.today().isoformat()

    spec_path = os.path.join(root, 'macstack.json')
    spec = json.load(io.open(spec_path, encoding='utf-8'))
    docs = spec.get('docs') or {}
    lang = docs.get('language') or 'en'
    t = L.get(lang, L['en'])
    src = 'macstack.json'

    targets = [('ROLES.md', render_roles), ('ARCHITECTURE.md', render_arch)]
    rc = 0
    for name, fn in targets:
        path = os.path.join(root, name)
        banner = '<!-- macstack:generated from=%s -->' % src
        docanc = '<!-- macstack:doc=%s lang=%s version=1 -->' % (
            'roles' if name == 'ROLES.md' else 'architecture', lang)
        body = '%s\n%s\n\n> %s\n\n%s' % (docanc, banner, t['banner_note'].format(src=src), fn(spec, t, src))

        old = io.open(path, encoding='utf-8').read() if os.path.exists(path) else ''
        old_body, old_rows = split_journal(old, t)
        changed = old_body.rstrip('\n') != body.rstrip('\n')
        new = with_journal(body, old_rows, t, src, date, changed or not old)

        if check:
            if old != new:
                rc = 1
                print('%s: РАСХОЖДЕНИЕ с источником' % path)
                for ln in list(difflib.unified_diff(old.split('\n'), new.split('\n'),
                                                    'на диске', 'из спеки', lineterm=''))[:12]:
                    print('   ' + ln)
            else:
                print('%s: совпадает' % path)
        else:
            if old != new:
                io.open(path, 'w', encoding='utf-8').write(new)
                print('%s: %s' % (path, 'пересобран' if old else 'создан'))
            else:
                print('%s: без изменений' % path)
    return rc

if __name__ == '__main__':
    sys.exit(main())
