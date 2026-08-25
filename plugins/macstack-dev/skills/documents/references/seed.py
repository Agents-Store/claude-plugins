#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Seed the three AUTHORED client documents once, from macstack.json.

client/AUTOMATION.md, client/UX-UI.md and client/HANDBOOK.md are written by a human
and read by the client — they are a SOURCE of the spec's business half, not its
output (invariant 9). But a blank page is a bad start when the spec already knows the
roles, the tasks, the triggers and the interfaces, so this seeds a FIRST v2-format
version of each and then never touches them again.

REFUSES to overwrite. If the file exists, say so and stop: overwriting an authored
document with a machine guess is how a client's correction disappears. `--force`
replaces it anyway with a fresh seed (used to reseed, never as the normal path).

Usage: seed.py <macstack-dir> [--force] [--date YYYY-MM-DD] [--only automation|ux-ui|handbook]
"""
import sys, os, io, json, datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mdblocks import parse, entities, entity, anchor, doc_header
from i18n import doc_lang, msg, out


def load_spec(root):
    try:
        with io.open(os.path.join(root, 'macstack.json'), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def L(table, lang):
    return table.get(lang) or table['en']


def _title(block):
    h = block.heading or ''
    return h.split('·', 1)[1].strip() if '·' in h else h


# ---------------------------------------------------------------- prose catalogue
TITLE = {
    'ru': dict(automation="Автоматизация — роли, задачи, триггеры",
               ux_ui="Интерфейс — что видно и чего быть не должно",
               handbook="Справочник — как работать с платформой"),
    'en': dict(automation="Automation — roles, tasks, triggers",
               ux_ui="Interface — what is visible and what must not be",
               handbook="Handbook — how to work with the platform"),
}

HEAD = {
    'ru': dict(howto="Как читать и как править", roles="Роли", tasks="Задачи",
               triggers="Триггеры", journal="Журнал документа",
               principles="Принципы", navigation="Навигация", states="Пустое, загрузка, ошибка",
               responsive="Адаптивность", accessibility="Доступность", tone="Тон",
               screens="Экраны", start="С чего начать", procedures="Процедуры",
               problems="Частые проблемы", glossary="Термины"),
    'en': dict(howto="How to read and how to edit", roles="Roles", tasks="Tasks",
               triggers="Triggers", journal="Document journal",
               principles="Principles", navigation="Navigation", states="Empty, loading, error",
               responsive="Responsive", accessibility="Accessibility", tone="Tone",
               screens="Screens", start="Where to start", procedures="Procedures",
               problems="Common problems", glossary="Terms"),
}

MISC = {
    'ru': dict(
        col_version="версия", col_date="дата", col_what="что изменилось", col_source="источник",
        seeded="заготовка собрана из `macstack.json`; дальше документ ведётся руками",
        automation_howto=(
            "**Этот документ пишете вы, а не платформа.** Из него собирается бизнес-половина\n"
            "спецификации: какие есть роли, какие у них задачи, что эти задачи запускает и какой\n"
            "процесс на это отвечает. Заготовка ниже собрана из `macstack.json`; правьте её как свой\n"
            "текст — она больше не пересобирается."),
        no_roles="В спецификации нет ни одной роли.", no_tasks="В спецификации нет ни одной задачи.",
        no_triggers="В спецификации нет ни одного триггера.",
        sees_label="Что видит", can_label="Что может",
        flow_label="Как это проходит",
        flow_hint="_Опишите шаги: кто и что делает от начала до конца этой задачи._",
        what_happens_label="Что при этом происходит",
        what_happens_hint="_Опишите, что видит роль, чья задача сдвигается, когда этот триггер срабатывает._",
        ux_howto=(
            "**Этот документ пишете вы.** Сквозные разделы ниже применяются к каждому экрану и\n"
            "пишутся один раз. Последняя секция каждого экрана — самая важная: там написано, чего на\n"
            "этом экране быть НЕ должно."),
        principles_hint="_Опишите 3-5 принципов интерфейса этого продукта._",
        navigation_hint="_Опишите, как человек попадает с экрана на экран._",
        states_hint="_Опишите пустое, загрузочное и ошибочное состояние — что видно и что делать._",
        responsive_hint="_Опишите поведение на узком и широком экране._",
        accessibility_hint="_Опишите требования доступности: контраст, клавиатура, читалки экрана._",
        tone_hint="_Опишите тон текста интерфейса: формальность, обращение, длина сообщений._",
        no_screens="Подходящих интерфейсов в спецификации нет.",
        content_label="Что на экране", content_hint="_Опишите, что видно на этом экране._",
        actions_label="Что можно сделать", actions_hint="_Опишите доступные действия._",
        forbidden_label="Чего здесь быть не должно", forbidden_hint="_Опишите, что запрещено показывать здесь._",
        handbook_howto=(
            "**Этот документ пишете вы**, для человека, который будет работать с платформой изо дня\n"
            "в день — не для того, кто её заказал. Заготовки процедур ниже собраны из критичных\n"
            "кейсов `client/USER-CASES.md`, если он уже существует."),
        start_hint="_Опишите первый вход: что человек видит и делает в первые пять минут._",
        see_automation="определение роли — в `AUTOMATION.md`",
        no_procedures="Нет `client/USER-CASES.md`, либо в нём нет критичных кейсов — заготовок нет.",
        steps_label="Шаги", steps_hint="_Опишите шаги от начала до конца этой процедуры._",
        problems_hint="_Опишите частые проблемы и что с ними делать._",
        glossary_hint="_Соберите термины, которые встречаются в интерфейсе, в одном месте._",
    ),
    'en': dict(
        col_version="version", col_date="date", col_what="what changed", col_source="source",
        seeded="seeded from `macstack.json`; from here the document is maintained by hand",
        automation_howto=(
            "**You write this document, not the platform.** It builds the business half of the\n"
            "specification: which roles exist, what their tasks are, what starts each one, and which\n"
            "process answers. The seed below is built from `macstack.json`; edit it as your own text —\n"
            "it is never regenerated again."),
        no_roles="The spec declares no roles.", no_tasks="The spec declares no tasks.",
        no_triggers="The spec declares no triggers.",
        sees_label="Sees", can_label="Can",
        flow_label="How it runs",
        flow_hint="_Describe the steps: who does what, start to finish, for this task._",
        what_happens_label="What happens",
        what_happens_hint="_Describe what the role whose task moves sees when this trigger fires._",
        ux_howto=(
            "**You write this document.** The cross-cutting sections below apply to every screen and\n"
            "are written once. The last section of each screen is the important one: it says what must\n"
            "NOT be visible there."),
        principles_hint="_Describe 3-5 interface principles for this product._",
        navigation_hint="_Describe how a person moves from screen to screen._",
        states_hint="_Describe the empty, loading and error state — what is visible and what to do._",
        responsive_hint="_Describe behaviour at a narrow and a wide viewport._",
        accessibility_hint="_Describe accessibility requirements: contrast, keyboard, screen readers._",
        tone_hint="_Describe the tone of the interface text: formality, address, message length._",
        no_screens="No matching interfaces in the spec.",
        content_label="What is on this screen", content_hint="_Describe what is visible here._",
        actions_label="What can be done", actions_hint="_Describe the actions available._",
        forbidden_label="What must NOT be visible", forbidden_hint="_Describe what is forbidden here._",
        handbook_howto=(
            "**You write this document**, for the person who will use the platform day to day — not\n"
            "for the person who commissioned it. The procedure seeds below are built from the critical\n"
            "cases in `client/USER-CASES.md`, if it already exists."),
        start_hint="_Describe the first login: what a person sees and does in the first five minutes._",
        see_automation="role definition lives in `AUTOMATION.md`",
        no_procedures="No `client/USER-CASES.md`, or it has no critical cases — nothing seeded.",
        steps_label="Steps", steps_hint="_Describe the steps, start to finish, for this procedure._",
        problems_hint="_Describe common problems and what to do about them._",
        glossary_hint="_Collect the terms that appear in the interface, in one place._",
    ),
}

SOURCE_BY_TYPE = {'schedule': 'schedule', 'form': 'interface', 'webhook': 'integration',
                   'db_event': 'backend', 'manual': 'manual'}
CFG_PRIORITY = ('schedule', 'entity', 'event', 'condition', 'path', 'form', 'queue')
SCREENISH = {'web', 'admin_ui', 'dashboard', 'approval_center', 'form'}


def trigger_source(trg):
    return SOURCE_BY_TYPE.get(trg.get('type'))


def trigger_cfg(trg):
    cfg = trg.get('config') or {}
    for key in CFG_PRIORITY:
        if cfg.get(key) is not None:
            return key, cfg[key]
    return None, None


def raises_of(trigger_id, workflows):
    return [w['id'] for w in workflows if trigger_id in (w.get('triggers') or [])]


# ---------------------------------------------------------------- client/AUTOMATION.md
def seed_automation(spec, lang):
    h, m = L(HEAD, lang), L(MISC, lang)
    out_lines = [anchor('section', 'howto'), '## ' + h['howto'], '', m['automation_howto'], '']

    out_lines += [anchor('section', 'roles'), '## ' + h['roles'], '']
    roles = spec.get('roles') or []
    if not roles:
        out_lines += ['_%s_' % m['no_roles'], '']
    for r in roles:
        yaml_fields = {'cases': r.get('cases') or [], 'isolation': r.get('isolation')}
        fields = []
        if r.get('sees'):
            fields.append(('sees', m['sees_label'], [r['sees']]))
        if r.get('can'):
            fields.append(('can', m['can_label'], [r['can']]))
        out_lines.append(entity('role', r['id'], r.get('name', r['id']), yaml_fields, fields))

    out_lines += [anchor('section', 'tasks'), '## ' + h['tasks'], '']
    procs = spec.get('processes') or []
    wfs = {w['id']: w for w in (spec.get('workflows') or [])}
    any_task = False
    for p in procs:
        for task in (p.get('tasks') or []):
            any_task = True
            human = task.get('human') or {}
            wf = wfs.get(task.get('workflow'))
            trig = (wf.get('triggers') or []) if wf else []
            yaml_fields = {
                'role': human.get('role'),
                'gate': human.get('gate') or ('none' if task.get('workflow') else None),
                'trigger': (trig[0] if len(trig) == 1 else trig) if trig else None,
                'workflow': task.get('workflow'),
                'process': p.get('id'),
            }
            fields = [('flow', m['flow_label'], [m['flow_hint']])]
            out_lines.append(entity('task', task['id'], task.get('name', task['id']), yaml_fields, fields))
    if not any_task:
        out_lines += ['_%s_' % m['no_tasks'], '']

    out_lines += [anchor('section', 'triggers'), '## ' + h['triggers'], '']
    trgs = spec.get('triggers') or []
    workflows = spec.get('workflows') or []
    if not trgs:
        out_lines += ['_%s_' % m['no_triggers'], '']
    for g in trgs:
        cfg_key, cfg_val = trigger_cfg(g)
        yaml_fields = {'type': g.get('type'), 'source': trigger_source(g)}
        if cfg_key:
            yaml_fields[cfg_key] = cfg_val
        yaml_fields['raises'] = raises_of(g['id'], workflows)
        fields = [('what_happens', m['what_happens_label'], [m['what_happens_hint']])]
        out_lines.append(entity('trigger', g['id'], g.get('name', g['id']), yaml_fields, fields))

    return '\n'.join(out_lines).rstrip('\n') + '\n'


# ---------------------------------------------------------------- client/UX-UI.md
def seed_ux_ui(spec, lang):
    h, m = L(HEAD, lang), L(MISC, lang)
    out_lines = [anchor('section', 'howto'), '## ' + h['howto'], '', m['ux_howto'], '']
    for key in ('principles', 'navigation', 'states', 'responsive', 'accessibility', 'tone'):
        out_lines += [anchor('section', key), '## ' + h[key], '', m['%s_hint' % key], '']

    out_lines += [anchor('section', 'screens'), '## ' + h['screens'], '']
    ifs = spec.get('interfaces') or []
    screens = [i for i in ifs if i.get('type') in SCREENISH
               and (not i.get('mode') or i.get('mode') == 'ui')
               and (i.get('audience') in (None, 'human'))]
    if not screens:
        out_lines += ['_%s_' % m['no_screens'], '']
    for i in screens:
        yaml_fields = {'path': i.get('path'), 'roles': i.get('roles') or []}
        fields = [
            ('content', m['content_label'], [m['content_hint']]),
            ('actions', m['actions_label'], [m['actions_hint']]),
            ('forbidden', m['forbidden_label'], [m['forbidden_hint']]),
        ]
        out_lines.append(entity('screen', i['id'], i.get('name', i['id']), yaml_fields, fields))

    return '\n'.join(out_lines).rstrip('\n') + '\n'


# ---------------------------------------------------------------- client/HANDBOOK.md
def seed_handbook(spec, root, lang):
    h, m = L(HEAD, lang), L(MISC, lang)
    out_lines = [anchor('section', 'howto'), '## ' + h['howto'], '', m['handbook_howto'], '']
    out_lines += [anchor('section', 'start'), '## ' + h['start'], '', m['start_hint'], '']

    roles = spec.get('roles') or []
    out_lines += [anchor('section', 'roles'), '## ' + h['roles'], '']
    if not roles:
        out_lines += ['_%s_' % m['no_roles'], '']
    for r in roles:
        out_lines.append('- **%s** — %s' % (r['id'], m['see_automation']))
    out_lines.append('')

    out_lines += [anchor('section', 'procedures'), '## ' + h['procedures'], '']
    uc_path = os.path.join(root, 'client', 'USER-CASES.md')
    critical_by_role = {}
    if os.path.exists(uc_path):
        with io.open(uc_path, encoding='utf-8') as f:
            _, blocks = parse(f.read())
        for c in entities(blocks, 'case'):
            if (c.yaml.get('priority') or '') == 'critical':
                critical_by_role.setdefault(c.yaml.get('role') or '', []).append(c)
    if not critical_by_role:
        out_lines += ['_%s_' % m['no_procedures'], '']
    else:
        for role in sorted(critical_by_role):
            for c in sorted(critical_by_role[role], key=lambda b: b.id):
                slug = '%s-%s' % (role, c.id.lower())
                yaml_fields = {'role': role, 'screens': c.yaml.get('screens') or [],
                                'cases': [c.id], 'frequency': None}
                fields = [('steps', m['steps_label'], [m['steps_hint']])]
                out_lines.append(entity('procedure', slug, _title(c), yaml_fields, fields))

    out_lines += [anchor('section', 'problems'), '## ' + h['problems'], '', m['problems_hint'], '']
    out_lines += [anchor('section', 'glossary'), '## ' + h['glossary'], '', m['glossary_hint'], '']

    return '\n'.join(out_lines).rstrip('\n') + '\n'


# ---------------------------------------------------------------- assembly
def seed_journal(lang, date):
    m = L(MISC, lang)
    row = '| %s | %s | %s | %s |' % ('1.0', date, m['seeded'], 'seed')
    return '\n'.join([
        anchor('section', 'journal'), '## ' + L(HEAD, lang)['journal'], '',
        '| %s | %s | %s | %s |' % (m['col_version'], m['col_date'], m['col_what'], m['col_source']),
        '|---|---|---|---|', row, ''])


def build_full(doc_key, lang, date, body):
    header = doc_header(doc_key, lang, '1.0')
    title = '# ' + L(TITLE, lang)[doc_key]
    return header + '\n' + title + '\n\n' + body.rstrip('\n') + '\n\n' + seed_journal(lang, date)


# ---------------------------------------------------------------- main
def main():
    argv = sys.argv[1:]
    force = '--force' in argv
    date, only = None, None
    positional = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--date' and i + 1 < len(argv):
            date = argv[i + 1]; i += 2; continue
        if a == '--only' and i + 1 < len(argv):
            only = argv[i + 1]; i += 2; continue
        if a == '--force':
            i += 1; continue
        positional.append(a); i += 1
    root = positional[0] if positional else 'macstack'
    date = date or datetime.date.today().isoformat()

    spec = load_spec(root)
    lang = doc_lang(root)
    os.makedirs(os.path.join(root, 'client'), exist_ok=True)

    jobs = []
    if only in (None, 'automation'):
        jobs.append(('automation', 'AUTOMATION.md', lambda: seed_automation(spec, lang)))
    if only in (None, 'ux-ui'):
        jobs.append(('ux_ui', 'UX-UI.md', lambda: seed_ux_ui(spec, lang)))
    if only in (None, 'handbook'):
        jobs.append(('handbook', 'HANDBOOK.md', lambda: seed_handbook(spec, root, lang)))

    rc = 0
    for doc_key, filename, fn in jobs:
        path = os.path.join(root, 'client', filename)
        if os.path.exists(path) and not force:
            out(lang, 'refuse_exists', path=path)
            rc = 1
            continue
        body = build_full(doc_key, lang, date, fn())
        with io.open(path, 'w', encoding='utf-8') as f:
            f.write(body)
        out(lang, 'wrote', path=path)
    return rc


if __name__ == '__main__':
    sys.exit(main())
