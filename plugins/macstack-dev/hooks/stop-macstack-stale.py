#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Работа закончилась, код изменился, папка macstack/ — нет. Сказать об этом.

Почему хук, а не правило линтера. Правила у этого плагина есть и они хорошие, но
все они срабатывают, когда кто-то САМ наберёт `/macstack-dev:check`. А не набирает
их ровно тот, кто торопится, — то есть тот, чьи документы и расходятся с кодом.
Проверка, которую надо не забыть запустить, ловит только дисциплинированных.

Мягко и намеренно. Возвращает `additionalContext`: агент получает обратную связь,
ход не прерывается, ничего не блокируется. Жёсткий вариант — не дать закоммитить —
надёжнее ровно до первой мелкой правки, после которой его начинают обходить, и
тогда он не ловит уже никого.

Молчит всегда, когда не уверен: нет git, нет папки, нечего сравнивать. Хук,
который говорит невпопад, обучает себя игнорировать — и тогда он не сработает
в тот единственный раз, когда был нужен.
"""
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import macstack_freshness                                       # noqa: E402

# Изменения, которые не меняют поведение системы и потому не повод трогать
# документы. Список короткий намеренно: чем он длиннее, тем больше настоящих
# правок пройдёт мимо.
IGNORED_SUFFIX = ('.lock', '.log', '.snap')
IGNORED_PREFIX = ('.env', '.claude/', '.github/', 'node_modules/')
IGNORED_NAME = ('package-lock.json', 'pnpm-lock.yaml', 'yarn.lock',
                'poetry.lock', 'Cargo.lock', 'uv.lock')


def quiet(reason=''):
    """Тишина — не ошибка. Выходим с нулём и без вывода."""
    if os.environ.get('MACSTACK_HOOK_DEBUG'):
        sys.stderr.write('macstack-hook: молчу (%s)\n' % (reason or 'нечего сказать'))
    sys.exit(0)


def run(args, cwd):
    try:
        p = subprocess.run(args, cwd=cwd, stdout=subprocess.PIPE,
                           stderr=subprocess.DEVNULL, timeout=10)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    return p.stdout.decode('utf-8', 'replace')


def find_root(start):
    """Ближайший каталог вверх, в котором есть macstack/macstack.json."""
    d = os.path.abspath(start)
    while True:
        if os.path.exists(os.path.join(d, 'macstack', 'macstack.json')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def interesting(path):
    if path.startswith('macstack/'):
        return False
    base = os.path.basename(path)
    if base in IGNORED_NAME or path.startswith(IGNORED_PREFIX):
        return False
    if path.endswith(IGNORED_SUFFIX):
        return False
    return True


def main():
    try:
        payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except (ValueError, OSError):
        payload = {}
    # Повторный заход того же хука — вторая подсказка про то же самое лишняя.
    if payload.get('stop_hook_active'):
        quiet('уже сработал в этом ходе')

    cwd = payload.get('cwd') or os.getcwd()
    root = find_root(cwd)
    if not root:
        quiet('папки macstack/ нет — проект не пользуется стандартом')

    status = run(['git', 'status', '--porcelain'], root)
    if status is None:
        quiet('git не отвечает или это не репозиторий')

    changed = []
    for line in status.splitlines():
        if len(line) < 4:
            continue
        p = line[3:].strip().strip('"')
        if ' -> ' in p:                       # переименование
            p = p.split(' -> ')[-1]
        changed.append(p)
    if not changed:
        quiet('рабочее дерево чистое')

    touched_macstack = [p for p in changed if p.startswith('macstack/')]
    if touched_macstack:
        quiet('macstack/ уже трогали: %d' % len(touched_macstack))

    code = [p for p in changed if interesting(p)]
    if not code:
        quiet('изменилось только то, что поведения не меняет')

    shown = ', '.join(sorted(code)[:4]) + (' и ещё %d' % (len(code) - 4) if len(code) > 4 else '')
    msg = (
        'Незакоммиченных изменений вне macstack/: %d (%s). Папка macstack/ не '
        'тронута.\n'
        'Если поведение системы изменилось — запустите /macstack-dev:update: он '
        'сверит документы с кодом, пересоберёт generated/ и запишет для клиента, '
        'что изменилось.\n'
        'Если появилась сущность, маршрут, задание или роль, которых нет в '
        'документах — /macstack-dev:check --new.\n'
        'Если это правка, поведения не меняющая, просто скажите об этом и идите '
        'дальше — это напоминание, а не запрет.'
        % (len(code), shown)
    )
    # Про отставание документов говорим ТОЛЬКО здесь, вместе с уже заслуженным
    # сообщением. Отдельная фраза об этом на каждом ходу была бы шумом, который
    # всегда одинаков, — а такой шум учит не читать и остальное.
    stale_line = None
    try:
        stale_line = macstack_freshness.sentence(root)
    except Exception:                                            # noqa: BLE001
        stale_line = None
    if stale_line:
        msg += '\n' + stale_line
    json.dump({'hookSpecificOutput': {'hookEventName': 'Stop',
                                      'additionalContext': msg}},
              sys.stdout, ensure_ascii=False)
    sys.stdout.write('\n')
    sys.exit(0)


if __name__ == '__main__':
    main()
