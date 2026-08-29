#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Линтер и хуки меряют свежесть документов ОДНИМ кодом.

Run: python3 tests/test_freshness.py

Правило 12.17 и оба хука отвечают на один вопрос — сколько дней назад документ
сверяли с кодом и не вышел ли он за срок. Ответов было три, и две копии успели
разойтись; обе поломки нашлись валидацией 2026-08-29 и обе были молчаливыми:

  * `freshness_days` схема описывает ВНУТРИ `docRef`, то есть на документ. И
    правило, и хук читали единственное верхнеуровневое `docs.freshness_days`,
    которого в схеме не было вовсе. Настройка, которую обещает документация, не
    делала ничего; работала недокументированная. Файл говорит «девяносто дней»,
    линтер меряет тридцатью, и никто из двоих про другого не упоминает.

  * дату последней сверки линтер поднимал по журналу И по `archive/reviews/` —
    для проектов, отревьюенных до переезда вердиктов в журнал. Хук читал только
    журнал. На таком проекте линтер молчал, а хук на старте сессии заявлял «ни
    разу не сверяли»: инструменты спорили о свежести, и разбираться пошли бы в
    документы проекта, а не в код плагина.

Оба дефекта живут в зазоре между двумя реализациями, поэтому проверяется не
поведение каждой, а то, что реализация ОДНА. Тест на «обе считают одинаково»
пришлось бы дописывать под каждый новый случай, и он бы отстал.

## Почему здесь же перепись правил

`_load_rule_modules` ловит любое исключение импорта, пишет строку в stderr и
идёт дальше. Правила из непрогрузившегося модуля просто не регистрируются, а
линтер отвечает «чисто» — то есть ошибка импорта выглядит как здоровый проект.
Перекрёстный импорт `rules_hygiene` → `hooks/` сделал этот путь достижимым,
поэтому число правил теперь утверждается, а не подразумевается.
"""
import datetime
import io
import json
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(HERE)
LINT = os.path.join(PLUGIN_DIR, 'skills', 'lint', 'references')
HOOKS = os.path.join(PLUGIN_DIR, 'hooks')
SCHEMA = os.path.join(LINT, 'macstack.schema.json')

sys.path.insert(0, HOOKS)
import macstack_freshness as mf                                 # noqa: E402

EXPECTED_RULES = 41


def _load(path):
    with io.open(path, encoding='utf-8') as fh:
        return json.load(fh)


class OneOwner(unittest.TestCase):
    """Считает один модуль, зовут из обоих мест."""

    def test_lint_delegates_the_audit_date_to_the_hook_module(self):
        sys.path.insert(0, LINT)
        import rules_hygiene                                    # noqa: PLC0415
        self.assertIs(
            rules_hygiene._latest_conformance_date, mf.last_audit,
            'правило 12.17 снова считает дату аудита само — вторая копия '
            'разойдётся с хуковой ровно так же, как разошлась прошлая')

    def test_every_rule_module_loads(self):
        sys.path.insert(0, LINT)
        import lint_folder                                      # noqa: PLC0415
        got = sorted(set(r.rid for r in lint_folder._RULES),
                     key=lambda s: [int(x) for x in s.split('.')])
        self.assertEqual(
            len(got), EXPECTED_RULES,
            'зарегистрировано %d правил вместо %d: %s. Загрузчик глотает ошибку '
            'импорта и идёт дальше, так что непрогрузившийся модуль правил '
            'выглядит как чистый проект.' % (len(got), EXPECTED_RULES, ' '.join(got)))


class Budget(unittest.TestCase):
    """Срок годности: свой → общий → 30."""

    def test_per_document_value_wins(self):
        self.assertEqual(mf.budget({'freshness_days': 60}, {'freshness_days': 7}), 7)

    def test_folder_wide_value_is_the_fallback(self):
        self.assertEqual(mf.budget({'freshness_days': 60}, {}), 60)

    def test_default_when_nothing_is_set(self):
        self.assertEqual(mf.budget({}, {}), mf.DEFAULT_DAYS)

    def test_junk_is_not_a_budget(self):
        # `true` наследует int и прошло бы как срок в один день; строка «thirty»
        # однажды убила правило целиком. Спецификация, не прошедшая проверку
        # схемы, всё равно доходит до этого кода.
        for junk in ('thirty', True, 0, -5, None, [], {}):
            self.assertEqual(mf.budget({'freshness_days': junk}, {}), mf.DEFAULT_DAYS,
                             'значение %r принято за срок' % (junk,))

    def test_junk_is_reported_from_both_places(self):
        found = dict(mf.bad_budget_values({
            'freshness_days': 'thirty',
            'files': {'overview': {'freshness_days': 0},
                      'handbook': {'freshness_days': 90}},
        }))
        self.assertIn('docs.freshness_days', found)
        self.assertIn('docs.files.overview.freshness_days', found)
        self.assertNotIn('docs.files.handbook.freshness_days', found)


class ArchivedAuditStillCounts(unittest.TestCase):
    """Вердикт, лежащий в archive/reviews/, поднимает часы и для хука тоже."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.ms = os.path.join(self.root, 'macstack')
        os.makedirs(os.path.join(self.ms, 'history', 'archive', 'reviews'))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def _write_spec(self, reviewed):
        spec = {'docs': {'root': 'macstack',
                         'files': {'overview': {'path': 'client/OVERVIEW.md',
                                                'reviewed': reviewed}}}}
        with io.open(os.path.join(self.ms, 'macstack.json'), 'w',
                     encoding='utf-8') as fh:
            fh.write(json.dumps(spec, ensure_ascii=False))

    def test_archived_verdict_is_read(self):
        open(os.path.join(self.ms, 'history', 'archive', 'reviews',
                          '2026-08-20-whole-stack-conformance.md'), 'w').close()
        self.assertEqual(mf.last_audit(self.ms), datetime.date(2026, 8, 20),
                         'вердикт из archive/reviews/ не прочитан — на проекте, '
                         'отревьюенном до переезда вердиктов в журнал, хук снова '
                         'скажет «ни разу не сверяли», пока линтер молчит')

    def test_the_lift_makes_a_stale_document_fresh(self):
        # Документ помечен сверенным год назад, но проект целиком отревьюен
        # вчера — вердикт двигает часы всем документам сразу.
        today = datetime.date(2026, 8, 29)
        self._write_spec('2025-08-01')
        self.assertIsNotNone(mf.survey(self.root, today),
                             'без вердикта документ обязан числиться устаревшим')
        open(os.path.join(self.ms, 'history', 'archive', 'reviews',
                          '2026-08-28-whole-stack-conformance.md'), 'w').close()
        self.assertIsNone(mf.survey(self.root, today),
                          'вердикт вчерашним числом не поднял часы')

    def test_a_broken_ledger_line_does_not_cost_the_whole_journal(self):
        # Журнал append-only и дописывается на живом проекте: оборванная
        # последняя строка — обычное дело, а не повод забыть всё остальное.
        led = os.path.join(self.ms, 'history', 'ledger.jsonl')
        with io.open(led, 'w', encoding='utf-8') as fh:
            fh.write(u'{"kind":"audit","date":"2026-08-25"}\n')
            fh.write(u'{"kind":"audit","date":"2026-08-2\n')
        self.assertEqual(mf.last_audit(self.ms), datetime.date(2026, 8, 25))


class SchemaDocumentsWhatIsRead(unittest.TestCase):
    """Читаемое поле описано, описанное поле читается."""

    def setUp(self):
        self.schema = _load(SCHEMA)

    def test_folder_wide_budget_is_in_the_schema(self):
        docs = self.schema['properties']['docs']['properties']
        self.assertIn('freshness_days', docs,
                      'линтер и хук читают docs.freshness_days, а схема о нём '
                      'молчит — работающая настройка снова недокументирована')

    def test_per_document_budget_is_in_the_schema(self):
        self.assertIn('freshness_days', self.schema['$defs']['docRef']['properties'])

    def test_the_two_defaults_agree_with_the_code(self):
        docs = self.schema['properties']['docs']['properties']['freshness_days']
        ref = self.schema['$defs']['docRef']['properties']['freshness_days']
        self.assertEqual(docs.get('default'), mf.DEFAULT_DAYS)
        self.assertEqual(ref.get('default'), mf.DEFAULT_DAYS)


if __name__ == '__main__':
    unittest.main(verbosity=2)
