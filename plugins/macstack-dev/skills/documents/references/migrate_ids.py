# -*- coding: utf-8 -*-
"""Перевод проекта со старой формы id на новую: `C-14` → `CC-14`, `A27` → `QA27`.

## Зачем

Старая форма не говорила, в каком файле искать запись, и переиспользовала буквы:
`T-19` был кейсом тренинг-центра, а `T` в `M15-T11` — задачей. Владелец проекта
читал код и не мог по нему понять ни файла, ни вида записи.

Новая форма ставит букву файла впереди: `C` — case (`client/USER-CASES.md`),
`Q` — question (`client/OPEN-QUESTIONS.md`). Вторая буква остаётся прежней и
означает то же, что раньше: роль у кейса, адресата у вопроса.

## Почему слепой regex здесь НЕЛЬЗЯ

`^[A-Z]-\\d{2}$` matches не только наши кейсы. В живом проекте по этой же форме
записаны id ЧУЖОГО документа — немецкого технического задания заказчика
(`E-05`, `A-08`, `NF-07`). Переименовав их, мы бы порвали ссылку на бумагу,
которой не владеем, и сделали это молча.

Поэтому скрипт **сначала читает объявления** — заголовки в `USER-CASES.md` и
`OPEN-QUESTIONS.md`, — и переименовывает ровно те id, которые там объявлены.
Всё остальное, даже совпадающее по форме, не трогается.

## Что не трогается никогда

`inbox/` и `history/handoffs/` — материал заказчика и уже отправленные ему
пакеты. Оба неизменяемы по устройству macstack: пакет, отданный клиенту, несёт
те id, которые клиент прочитал, и переписать их задним числом значит рассинхронить
его копию с нашей без единого следа.

## Как запускать

    python3 migrate_ids.py <корень проекта>            # показать, ничего не менять
    python3 migrate_ids.py <корень проекта> --apply     # переписать

Второй запуск идемпотентен: `CC-14` под старый шаблон уже не подходит.
"""
from __future__ import print_function

import io
import os
import re
import sys

MACSTACK = 'macstack'
# Имена КАТАЛОГОВ, в которые не заходим. Сравниваются как компоненты пути на
# любой глубине, а не как префикс от корня: неизменяемое лежит внутри
# `macstack/`, и сравнение с началом пути молча пропускало бы его.
NEVER_DIRS = ('inbox', 'handoffs', 'node_modules', '.git', '.next', 'dist',
              'build', 'coverage', '.turbo', '.claude', '.codex', '.venv',
              '__pycache__')
EXT = ('.md', '.json', '.jsonl', '.ts', '.tsx', '.js', '.jsx', '.html')

CASE_HEADING = re.compile(r'^#{2,6}\s+~*([A-Z]-[0-9]{2})~*\s*[·.]', re.M)
OPEN_HEADING = re.compile(r'^#{2,6}\s+~*([AB][0-9]+)~*\s*[·.—-]', re.M)


def declared(root):
    """-> (кейсы, открытые вопросы) — ровно те id, что ОБЪЯВЛЕНЫ заголовками."""
    def read(rel):
        p = os.path.join(root, MACSTACK, rel)
        if not os.path.exists(p):
            return ''
        return io.open(p, encoding='utf-8', errors='replace').read()

    cases = set(CASE_HEADING.findall(read(os.path.join('client', 'USER-CASES.md'))))
    opens = set(OPEN_HEADING.findall(read(os.path.join('client', 'OPEN-QUESTIONS.md'))))
    return cases, opens


def rename_map(cases, opens):
    out = {}
    for cid in cases:
        out[cid] = 'C' + cid
    for oid in opens:
        out[oid] = 'Q' + oid
    return out


def walkable(root):
    for base, dirs, files in os.walk(root):
        parts = os.path.relpath(base, root).split(os.sep)
        if any(part in NEVER_DIRS for part in parts):
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs
                   if d not in NEVER_DIRS
                   and not os.path.exists(os.path.join(base, d, '.git'))]
        for f in files:
            if f.endswith(EXT):
                yield os.path.join(base, f)


def main():
    argv = [a for a in sys.argv[1:] if not a.startswith('-')]
    apply_ = '--apply' in sys.argv[1:]
    if any(a in ('-h', '--help') for a in sys.argv[1:]) or not argv:
        print(__doc__)
        return 0
    root = argv[0]

    docs = [os.path.join(root, MACSTACK, 'client', n)
            for n in ('USER-CASES.md', 'OPEN-QUESTIONS.md')]
    if not any(os.path.exists(d) for d in docs):
        print('в %s нет ни USER-CASES.md, ни OPEN-QUESTIONS.md — это не проект macstack' % root)
        return 1

    cases, opens = declared(root)
    if not cases and not opens:
        # Документы на месте, но ни одного id СТАРОЙ формы в заголовках. Это
        # нормальный исход второго запуска, а не отказ: код возврата 1 здесь
        # выглядел бы в скрипте вызывающего как сломанная миграция.
        print('старой формы id в заголовках нет — проект уже переведён, делать нечего')
        return 0
    mapping = rename_map(cases, opens)
    # Длинные сначала: иначе `A2` съел бы префикс `A27`.
    ordered = sorted(mapping, key=len, reverse=True)
    pattern = re.compile(r'\b(' + '|'.join(re.escape(k) for k in ordered) + r')\b')

    print('объявлено кейсов: %d, вопросов: %d' % (len(cases), len(opens)))
    touched, total = 0, 0
    for path in walkable(root):
        try:
            text = io.open(path, encoding='utf-8', errors='replace').read()
        except IOError:
            continue
        new, n = pattern.subn(lambda m: mapping[m.group(1)], text)
        if n:
            touched += 1
            total += n
            print('%5d  %s' % (n, os.path.relpath(path, root)))
            if apply_:
                with io.open(path, 'w', encoding='utf-8') as f:
                    f.write(new)

    print('\nфайлов: %d, замен: %d' % (touched, total))
    if not apply_:
        print('это показ. чтобы переписать — добавьте --apply')
    else:
        print('переписано. дальше: пересобрать generated/ и прогнать линт')
    return 0


if __name__ == '__main__':
    sys.exit(main())
