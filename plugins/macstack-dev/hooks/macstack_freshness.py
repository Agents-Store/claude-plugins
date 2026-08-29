# -*- coding: utf-8 -*-
"""Насколько документы отстали от кода. Одна реализация на оба хука И на линтер.

Правило 12.17 и оба хука спрашивают одно и то же: сколько дней назад документ в
последний раз сверяли с кодом и не вышел ли он за свой срок. Три ответа на один
вопрос считались тремя разными кусками кода, и две копии успели разойтись:

  * порог. Схема описывает `freshness_days` ВНУТРИ `docRef`, то есть на документ
    (`docs.files.<key>.freshness_days`), а линтер и хук читали единственное
    верхнеуровневое `docs.freshness_days`, которого в схеме нет. Настройка,
    которую документация обещает, не делала ничего; работала недокументированная.
    Теперь `budget()` читает обе: сначала документ, потом общее, потом 30.

  * дата аудита. Линтер поднимал часы по журналу И по `archive/reviews/` — для
    проектов, отревьюенных до переезда вердиктов в журнал. Хук читал только
    журнал. На таком проекте линтер молчал, а хук на старте сессии заявлял «ни
    разу не сверяли» — то самое расхождение, ради предотвращения которого этот
    модуль и написан, случившееся внутри него самого.

Отсюда правило: считает здесь, зовут отсюда. `rules_hygiene.py` импортирует этот
файл (путь ему кладёт `lint_folder.py`, ровно как уже кладёт `documents/references`).
Расхождение теперь невозможно не потому, что за ним следят, а потому, что копии
больше нет.
"""
import datetime
import io
import json
import os
import re

DEFAULT_DAYS = 30
# Контракт документов — тот же файл, который читает линтер. Список
# сгенерированных здесь НЕ дублируется: копия разошлась бы молча, и первым
# признаком стало бы то, что хук считает шесть документов, а правило пять.
_CONTRACT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '..', 'skills', 'documents', 'references',
                         'doc-contracts.json')

_REVIEW_DATE = re.compile(r'^(\d{4}-\d{2}-\d{2})-.*-conformance\.md$')


def _load(path):
    try:
        with io.open(path, encoding='utf-8') as fh:
            return json.load(fh)
    except (IOError, ValueError):
        return None


def _date(value):
    """Дата или None. Всё, что не строка ГГГГ-ММ-ДД, — не дата.

    Значение приходит из файла, который мог не пройти проверку схемы: `reviewed:
    20260101` без кавычек читается как число и однажды убил правило 12.17 целиком.
    Хук, упавший на плохом значении, молчит — и выглядит точно как хук, которому
    нечего сказать.
    """
    try:
        return datetime.date(*[int(x) for x in str(value).split('-')])
    except (ValueError, TypeError):
        return None


def _generated_keys():
    c = _load(os.path.normpath(_CONTRACT)) or {}
    return set(k for k, d in (c.get('documents') or {}).items()
               if isinstance(d, dict) and d.get('generated'))


def _positive_int(value):
    """Целое больше нуля или None. `True` — не число: bool наследует int, и
    `freshness_days: true` иначе прошло бы как срок в один день."""
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def budget(docs, entry=None):
    """Срок годности документа в днях: свой → общий → 30.

    Схема описывает `freshness_days` на документ, и это осмысленно: бизнес-логика
    живёт дольше пользовательских кейсов, и один общий срок даёт либо шум, либо
    ложное спокойствие. Общее значение остаётся как умолчание для папки.
    """
    docs = docs if isinstance(docs, dict) else {}
    if isinstance(entry, dict):
        own = _positive_int(entry.get('freshness_days'))
        if own:
            return own
    return _positive_int(docs.get('freshness_days')) or DEFAULT_DAYS


def bad_budget_values(docs):
    """Значения `freshness_days`, которые заданы, но числом-сроком не являются —
    [(где, значение)]. Правило 12.17 сообщает о них; хук молча берёт умолчание.

    Отдельной функцией потому, что «плохое значение» и «нет значения» — разные
    события: второе нормально, первое означает, что человек хотел задать срок и
    промахнулся, а срок при этом молча стал равен тридцати.
    """
    docs = docs if isinstance(docs, dict) else {}
    out = []
    top = docs.get('freshness_days')
    if top is not None and _positive_int(top) is None:
        out.append(('docs.freshness_days', top))
    for key in sorted((docs.get('files') or {})):
        entry = (docs.get('files') or {}).get(key)
        if not isinstance(entry, dict):
            continue
        own = entry.get('freshness_days')
        if own is not None and _positive_int(own) is None:
            out.append(('docs.files.%s.freshness_days' % key, own))
    return out


def last_audit(macstack_dir):
    """День последней сверки документов с кодом, или None.

    Смысл ОДИН на всю папку («считается сверкой»), а не по документу: проект
    ревьюят целиком, и вердикт двигает часы всем документам разом.

    Читается из `history/ledger.jsonl`, строки `kind: audit`. Раньше читалось из
    `history/reviews/<дата>-*-conformance.md`; когда вердикты стали строками
    журнала, папка уехала в `archive/`, и чтение стало возвращать None на каждом
    проекте — подъём часов молча перестал работать. Поэтому `reviews/` и
    `archive/reviews/` читаются до сих пор: без них документы проекта,
    отревьюенного до переезда, выглядят несверенными ни разу.

    Аргумент — папка macstack/, не корень проекта.
    """
    best = None
    led = os.path.join(macstack_dir, 'history', 'ledger.jsonl')
    if os.path.exists(led):
        try:
            with io.open(led, encoding='utf-8') as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        row = json.loads(line)
                    except ValueError:
                        # Одна битая строка не должна стоить всего журнала: он
                        # append-only и дописывается на живом проекте, так что
                        # оборванная последняя строка — обычное дело, а не поломка.
                        continue
                    if not isinstance(row, dict) or row.get('kind') != 'audit':
                        continue
                    d = _date(row.get('date'))
                    if d and (best is None or d > best):
                        best = d
        except IOError:
            pass
    for reviews in (os.path.join(macstack_dir, 'history', 'reviews'),
                    os.path.join(macstack_dir, 'history', 'archive', 'reviews')):
        if not os.path.isdir(reviews):
            continue
        try:
            names = os.listdir(reviews)
        except OSError:
            continue
        for name in names:
            m = _REVIEW_DATE.match(name)
            if not m:
                continue
            d = _date(m.group(1))
            if d and (best is None or d > best):
                best = d
    return best


def survey(root, today=None):
    """(никогда_не_сверяли, [(имя, дней)], порог) — или None, если мерить нечем.

    `root` — корень ПРОЕКТА; папка спецификации ищется в нём как `macstack/`.
    Порог в ответе — общий по папке: фраза для человека одна на все документы, а
    свой срок каждого учтён при отборе тех, кто в неё попал.
    """
    macstack_dir = os.path.join(root, 'macstack')
    spec = _load(os.path.join(macstack_dir, 'macstack.json'))
    if spec is None:
        return None
    docs = spec.get('docs') or {}
    files = docs.get('files') or {}
    if not files:
        return None

    today = today or datetime.date.today()
    lift = last_audit(macstack_dir)
    generated = _generated_keys()

    never, old = [], []
    for key in sorted(files):
        entry = files[key]
        if not isinstance(entry, dict):
            continue
        # Сгенерированный документ с кодом не сверяют — его пересобирают, и за
        # это отвечает правило 12.18. Требовать с него дату «когда сверяли»
        # значит требовать проверку, которой для него не существует.
        if key in generated:
            continue
        d = _date(entry.get('reviewed'))
        if d is None:
            # Прочерк — это не «свежий», это «не сверяли ни разу», и это хуже,
            # чем устаревший: устаревший хотя бы был верен когда-то.
            never.append(key)
            continue
        if lift and lift > d:
            d = lift
        age = (today - d).days
        if age > budget(docs, entry):
            old.append((key, age))
    if not never and not old:
        return None
    return never, sorted(old, key=lambda x: -x[1]), budget(docs)


def sentence(root, today=None):
    """Одна фраза для человека, или None, когда говорить не о чем."""
    got = survey(root, today)
    if not got:
        return None
    never, old, limit = got
    parts = []
    if never:
        parts.append('ни разу не сверяли: %s' % ', '.join(never[:5])
                     + (' и ещё %d' % (len(never) - 5) if len(never) > 5 else ''))
    if old:
        parts.append('не сверяли дольше %d дней: %s'
                     % (limit, ', '.join('%s (%d)' % kv for kv in old[:4]))
                     + (' и ещё %d' % (len(old) - 4) if len(old) > 4 else ''))
    return ('Документы и код: %s. Сверка — /macstack-dev:check --code; она пишет '
            'вердикт по каждому кейсу в журнал и двигает даты.' % '; '.join(parts))
