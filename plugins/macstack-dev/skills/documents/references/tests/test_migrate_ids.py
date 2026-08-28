# -*- coding: utf-8 -*-
"""Перевод id на новую форму переименовывает объявленное и НИЧЕГО больше.

Два способа сделать эту миграцию неправильно, и оба измерены на живом проекте:

1. **Слепой regex.** `^[A-Z]-\\d{2}$` совпадает не только с нашими кейсами. В
   проекте ohawo по той же форме записаны id ЧУЖОГО документа — немецкого
   технического задания заказчика (`E-05`, `A-08`, `NF-07`). Переименовав их, мы
   порвали бы ссылку на бумагу, которой не владеем, и молча.

2. **Забыть про неизменяемое.** Первая версия скрипта сравнивала путь с началом
   строки, а `inbox/` и `history/handoffs/` лежат ВНУТРИ `macstack/` — проверка
   не срабатывала ни разу. Разница измерена: 9041 замена против 2964. Две трети
   всех совпадений сидели в пакетах, уже отправленных заказчику, где id — это то,
   что он прочитал, и переписывать их задним числом значит рассинхронить его
   копию с нашей без единого следа.
"""
import io
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPT = os.path.join(os.path.dirname(HERE), 'migrate_ids.py')


def write(path, text):
    d = os.path.dirname(path)
    if not os.path.isdir(d):
        os.makedirs(d)
    with io.open(path, 'w', encoding='utf-8') as f:
        f.write(text)


def read(path):
    return io.open(path, encoding='utf-8').read()


class MigrateIds(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix='macstack-migrate-')
        ms = os.path.join(self.root, 'macstack')
        write(os.path.join(ms, 'client', 'USER-CASES.md'),
              u'### C-14 · Сообщить о проблеме\n\n### T-19 · Табель\n')
        write(os.path.join(ms, 'client', 'OPEN-QUESTIONS.md'),
              u'### A27 · Роли на смене\n\n### A2 · Реквизиты\n\n### B1 · Отложенное\n')
        write(os.path.join(ms, 'history', 'TASKS.md'),
              u'Закрывает `C-14`. Заблокирована `A27`. Задача M15-T11.\n')
        write(os.path.join(self.root, 'tests', 'a.spec.ts'),
              u"it('делает своё дело (C-14)', () => {})\n")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def run_script(self, *args):
        return subprocess.check_output(
            [sys.executable, SCRIPT, self.root] + list(args),
            stderr=subprocess.STDOUT).decode('utf-8')

    def test_declared_ids_are_renamed_everywhere_they_are_cited(self):
        self.run_script('--apply')
        tasks = read(os.path.join(self.root, 'macstack', 'history', 'TASKS.md'))
        self.assertIn('CC-14', tasks)
        self.assertIn('QA27', tasks)
        self.assertIn('M15-T11', tasks, u'задача не должна меняться — M это веха')
        self.assertIn('(CC-14)', read(os.path.join(self.root, 'tests', 'a.spec.ts')))

    def test_both_a_short_and_a_long_id_sharing_a_prefix_survive(self):
        # `A2` и `A27` объявлены оба. Опасность — что короткий съест префикс
        # длинного. Проверяется на тексте, где стоят ОБА: если бы съел, вместо
        # `QA2` и `QA27` вышло бы `QA2` и `QA2` с висящей семёркой.
        p = os.path.join(self.root, 'macstack', 'history', 'DECISIONS.md')
        write(p, u'Вопрос A2 про реквизиты и вопрос A27 про роли.\n')
        self.run_script('--apply')
        got = read(p)
        self.assertIn(u'Вопрос QA2 про реквизиты', got)
        self.assertIn(u'вопрос QA27 про роли', got)

    def test_a_lookalike_from_someone_elses_document_is_left_alone(self):
        # Ровно та форма, но НЕ объявлено заголовком в USER-CASES.md.
        p = os.path.join(self.root, 'macstack', 'history', 'DECISIONS.md')
        write(p, u'По §14 UStG, требования `E-05`, `A-08` и `NF-07` из ТЗ заказчика.\n')
        self.run_script('--apply')
        kept = read(p)
        for foreign in (u'E-05', u'A-08', u'NF-07'):
            self.assertIn(foreign, kept)
        self.assertNotIn(u'CE-05', kept)
        self.assertNotIn(u'CA-08', kept)

    def test_material_already_sent_to_the_client_is_never_rewritten(self):
        sent = os.path.join(self.root, 'macstack', 'history', 'handoffs', 'p.html')
        raw = os.path.join(self.root, 'macstack', 'inbox', 'brief.md')
        write(sent, u'<p>Кейс C-14, вопрос A27</p>\n')
        write(raw, u'Кейс C-14 из письма клиента\n')
        self.run_script('--apply')
        self.assertIn(u'C-14', read(sent))
        self.assertNotIn(u'CC-14', read(sent))
        self.assertIn(u'C-14', read(raw))
        self.assertNotIn(u'CC-14', read(raw))

    def test_showing_changes_nothing(self):
        before = read(os.path.join(self.root, 'macstack', 'history', 'TASKS.md'))
        out = self.run_script()
        self.assertIn(u'--apply', out)
        self.assertEqual(before, read(os.path.join(self.root, 'macstack', 'history', 'TASKS.md')))

    def test_running_twice_does_not_double_the_prefix(self):
        self.run_script('--apply')
        again = self.run_script('--apply')
        self.assertIn(u'уже переведён', again)
        tasks = read(os.path.join(self.root, 'macstack', 'history', 'TASKS.md'))
        self.assertIn('CC-14', tasks)
        self.assertNotIn('CCC-14', tasks)
        self.assertNotIn('QQA27', tasks)


if __name__ == '__main__':
    unittest.main(verbosity=2)
