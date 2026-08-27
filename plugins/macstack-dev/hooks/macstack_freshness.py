# -*- coding: utf-8 -*-
"""Насколько документы отстали от кода. Одна реализация на оба хука.

Считает ровно как правило линтера 12.17: порог из `docs.freshness_days` (по
умолчанию 30), сгенерированные документы не в счёт, а самая свежая запись `audit`
в журнале двигает часы всем документам сразу. Две копии одного правила разошлись
бы молча, и первым признаком стало бы то, что хук и линтер говорят о свежести
разное — а разбираться пошли бы в код проекта, а не в код плагина.
"""
import datetime
import io
import json
import os

DEFAULT_DAYS = 30
# Контракт документов — тот же файл, который читает линтер. Список
# сгенерированных здесь НЕ дублируется: копия разошлась бы молча, и первым
# признаком стало бы то, что хук считает шесть документов, а правило пять.
_CONTRACT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         '..', 'skills', 'documents', 'references',
                         'doc-contracts.json')


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


def last_audit(root):
    """День последней сверки с кодом: свежайшая строка `audit` в журнале."""
    best = None
    p = os.path.join(root, 'macstack', 'history', 'ledger.jsonl')
    if not os.path.exists(p):
        return None
    try:
        for line in io.open(p, encoding='utf-8'):
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            if row.get('kind') != 'audit':
                continue
            d = _date(row.get('date'))
            if d and (best is None or d > best):
                best = d
    except (IOError, ValueError):
        return best
    return best


def survey(root, today=None):
    """(никогда_не_сверяли, [(имя, дней)], порог) — или None, если мерить нечем."""
    spec = _load(os.path.join(root, 'macstack', 'macstack.json'))
    if spec is None:
        return None
    docs = spec.get('docs') or {}
    files = docs.get('files') or {}
    if not files:
        return None

    limit = docs.get('freshness_days')
    if not isinstance(limit, int) or isinstance(limit, bool) or limit <= 0:
        limit = DEFAULT_DAYS

    today = today or datetime.date.today()
    lift = last_audit(root)
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
        if age > limit:
            old.append((key, age))
    if not never and not old:
        return None
    return never, sorted(old, key=lambda x: -x[1]), limit


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
