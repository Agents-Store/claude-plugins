#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Манифест плагина и его запись в каталоге маркетплейса говорят одно и то же.

Run: python3 tests/test_manifest.py

Номер версии записан ДВАЖДЫ: в `.claude-plugin/plugin.json` самого плагина и в
записи этого плагина в корневом `.claude-plugin/marketplace.json`. Ничто их не
сверяет, и это измерено, а не предположено:

  * `claude plugin validate .` на плагине с расхождением 1.0.0 против 2.0.0
    отвечает «Validation passed» — молча, и с `--strict` тоже;
  * `claude plugin tag --help` обещает «validating that plugin.json and any
    enclosing marketplace entry agree», но читает только `plugin.json` и о
    расхождении не сообщает;
  * схема по адресу из `$schema` каталога отдаёт 404.

Правило при этом записано в процессе ТРИЖДЫ — `plugin-creator:improve` шаг 6
(«Both versions MUST be identical»), его же шаг 8 и чек-лист
`plugin-creator:validate` (там даже заготовлен текст ошибки). И всё равно на
2026-08-29 из 51 плагина репозитория разошлись три: `document-generator`,
`nocobase`, `plane-ops` — во всех трёх каталог отстал от плагина. Правило,
адресованное модели, срабатывает только когда кто-то вызовет скилл; этот файл
срабатывает всегда.

## Почему сверка, а не отказ от дубля

Документация Claude Code противоречит сама себе. `plugin-marketplaces.md` даёт
«Version Resolution Order: 1) marketplace entry, 2) plugin.json» — и следующей
строкой пишет «Avoid setting `version` in both places; `plugin.json` takes
precedence». Официальный каталог голосует за второе: `version` несут 14 записей
из 291.

Пока противоречие не разрешено, РАВЕНСТВО — единственное состояние, при котором
любое из двух прочтений даёт один ответ. Убрать дубль из каталога было бы
элегантнее и ближе к совету документации, но это ставка на одно из двух
несогласованных утверждений, а равенство ставкой не является.

## Область

Проверяется ТОЛЬКО запись этого плагина. Прогон принадлежит `macstack-dev`, и
краснеть из-за чужой версии он не должен — это чужая работа в чужом каталоге.
Каталог ищется вверх по дереву, а не по фиксированному «два уровня»: установленный
плагин лежит не там, где исходник, и отсутствие каталога — не провал, а другой
способ существования плагина.
"""
import io
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(HERE)
MANIFEST = os.path.join(PLUGIN_DIR, '.claude-plugin', 'plugin.json')


def _load(path):
    with io.open(path, encoding='utf-8') as fh:
        return json.load(fh)


def find_marketplace_entry(name, start):
    """Ближайший вверх по дереву каталог, в котором ЕСТЬ запись этого плагина.

    Возвращает `(путь, запись)` либо `(None, None)`. Найденный, но не содержащий
    нас каталог не останавливает подъём: репозиторий плагинов может лежать
    внутри другого маркетплейса.
    """
    path = start
    while True:
        candidate = os.path.join(path, '.claude-plugin', 'marketplace.json')
        if os.path.exists(candidate):
            try:
                data = _load(candidate)
            except ValueError:
                data = {}
            for entry in (data.get('plugins') or []):
                if entry.get('name') == name:
                    return candidate, entry
        parent = os.path.dirname(path)
        if parent == path:
            return None, None
        path = parent


class Manifest(unittest.TestCase):
    def setUp(self):
        self.assertTrue(os.path.exists(MANIFEST),
                        'у плагина нет .claude-plugin/plugin.json: %s' % MANIFEST)
        self.plugin = _load(MANIFEST)

    def test_name_and_version_are_present(self):
        # `version` в схеме необязателен, но этот плагин им пользуется, и
        # молчаливое исчезновение поля обесценило бы сверку ниже.
        self.assertIn('name', self.plugin)
        self.assertIn('version', self.plugin,
                      'plugin.json потерял version — сверять станет нечего')

    def test_version_matches_the_marketplace_entry(self):
        name = self.plugin['name']
        path, entry = find_marketplace_entry(name, PLUGIN_DIR)
        if entry is None:
            self.skipTest('каталог маркетплейса с записью «%s» не найден выше %s '
                          '— плагин установлен отдельно' % (name, PLUGIN_DIR))
        if 'version' not in entry:
            self.skipTest('запись «%s» в %s не несёт version — дубля нет, '
                          'сверять нечего' % (name, path))
        self.assertEqual(
            entry['version'], self.plugin['version'],
            'версии разошлись: %s говорит %s, а запись в %s — %s. '
            'Каталог следует за plugin.json.'
            % (MANIFEST, self.plugin['version'], path, entry['version']))

    def test_name_matches_the_marketplace_entry(self):
        # Имя — ключ, по которому запись вообще находится, поэтому расхождение
        # имени выглядит как отсутствие записи. Утверждение существует, чтобы
        # пропуск выше нельзя было принять за успех.
        name = self.plugin['name']
        path, entry = find_marketplace_entry(name, PLUGIN_DIR)
        if entry is None:
            self.skipTest('каталога с записью «%s» нет выше %s' % (name, PLUGIN_DIR))
        self.assertEqual(entry['name'], name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
