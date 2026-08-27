#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сессия начинается — сказать, если документы давно не сверяли с кодом.

Почему отдельным хуком, а не в Stop. Stop срабатывает на каждом ходу, и фраза
про отставание, повторённая тридцать раз за сессию, перестаёт читаться на третий.
SessionStart срабатывает один раз — это естественная граница «раз в сеанс», и она
не требует ни файла состояния, ни счётчика, которому можно разойтись с правдой.

Stop говорит про отставание тоже, но только когда УЖЕ заслужил слово: код
изменился, а папку не трогали. Тогда это уместно. Здесь — когда вы только сели
работать и ещё ничего не сделали.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import macstack_freshness                                       # noqa: E402


def main():
    try:
        payload = json.load(sys.stdin) if not sys.stdin.isatty() else {}
    except (ValueError, OSError):
        payload = {}
    cwd = payload.get('cwd') or os.getcwd()

    root = cwd
    while True:
        if os.path.exists(os.path.join(root, 'macstack', 'macstack.json')):
            break
        parent = os.path.dirname(root)
        if parent == root:
            sys.exit(0)          # проект не пользуется стандартом — молчим
        root = parent

    try:
        line = macstack_freshness.sentence(root)
    except Exception:                                            # noqa: BLE001
        sys.exit(0)              # не смогли измерить — молчать честнее, чем гадать
    if not line:
        sys.exit(0)

    json.dump({'hookSpecificOutput': {'hookEventName': 'SessionStart',
                                      'additionalContext': line}},
              sys.stdout, ensure_ascii=False)
    sys.stdout.write('\n')


if __name__ == '__main__':
    main()
