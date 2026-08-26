#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Render the three GENERATED documents of a macstack/ folder. Three documents,
three different sources:

    generated/ARCHITECTURE.md   <- macstack.json                 how it is built
    generated/INDEX.md          <- client/*.md + TEST-CASES.md    the folder's own index
    README.md                   <- doc-contracts.json             the folder's own contract

Deterministic BY DESIGN. Lint rule 12.18 re-renders and compares, so a renderer whose
output varies between runs would make that rule permanently red. Everything here is a
pure function of its source: no timestamps in the body, no dict iteration that depends
on hash order (every grouping key is sorted explicitly before it is walked), no prose
invented at render time.

The ONE exception is the journal: those rows are human history and must survive a
rebuild. They are read back out of the existing file and carried forward. A new row is
appended only when the rendered body actually changed, which is what keeps a second run
byte-identical to the first.

Usage:  render.py <macstack-dir> [--date YYYY-MM-DD] [--check] [--only architecture|index|readme]
        --check   render into memory and report differences without writing (12.18)
"""
import sys, os, io, re, json, datetime, difflib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mdblocks import parse, entities, entity, anchor, doc_header
from i18n import doc_lang, msg, out
import v3                                            # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CONTRACT_PATH = os.path.join(HERE, 'doc-contracts.json')


def load_contract():
    with io.open(CONTRACT_PATH, encoding='utf-8') as f:
        return json.load(f)


def load_spec(root):
    try:
        with io.open(os.path.join(root, 'macstack.json'), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def load_doc(path):
    """Parse an existing markdown document. (header, blocks) — ([], {}) if absent."""
    if not os.path.exists(path):
        return None, []
    with io.open(path, encoding='utf-8') as f:
        return parse(f.read())


def esc(s):
    return str(s).replace('|', '\\|').replace('\n', ' ').strip() if s is not None else ''


def L(table, lang):
    return table.get(lang) or table['en']


def _title(block):
    """A block's heading is '<id> · <title>' — split off the title half."""
    h = block.heading or ''
    return h.split('·', 1)[1].strip() if '·' in h else h


# ---------------------------------------------------------------- prose catalogue
# Headings, one-line explanations and grouping labels, per document. Anchors and
# YAML keys never appear here — only what docs.language governs.
TITLE = {
    'ru': dict(architecture="Архитектура — как здесь строят",
               index="Индекс — кейсы, экраны, триггеры, покрытие",
               readme="Карта папки macstack/"),
    'en': dict(architecture="Architecture — how this is built",
               index="Index — cases, screens, triggers, coverage",
               readme="Map of the macstack/ folder"),
}

HEAD = {
    'ru': dict(howto="Как читать этот документ", stack="Чем собрано",
               entities="Сущности и где они лежат", workflows="Что исполняется",
               integrations="Интеграции и контекст", journal="Журнал документа",
               cases="Кейсы", screens="Экраны", triggers="Триггеры", coverage="Покрытие",
               map="Карта", ownership="Кто чем владеет", idspaces="Пространства id",
               loop="Цикл работы"),
    'en': dict(howto="How to read this", stack="What it is made of",
               entities="Entities and where they live", workflows="What runs",
               integrations="Integrations and context", journal="Document journal",
               cases="Cases", screens="Screens", triggers="Triggers", coverage="Coverage",
               map="Map", ownership="Who owns what", idspaces="ID spaces",
               loop="Working loop"),
}

MISC = {
    'ru': dict(
        banner_note="Собран из `{src}`. Правки руками теряются при следующей сборке — правьте источник.",
        rebuilt="пересобран из `{src}`", created="создан",
        col_date="дата", col_what="что изменилось",
        arch_howto=(
            "Машинная половина спецификации, разложенная для человека и для агента, которому предстоит\n"
            "здесь строить: чем собрано, что хранится и где, что исполняется и в каком файле.\n\n"
            "Этот документ **не заменяет** `../docs/architecture.md`. Там — то, чего в спеке не выразить:\n"
            "измеренные ловушки, аргументы за решения, грабли, на которые уже наступали."),
        patterns="паттерны", no_software="В спецификации нет ни одного software.",
        no_entities="В спецификации нет ни одной сущности.",
        single_master="**master для всех сущностей этого раздела:** `{master}`.",
        master_label="master", status_label="статус",
        no_workflows="В спецификации нет ни одного workflow.",
        mcp_label="MCP-соединения", interfaces_label="Интерфейсы", plugins_label="Плагины",
        no_cases="Пока нет `client/USER-CASES.md` — кейсов нет.",
        no_screens="Пока нет `client/UX-UI.md` — экранов нет.",
        no_triggers="Пока нет `client/AUTOMATION.md` — триггеров нет.",
        no_coverage="Нет кейсов, покрывать нечего.",
        role_col="роль", cases_col="кейсов", acc_col="пунктов приёмки", tests_col="тестов",
        tests_cell="{n} (авто {auto} / вручную {manual}, без теста {open})",
        coverage_line="кейсов: {cases} · пунктов приёмки: {acc} · тестов: {tests} (авто {auto} / вручную {manual}, без теста {open})",
        owned_generated="генерируется из `{source}`",
        owned_derived="сеется из {sources}, дальше ведётся руками",
        owned_authored="авторский документ, аудитория: {audience}",
        loop_lines=[
            "Материал клиента ложится в `inbox/` и получает запись в `history/log.md`.",
            "Анализ становится дельтой в `history/deltas/` — что противоречит, что добавляется.",
            "Дельта разрешается решениями в `history/decisions/` — что принято и почему.",
            "Принятое применяется к `client/*.md`, откуда `render.py` пересобирает генерируемые документы.",
        ],
        value_prose={
            'interface': "Обеспечивает интерфейс — то, через что человек или агент видит систему.",
            'workflows': "Исполняет процессы — то, что двигает данные и запускает действия.",
            'data': "Держит данные — источник фактов для остального стека.",
            'storage': "Хранит и раздаёт — инфраструктурный слой под данными и процессами.",
        },
    ),
    'en': dict(
        banner_note="Generated from `{src}`. Hand edits are lost on the next render — edit the source.",
        rebuilt="rebuilt from `{src}`", created="created",
        col_date="date", col_what="what changed",
        arch_howto=(
            "The machine half of the spec laid out for a human and for the agent that has to build here:\n"
            "what it is made of, what is stored and where, what runs and in which file.\n\n"
            "This does **not** replace `../docs/architecture.md`. That one holds what the spec cannot\n"
            "express — measured traps, the argument behind a decision, the rake already stepped on."),
        patterns="patterns", no_software="The spec declares no software.",
        no_entities="The spec declares no entities.",
        single_master="**master for every entity in this section:** `{master}`.",
        master_label="master", status_label="status",
        no_workflows="The spec declares no workflows.",
        mcp_label="MCP connections", interfaces_label="Interfaces", plugins_label="Plugins",
        no_cases="No `client/USER-CASES.md` yet — no cases.",
        no_screens="No `client/UX-UI.md` yet — no screens.",
        no_triggers="No `client/AUTOMATION.md` yet — no triggers.",
        no_coverage="No cases, nothing to cover.",
        role_col="role", cases_col="cases", acc_col="acceptance bullets", tests_col="tests",
        tests_cell="{n} (auto {auto} / manual {manual}, {open} without a test)",
        coverage_line="cases: {cases} · acceptance bullets: {acc} · tests: {tests} (auto {auto} / manual {manual}, {open} without a test)",
        owned_generated="generated from `{source}`",
        owned_derived="seeded from {sources}, maintained by hand from there",
        owned_authored="authored document, audience: {audience}",
        loop_lines=[
            "Client material lands in `inbox/` and gets an entry in `history/log.md`.",
            "Analysis becomes a delta in `history/deltas/` — what contradicts, what is added.",
            "The delta is resolved by decisions in `history/decisions/` — what was ruled, and why.",
            "What was accepted is applied to `client/*.md`, from which `render.py` rebuilds the generated documents.",
        ],
        value_prose={
            'interface': "Provides the interface — what a person or an agent sees the system through.",
            'workflows': "Runs the processes — what moves data and fires actions.",
            'data': "Holds the data — the source of facts for the rest of the stack.",
            'storage': "Stores and serves — the infrastructure layer under the data and the processes.",
        },
    ),
}


# ---------------------------------------------------------------- ARCHITECTURE.md
def render_architecture(spec, lang):
    h, m = L(HEAD, lang), L(MISC, lang)
    out_lines = ['# ' + L(TITLE, lang)['architecture'], '',
                 anchor('section', 'howto'), '## ' + h['howto'], '', m['arch_howto'], '']

    # ---- stack ----
    out_lines += [anchor('section', 'stack'), '## ' + h['stack'], '']
    patterns = ((spec.get('profile') or {}).get('architecture_patterns')) or []
    if patterns:
        out_lines += ['**%s:** %s' % (m['patterns'], ' · '.join('`%s`' % p for p in patterns)), '']
    software = spec.get('software') or []
    if not software:
        out_lines += ['_%s_' % m['no_software'], '']
    for s in software:
        # dump_yaml lower-cases a top-level bool but not one nested in a dict — pre-stringify
        # so a nested {mcp: true} does not come back out as Python's {mcp: True}.
        agentic = dict((k, ('true' if v is True else 'false' if v is False else v))
                       for k, v in (s.get('agentic') or {}).items())
        yaml_fields = {
            'category': s.get('category'), 'type': s.get('type'),
            'layers': s.get('layers') or [], 'license': s.get('license'),
            'hosting': s.get('hosting'), 'agentic': agentic,
            'role': s.get('role'),
        }
        fields = []
        if s.get('value'):
            prose = m['value_prose'].get(s['value'], s['value'])
            fields.append(('role', None, [prose]))
        out_lines.append(entity('software', s['id'], s.get('name', s['id']), yaml_fields, fields))

    # ---- entities ----
    out_lines += [anchor('section', 'entities'), '## ' + h['entities'], '']
    ents = spec.get('entities') or []
    if not ents:
        out_lines += ['_%s_' % m['no_entities'], '']
    else:
        masters = sorted(set(e.get('master') for e in ents))
        single_master = masters[0] if len(masters) == 1 else None
        if single_master:
            out_lines += [m['single_master'].format(master=single_master), '']
            for e in ents:
                yaml_fields = {'stores': [st.get('software') for st in (e.get('stores') or [])],
                                'volume': e.get('volume')}
                out_lines.append(entity('entity', e['id'], e.get('name', e['id']), yaml_fields, []))
        else:
            by_master = {}
            for e in ents:
                by_master.setdefault(e.get('master') or '', []).append(e)
            for master in sorted(by_master):
                out_lines += ['**%s:** `%s`' % (m['master_label'], master or '—'), '']
                for e in by_master[master]:
                    yaml_fields = {'master': e.get('master'),
                                    'stores': [st.get('software') for st in (e.get('stores') or [])],
                                    'volume': e.get('volume')}
                    out_lines.append(entity('entity', e['id'], e.get('name', e['id']), yaml_fields, []))

    # ---- workflows ----
    out_lines += [anchor('section', 'workflows'), '## ' + h['workflows'], '']
    wfs = spec.get('workflows') or []
    if not wfs:
        out_lines += ['_%s_' % m['no_workflows'], '']
    else:
        by_status = {}
        for w in wfs:
            by_status.setdefault(w.get('status') or '', []).append(w)
        for status in sorted(by_status):
            out_lines += ['**%s:** `%s`' % (m['status_label'], status or '—'), '']
            for w in by_status[status]:
                yaml_fields = {
                    'engine': w.get('engine'), 'triggers': w.get('triggers') or [],
                    'invocation': w.get('invocation') or [], 'implements': w.get('implements'),
                    'location': w.get('location'),
                }
                out_lines.append(entity('workflow', w['id'], w.get('name', w['id']), yaml_fields, []))

    # ---- integrations ----
    out_lines += [anchor('section', 'integrations'), '## ' + h['integrations'], '']
    mcp = ((spec.get('connections') or {}).get('mcp')) or []
    if mcp:
        out_lines += ['**%s**' % m['mcp_label'], '']
        for c in mcp:
            out_lines.append('- `%s`' % esc(c.get('software') or c.get('id')))
        out_lines.append('')
    ifs = spec.get('interfaces') or []
    if ifs:
        out_lines += ['**%s**' % m['interfaces_label'], '']
        for i in ifs:
            out_lines.append('- `%s` — %s' % (esc(i['id']), esc(i.get('type') or '—')))
        out_lines.append('')
    plugins = ((spec.get('context') or {}).get('plugins')) or {}
    flat = []
    if isinstance(plugins, dict):
        for host in sorted(plugins):
            lst = plugins[host]
            if isinstance(lst, list):
                for p in lst:
                    flat.append((host, p))
    if flat:
        out_lines += ['**%s**' % m['plugins_label'], '']
        for host, p in flat:
            name = p.get('name') if isinstance(p, dict) else str(p)
            covers = ' · '.join(p.get('covers') or []) if isinstance(p, dict) else ''
            out_lines.append('- `%s` (%s) — %s' % (esc(name), esc(host), esc(covers or '—')))
        out_lines.append('')

    return '\n'.join(out_lines).rstrip('\n') + '\n'


# ---------------------------------------------------------------- INDEX.md
def render_index(root, lang):
    """Оглавление: все кейсы, экраны и триггеры плюс счёт покрытия.

    Читает КЛИЕНТСКИЕ документы в формате v3 — заголовки и списки. v2-читатель искал
    здесь якоря сущностей и, когда их убрали, молча отдал пустой указатель: пять
    разделов по нулю пунктов, и ни одной ошибки. Отсюда правило: генератор, не нашедший
    ни одного элемента там, где документ не пуст, обязан сказать об этом вслух.
    """
    h, m = L(HEAD, lang), L(MISC, lang)
    out_lines = ['# ' + L(TITLE, lang)['index'], '']

    cases = [i for i in v3.load(os.path.join(root, 'client', 'USER-CASES.md'), lang) if i.id]
    screens = [i for i in v3.load(os.path.join(root, 'client', 'UX-UI.md'), lang)
               if i.id and (i.ref or '').startswith('interfaces[')]
    triggers = [i for i in v3.load(os.path.join(root, 'client', 'AUTOMATION.md'), lang)
                if i.id and (i.ref or '').startswith('triggers[id=')]
    tests = [i for i in v3.load(os.path.join(root, 'generated', 'TEST-CASES.md'), lang) if i.id]

    # ---- кейсы, сгруппированные по разделу документа ----
    out_lines += ['## ' + h['cases'], '']
    if not cases:
        out_lines += ['_%s_' % m['no_cases'], '']
    else:
        by_sec = []
        for c in cases:
            key = c.section or '—'
            if not by_sec or by_sec[-1][0] != key:
                by_sec.append((key, []))
            by_sec[-1][1].append(c)
        for sec, items in by_sec:
            out_lines += ['**%s**' % esc(sec), '']
            for c in items:
                prio = c.get('priority')
                out_lines.append('- **%s** · %s%s' % (
                    c.id, esc(c.title or ''), (' — `%s`' % esc(prio)) if prio else ''))
            out_lines.append('')

    # ---- экраны ----
    out_lines += ['## ' + h['screens'], '']
    if not screens:
        out_lines += ['_%s_' % m['no_screens'], '']
    else:
        for sc in sorted(screens, key=lambda b: b.id):
            path = sc.get('path')
            roles = sc.get('roles')
            roles_s = ', '.join(roles) if isinstance(roles, list) else (roles or '')
            out_lines.append('- **%s** · %s%s%s' % (
                sc.id, esc(sc.title or ''),
                (' — `%s`' % esc(str(path))) if path else '',
                (' (%s)' % esc(str(roles_s))) if roles_s else ''))
        out_lines.append('')

    # ---- триггеры ----
    out_lines += ['## ' + h['triggers'], '']
    if not triggers:
        out_lines += ['_%s_' % m['no_triggers'], '']
    else:
        for tg in sorted(triggers, key=lambda b: b.id):
            bits = [x for x in (tg.get('type'), tg.get('source')) if x]
            raises = tg.get('raises')
            out_lines.append('- **%s** · %s%s%s' % (
                tg.id, esc(tg.title or ''),
                (' — %s' % esc(' / '.join(str(b) for b in bits))) if bits else '',
                (' — %s' % esc(str(raises))) if raises else ''))
        out_lines.append('')

    # ---- покрытие ----
    out_lines += ['## ' + h['coverage'], '']
    if not cases:
        out_lines += ['_%s_' % m['no_coverage'], '']
    else:
        out_lines += _coverage_v3(cases, tests, lang)

    return '\n'.join(out_lines).rstrip('\n') + '\n'


def _coverage_v3(cases, tests, lang):
    """Счёт покрытия списком: пунктов приёмки против тестов, по разделам документа."""
    m = L(MISC, lang)
    covered = set()
    for t in tests:
        cov = t.get('covers')
        for aid in (cov if isinstance(cov, list) else ([cov] if cov else [])):
            covered.add(str(aid))
    per = []
    for c in cases:
        key = c.section or '—'
        bullets = 0
        for label, body in c.sections.items():
            if any(w in label.lower() for w in ('готово', 'done when', 'acceptance')):
                bullets = sum(1 for ln in body if ln.strip().startswith('-'))
        ids = ['%s.a%d' % (c.id, i + 1) for i in range(bullets)]
        if not per or per[-1][0] != key:
            per.append([key, 0, 0, 0])
        per[-1][1] += 1
        per[-1][2] += len(ids)
        per[-1][3] += sum(1 for a in ids if a in covered)
    lines = []
    for key, n_cases, n_acc, n_cov in per:
        gap = n_acc - n_cov
        lines.append('- **%s** — кейсов %d, пунктов приёмки %d, покрыто тестами %d%s'
                     % (esc(key), n_cases, n_acc, n_cov,
                        (', без теста %d' % gap) if gap else ''))
    lines.append('')
    return lines


def _coverage(cases, tests, lang):
    m = L(MISC, lang)
    per_role = {}
    for c in cases:
        role = c.yaml.get('role') or ''
        acc = c.field('acceptance')
        bullets = [ln for ln in (acc.body if acc is not None else []) if ln.strip().startswith('-')]
        ids = ['%s.a%d' % (c.id, i + 1) for i in range(len(bullets))]
        d = per_role.setdefault(role, {'cases': 0, 'acc_ids': []})
        d['cases'] += 1
        d['acc_ids'].extend(ids)

    covers_map = {}
    for t in tests:
        covers = t.yaml.get('covers')
        covers = covers if isinstance(covers, list) else ([covers] if covers else [])
        for aid in covers:
            covers_map.setdefault(aid, []).append(t.yaml.get('kind'))

    rows = []
    for role in sorted(per_role):
        d = per_role[role]
        auto = manual = open_n = 0
        for aid in d['acc_ids']:
            kinds = covers_map.get(aid) or []
            if not kinds:
                open_n += 1
            else:
                auto += sum(1 for k in kinds if k == 'auto')
                manual += sum(1 for k in kinds if k == 'manual')
        rows.append((role or '—', d['cases'], len(d['acc_ids']), auto + manual, auto, manual, open_n))

    lines = []
    if len(rows) >= 3:
        lines.append('| %s | %s | %s | %s |' % (m['role_col'], m['cases_col'], m['acc_col'], m['tests_col']))
        lines.append('|---|---|---|---|')
        for role, n_cases, acc_n, tests_n, auto, manual, open_n in rows:
            cell = m['tests_cell'].format(n=tests_n, auto=auto, manual=manual, open=open_n)
            lines.append('| %s | %s | %s | %s |' % (esc(role), n_cases, acc_n, cell))
        lines.append('')
    else:
        for role, n_cases, acc_n, tests_n, auto, manual, open_n in rows:
            lines.append('- **%s** · %s' % (esc(role), m['coverage_line'].format(
                cases=n_cases, acc=acc_n, tests=tests_n, auto=auto, manual=manual, open=open_n)))
        lines.append('')
    return lines


# ---------------------------------------------------------------- README.md
def _first_sentence(text):
    text = (text or '').strip()
    if not text:
        return ''
    idx = text.find('. ')
    return text[:idx + 1] if idx != -1 else text.split('\n')[0]


def render_readme(contract, lang):
    h, m = L(HEAD, lang), L(MISC, lang)
    docs = contract.get('documents') or {}
    dirs = contract.get('dirs') or {}
    id_spaces = contract.get('id_spaces') or {}

    out_lines = ['# ' + L(TITLE, lang)['readme'], '']

    # ---- map ----
    out_lines += [anchor('section', 'map'), '## ' + h['map'], '']
    root_docs = [(k, d) for k, d in docs.items() if '/' not in d.get('path', '')]
    for key, d in sorted(root_docs, key=lambda kv: kv[1]['path']):
        out_lines.append('- **%s** — %s' % (d['path'], esc(_first_sentence(d.get('note')))))
    for dirname in sorted(dirs):
        if dirname.startswith('_'):
            continue
        out_lines.append('- **%s/** — %s' % (dirname, esc(_first_sentence(dirs[dirname]))))
        entries = [(k, d) for k, d in docs.items() if d.get('path', '').startswith(dirname + '/')]
        for key, d in sorted(entries, key=lambda kv: kv[1]['path']):
            out_lines.append('  - `%s` — %s' % (d['path'], esc(_first_sentence(d.get('note')))))
    out_lines.append('')

    # ---- ownership ----
    out_lines += [anchor('section', 'ownership'), '## ' + h['ownership'], '']
    for key, d in sorted(docs.items(), key=lambda kv: kv[1]['path']):
        if d.get('generated'):
            line = m['owned_generated'].format(source=d['generated'])
        elif d.get('derived_from'):
            line = m['owned_derived'].format(sources=', '.join(d['derived_from']))
        else:
            line = m['owned_authored'].format(audience=d.get('audience', '—'))
        out_lines.append('- **%s** — %s' % (d['path'], line))
    out_lines.append('')

    # ---- idspaces ----
    out_lines += [anchor('section', 'idspaces'), '## ' + h['idspaces'], '']
    for space in sorted(id_spaces):
        info = id_spaces[space]
        out_lines.append('- **%s** — `%s` — %s' % (space, info.get('pattern', ''), info.get('owner', '')))
    out_lines.append('')

    # ---- loop ----
    out_lines += [anchor('section', 'loop'), '## ' + h['loop'], '']
    for i, line in enumerate(m['loop_lines'], 1):
        out_lines.append('%d. %s' % (i, line))
    out_lines.append('')

    return '\n'.join(out_lines).rstrip('\n') + '\n'


# ---------------------------------------------------------------- journal
# Журнал — список, а не таблица. Строка v2-формата ещё читается, чтобы история,
# написанная до перехода, не пропала при первой же пересборке.
JOURNAL_ROW = re.compile(r'^\|\s*(\d{4}-\d{2}-\d{2})\s*\|\s*(.+?)\s*\|\s*$')
JOURNAL_ITEM = re.compile(r'^-\s+\*\*(\d{4}-\d{2}-\d{2})\*\*\s+—\s+(.+?)\s*$')


def split_journal(text):
    """Тело документа и строки журнала: (date, what)."""
    head = None
    for cand in ('## ' + L(HEAD, 'ru')['journal'], '## ' + L(HEAD, 'en')['journal'],
                 anchor('section', 'journal')):
        if cand in text:
            head = cand
            break
    if head is None:
        return text, []
    body, _, jr = text.partition(head)
    rows = []
    for ln in jr.split('\n'):
        m = JOURNAL_ROW.match(ln) or JOURNAL_ITEM.match(ln)
        if m:
            item = (m.group(1), m.group(2).strip())
            # «пересобран из client/*.md» пять раз подряд — это не история,
            # это шум от пяти прогонов. Подряд идущие одинаковые схлопываются.
            if rows and rows[-1][1] == item[1]:
                rows[-1] = item
                continue
            rows.append(item)
    return body, rows


def with_journal(body, rows, lang, date, changed, seed_text):
    m = L(MISC, lang)
    if changed:
        # одна и та же запись подряд ничего не сообщает: пять «пересобран из
        # client/*.md» в живом документе появились ровно так
        if not rows or rows[-1][1] != seed_text:
            rows = rows + [(date, seed_text)]
        else:
            rows = rows[:-1] + [(date, seed_text)]
    if not rows:
        rows = [(date, m['created'])]
    j = ['## ' + L(HEAD, lang)['journal'], '']
    j += ['- **%s** — %s' % (d, w) for d, w in rows]
    return body.rstrip('\n') + '\n\n' + '\n'.join(j) + '\n'


def build_full(doc_key, lang, src, body):
    header = doc_header(doc_key, lang, 1)
    banner = '<!-- macstack:generated from=%s -->' % src
    note = '> ' + L(MISC, lang)['banner_note'].format(src=src)
    return '%s\n%s\n\n%s\n\n%s' % (header, banner, note, body)


# ---------------------------------------------------------------- main
def main():
    argv = sys.argv[1:]
    check = '--check' in argv
    date, only = None, None
    positional = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == '--date' and i + 1 < len(argv):
            date = argv[i + 1]; i += 2; continue
        if a == '--only' and i + 1 < len(argv):
            only = argv[i + 1]; i += 2; continue
        if a == '--check':
            i += 1; continue
        positional.append(a); i += 1
    root = positional[0] if positional else 'macstack'
    date = date or datetime.date.today().isoformat()

    lang = doc_lang(root)
    contract = load_contract()
    spec = load_spec(root)
    if not spec and only in (None, 'architecture'):
        out(lang, 'no_spec', dir=root)

    jobs = []
    if only in (None, 'architecture'):
        jobs.append(('architecture', os.path.join('generated', 'ARCHITECTURE.md'), 'macstack.json',
                      render_architecture(spec, lang)))
    if only in (None, 'index'):
        jobs.append(('index', os.path.join('generated', 'INDEX.md'), 'client/*.md',
                      render_index(root, lang)))
    if only in (None, 'readme'):
        jobs.append(('readme', 'README.md', 'doc-contracts.json', render_readme(contract, lang)))

    rc = 0
    for key, relpath, src, body in jobs:
        path = os.path.join(root, relpath)
        full = build_full(key, lang, src, body)

        old = ''
        if os.path.exists(path):
            with io.open(path, encoding='utf-8') as f:
                old = f.read()
        old_body, old_rows = split_journal(old)
        changed = old_body.rstrip('\n') != full.rstrip('\n')
        seed_text = L(MISC, lang)['rebuilt'].format(src=src)
        new = with_journal(full, old_rows, lang, date, changed or not old, seed_text)

        if check:
            if old != new:
                rc = 1
                out(lang, 'drift', path=path)
                print('  ' + msg(lang, 'drift_hint'))
                for ln in list(difflib.unified_diff(old.split('\n'), new.split('\n'),
                                                      'disk', 'spec', lineterm=''))[:12]:
                    print('   ' + ln)
            else:
                out(lang, 'in_sync', path=path)
        else:
            os.makedirs(os.path.dirname(path) or '.', exist_ok=True)
            if old != new:
                with io.open(path, 'w', encoding='utf-8') as f:
                    f.write(new)
                out(lang, 'wrote', path=path)
            else:
                out(lang, 'unchanged', path=path)
    return rc


if __name__ == '__main__':
    sys.exit(main())
