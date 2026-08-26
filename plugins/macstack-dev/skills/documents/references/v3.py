#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reader for the v3 client-document format: headings and lists, nothing else.

v2 put the machine fields in a fenced yaml block under each heading. That made the
parser trivial and the document unreadable — the owner's verdict on the first real one
was that markdown, yaml and tables had been stirred into porridge, and that a client
cannot tell what is safe to edit.

v3 has none of it. A client document is headings and bullet lists, plus ONE comment line
above the document and one above each entity naming where the same data sits in
macstack.json:

    <!-- macstack:ref=triggers[id=trg-week-close] -->
    ### Закрытие полумесячного периода — `trg-week-close`

    - **Что это за событие:** расписание
    - **Кто его создаёт:** часы, по расписанию

    **Что происходит.** 1-го и 16-го платформа собирает период…

So the reader matches bullet labels through a per-language table. That is the price of
a document a human will actually correct, and it is the right price: the labels are
few, they are declared here, and a project writing in German gets German labels rather
than a document nobody edits.
"""
import re, io

DOC_HEADER = re.compile(r'^<!--\s*macstack:doc=(\S+)\s+lang=(\S+)\s+version=(\S+)\s*-->')
REF = re.compile(r'^<!--\s*macstack:ref=(.+?)\s*-->\s*$')
HEADING = re.compile(r'^(#{1,6})\s+(.*?)\s*$')
BULLET = re.compile(r'^\s*[-*]\s+\*\*(.+?):\*\*\s*(.*)$')
PROSE = re.compile(r'^\*\*(.+?)[.:]?\*\*\s*(.*)$')

# Заголовок в списке -> машинное имя поля. Ключи ASCII, подписи по языкам.
LABELS = {
 'ru': {u'кто': 'role', u'кто видит': 'roles', u'насколько важно': 'priority',
        u'экраны': 'screens', u'триггеры': 'triggers', u'триггер': 'trigger',
        u'workflow': 'workflow', u'адрес': 'path', u'кейсы': 'cases',
        u'что требуется от человека': 'gate', u'процесс': 'process',
        u'что это за событие': 'type', u'кто его создаёт': 'source',
        u'когда срабатывает': 'schedule', u'что поднимает': 'raises',
        u'за чем следит': 'entity', u'чьи задачи двигает': 'moves',
        u'что платформа делает сама': 'workflow', u'открытый доступ': 'public',
        u'чужого не видит': 'isolation', u'как часто': 'frequency',
        u'когда спросили': 'asked_on', u'куда пойдёт': 'goes_to',
        u'что блокирует': 'blocks', u'проверяет': 'covers', u'как проверяется': 'kind',
        u'состояние': 'status', u'данные': 'entities', u'виды': 'views', u'языки': 'languages'},
 'en': {'who': 'role', 'who sees it': 'roles', 'how important': 'priority',
        'screens': 'screens', 'triggers': 'triggers', 'trigger': 'trigger',
        'workflow': 'workflow', 'address': 'path', 'cases': 'cases',
        'what the person must do': 'gate', 'process': 'process', 'kind of event': 'type',
        'who creates it': 'source', 'when it fires': 'schedule', 'what it raises': 'raises',
        'what it watches': 'entity', 'public': 'public', 'sees nothing else': 'isolation',
        'how often': 'frequency', 'asked on': 'asked_on', 'where it goes': 'goes_to',
        'blocks': 'blocks', 'covers': 'covers', 'how it is checked': 'kind',
        'status': 'status'},
}
VALUES = {
 'ru': {u'критично': 'critical', u'важно': 'important', u'желательно': 'nice-to-have',
        u'внести данные': 'input', u'совершить действие': 'execute', u'утвердить': 'approve',
        u'проверить': 'review', u'расписание': 'schedule', u'событие в данных': 'db_event',
        u'форма на экране': 'form', u'вызов извне': 'webhook', u'запуск вручную': 'manual',
        u'да': True, u'нет': False, u'автоматически': 'auto', u'руками': 'manual'},
 'en': {},
}


class Item(object):
    __slots__ = ('id', 'title', 'level', 'ref', 'fields', 'sections', 'body', 'section')

    def __init__(self):
        self.id = self.title = self.ref = self.section = None
        self.level = 0
        self.fields, self.sections, self.body = {}, {}, []

    def get(self, key, default=None):
        return self.fields.get(key, default)

    def __repr__(self):
        return '<v3 %s %r>' % (self.id, (self.title or '')[:28])


def _split_heading(text):
    """«C-04 · Название» или «Название — `slug`» -> (id, title)."""
    m = re.match(r'^~*([A-Z]-\d{2}|[AB]\d+|M\d+(?:-T\d+)?|Z-\d{2})~*\s*·\s*(.+)$', text)
    if m:
        return m.group(1), m.group(2).strip()
    m = re.search(r'^(.*?)\s+—\s+`([A-Za-z0-9][A-Za-z0-9._-]*)`\s*$', text)
    if m:
        return m.group(2), m.group(1).strip()
    return None, text.strip()


IDENT = re.compile(r'^[A-Za-z0-9][A-Za-z0-9._*-]*$')


def _value(raw, lang):
    """Список — только когда КАЖДАЯ часть выглядит идентификатором.

    Наивное деление по запятой резало cron `0 6 1,16 * *` пополам и превращало
    «часы, по расписанию» в два значения. Запятая в тексте — это запятая, а не
    разделитель списка."""
    v = raw.strip().rstrip('.')
    tbl = VALUES.get(lang, {})

    def one(x):
        x = x.strip()
        # обратные кавычки снимаем только если в них ВСЁ значение: иначе
        # «workflow `wf-x`» теряет закрывающую и перестаёт быть кодом
        if len(x) > 1 and x[0] == '`' and x[-1] == '`' and x.count('`') == 2:
            x = x[1:-1].strip()
        return tbl.get(x.lower(), x)

    if ',' in v:
        parts = [p.strip().strip('`').strip() for p in v.split(',')]  # список — только из id
        if len(parts) > 1 and all(IDENT.match(p) for p in parts if p):
            return [one(p) for p in parts if p]
    return one(v)


def header(text):
    m = DOC_HEADER.match(text.lstrip().splitlines()[0] if text.strip() else '')
    return dict(doc=m.group(1), lang=m.group(2), version=m.group(3)) if m else {}


def read(text, lang=None):
    """Every heading of the document as an Item, in order."""
    h = header(text)
    lang = lang or h.get('lang') or 'ru'
    labels = LABELS.get(lang) or LABELS['en']
    items, cur, pending_ref, section = [], None, None, None
    for line in text.splitlines():
        m = REF.match(line.strip())
        if m:
            pending_ref = m.group(1)
            continue
        if line.lstrip().startswith('<!--'):
            continue
        hm = HEADING.match(line)
        if hm:
            lvl, txt = len(hm.group(1)), hm.group(2)
            if lvl == 2:
                section = txt
            it = Item()
            it.level, it.ref, it.section = lvl, pending_ref, section
            it.id, it.title = _split_heading(txt)
            items.append(it)
            cur, pending_ref = it, None
            continue
        if cur is None:
            continue
        bm = BULLET.match(line)
        if bm:
            key = labels.get(bm.group(1).strip().lower(), bm.group(1).strip().lower())
            cur.fields[key] = _value(bm.group(2), lang)
            continue
        pm = PROSE.match(line.strip())
        if pm:
            cur.sections[pm.group(1).strip()] = [pm.group(2)] if pm.group(2).strip() else []
            cur.body.append(line)
            continue
        if cur.sections:
            last = list(cur.sections)[-1]
            cur.sections[last].append(line)
        cur.body.append(line)
    return items


def entities(items, kind=None, level=None):
    """Only headings that carry an id, optionally filtered by the ref's collection."""
    out = []
    for it in items:
        if it.id is None:
            continue
        if level and it.level != level:
            continue
        if kind and not (it.ref or '').startswith(kind):
            continue
        out.append(it)
    return out


def load(path, lang=None):
    try:
        return read(io.open(path, encoding='utf-8').read(), lang)
    except IOError:
        return []
