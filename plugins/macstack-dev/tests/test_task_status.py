#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Статус задачи двигается по вердикту аудита — и в обе стороны.

Run: python3 tests/test_task_status.py

Связь «кейс -> задача» читалась ровно в одну сторону: `uncovered.py` спрашивал, есть
ли у кейса задача, чтобы не предлагать работу дважды. Обратный вопрос — актуальна ли
ещё сама задача — не задавал никто, и оба следствия молчаливые: список работ либо
показывает объём, которого нет, либо выглядит короче правды.

Второе опаснее, и поэтому переоткрытие проверяется здесь наравне с закрытием.
Скрипт, умеющий только закрывать, — это храповик: список работ у него может
исполняться, но не может расти, и первым признаком поломки станет задача, которую
считают сделанной, а её нет в коде.

## Что здесь закреплено помимо самих переходов

  * **Словарь статусов берётся из контракта.** Правило линтера 12.14 судит по
    `fields.status.enum`; карта `documents.tasks.statuses` не читается ничем и несёт
    токены (`doing`, `blocked`), которые это правило как раз отвергает. Скрипт,
    записавший `doing`, прошёл бы молча и уронил линт на следующем прогоне.
  * **Доказательство новее заявления.** Аудит, прогнанный ДО работы, не должен
    переоткрывать задачу, закрытую после него: иначе скрипт спорит с человеком, у
    которого больше сведений.
  * **v2-файл — ошибка, а не пустой прогон.** Писателя у v2 нет; отчёт «0
    расхождений» на непрочитанном файле неотличим от чистого прогона.
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
PLANNING = os.path.join(PLUGIN_DIR, 'skills', 'planning', 'references')
CONTRACT = os.path.join(PLUGIN_DIR, 'skills', 'documents', 'references',
                        'doc-contracts.json')

sys.path.insert(0, PLANNING)
import task_status as ts                                       # noqa: E402

TODAY = datetime.date(2026, 8, 29)
OLD, NEW = '2026-08-01', '2026-08-28'


def task_md(ident, title, status, closes, opened=OLD, finished=None, started=None):
    out = ['<!-- macstack:ref=cases[id=%s] -->' % closes.split(',')[0].strip(),
           '### %s · %s' % (ident, title),
           '',
           '- **Состояние:** %s' % status,
           '- **Заведена:** %s' % opened,
           '- **Закрывает:** %s' % closes,
           '- **Тикет:** TRACK-1']
    if started:
        out.append('- **Взята:** %s' % started)
    if finished:
        out.append('- **Закрыта:** %s' % finished)
    out += ['', 'Проза задачи.', '']
    return '\n'.join(out)


class Fixture(unittest.TestCase):
    """Проект с TASKS.md и журналом, собираемый под каждый тест."""

    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.ms = os.path.join(self.root, 'macstack')
        os.makedirs(os.path.join(self.ms, 'history'))
        os.makedirs(os.path.join(self.ms, 'client'))

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def write_tasks(self, *blocks):
        body = ('<!-- macstack:doc=tasks lang=ru version=1.0 -->\n'
                '# Задачи\n\n'
                '## Как читать этот документ\n\n'
                'Что будет сделано и в каком порядке.\n\n'
                '## Задачи\n\n') + '\n'.join(blocks)
        io.open(os.path.join(self.ms, 'history', 'TASKS.md'), 'w',
                encoding='utf-8').write(body)

    def write_audit(self, *rows):
        p = os.path.join(self.ms, 'history', 'ledger.jsonl')
        with io.open(p, 'w', encoding='utf-8') as fh:
            for case, verdict, date in rows:
                fh.write(json.dumps({'date': date, 'doc': 'client/USER-CASES.md',
                                     'item': case, 'kind': 'audit', 'now': verdict,
                                     'why': 'proof.spec.ts', 'by': 'claude'},
                                    ensure_ascii=False) + '\n')

    def run_it(self, apply=False):
        return ts.run(self.ms, apply=apply)

    def move_for(self, res, task):
        for m in res['moves']:
            if m['task'] == task:
                return m
        return None

    def held_for(self, res, task):
        for h in res['held']:
            if h['task'] == task:
                return h
        return None


class Closing(Fixture):
    def test_implemented_closes_an_open_task(self):
        self.write_tasks(task_md('M1-T1', 'Выдача', 'todo', 'K-01'))
        self.write_audit(('K-01', 'implemented', NEW))
        m = self.move_for(self.run_it(), 'M1-T1')
        self.assertIsNotNone(m, 'задача с подтверждённым кейсом осталась todo')
        self.assertEqual(m['now'], 'done')

    def test_all_cases_must_be_implemented(self):
        # Задача закрывает два кейса; построен один. Считать её сделанной — значит
        # объявить выполненным обещание, которое никто не проверял.
        self.write_tasks(task_md('M1-T2', 'Двое', 'todo', 'K-01, K-02'))
        self.write_audit(('K-01', 'implemented', NEW))
        self.assertIsNone(self.move_for(self.run_it(), 'M1-T2'))

    def test_a_case_with_no_verdict_is_named_not_ignored(self):
        self.write_tasks(task_md('M1-T3', 'Без вердикта', 'todo', 'K-09'))
        self.write_audit(('K-01', 'implemented', NEW))
        h = self.held_for(self.run_it(), 'M1-T3')
        self.assertIn('no audit verdict', h['why'])


class Reopening(Fixture):
    def test_absent_reopens_a_closed_task(self):
        self.write_tasks(task_md('M1-T1', 'Выдача', 'done', 'K-01', finished=OLD))
        self.write_audit(('K-01', 'absent', NEW))
        m = self.move_for(self.run_it(), 'M1-T1')
        self.assertIsNotNone(m, 'задача done с вердиктом absent не переоткрыта — '
                                'список работ короче правды, и это худшая сторона')
        self.assertEqual(m['now'], 'todo')

    def test_partial_reopens_into_in_progress(self):
        self.write_tasks(task_md('M1-T2', 'Частично', 'done', 'K-02', finished=OLD))
        self.write_audit(('K-02', 'partial', NEW))
        self.assertEqual(self.move_for(self.run_it(), 'M1-T2')['now'], 'in_progress')

    def test_absent_wins_over_partial(self):
        self.write_tasks(task_md('M1-T3', 'Оба', 'done', 'K-01, K-02', finished=OLD))
        self.write_audit(('K-01', 'partial', NEW), ('K-02', 'absent', NEW))
        self.assertEqual(self.move_for(self.run_it(), 'M1-T3')['now'], 'todo')

    def test_externally_blocked_does_not_reopen(self):
        # Код закончен, мешает внешнее. Переоткрытая задача вернула бы в очередь
        # работу, которую взявший её не сможет доделать, — ровно тот отказ, ради
        # которого кейс, ждущий клиента, вообще не становится задачей.
        self.write_tasks(task_md('M1-T4', 'Ждёт счёт', 'done', 'K-01', finished=OLD))
        self.write_audit(('K-01', 'externally-blocked', NEW))
        self.assertIsNone(self.move_for(self.run_it(), 'M1-T4'))


class Freshness(Fixture):
    def test_a_verdict_older_than_the_task_is_stale(self):
        self.write_tasks(task_md('M1-T1', 'Выдача', 'done', 'K-01',
                                 opened=OLD, finished=NEW))
        self.write_audit(('K-01', 'absent', OLD))
        self.assertIsNone(self.move_for(self.run_it(), 'M1-T1'),
                          'аудит, прогнанный до работы, переоткрыл задачу, закрытую '
                          'после него — скрипт спорит с тем, кто знает больше')
        self.assertIn('stale evidence', self.held_for(self.run_it(), 'M1-T1')['why'])

    def test_the_newest_verdict_wins(self):
        self.write_tasks(task_md('M1-T2', 'Выдача', 'todo', 'K-01'))
        self.write_audit(('K-01', 'absent', '2026-08-10'),
                         ('K-01', 'implemented', NEW))
        self.assertEqual(self.move_for(self.run_it(), 'M1-T2')['now'], 'done')


class NeverTouched(Fixture):
    def test_a_decision_is_not_a_measurement(self):
        # cancelled/backlog — решения человека. Аудит меряет код и про решение
        # ничего сказать не может.
        self.write_tasks(task_md('M1-T1', 'Снята', 'cancelled', 'K-01'),
                         task_md('M1-T2', 'В бэклоге', 'backlog', 'K-01'))
        self.write_audit(('K-01', 'implemented', NEW))
        res = self.run_it()
        self.assertEqual(res['moves'], [])
        for t in ('M1-T1', 'M1-T2'):
            self.assertIn('is a decision', self.held_for(res, t)['why'])


class WritesAreLintValid(Fixture):
    def test_every_written_status_is_in_the_contract_enum(self):
        # Правило 12.14 судит по `fields.status.enum`. Захардкоженный где-либо
        # `doing` прошёл бы здесь молча и уронил линт на следующем прогоне.
        allowed = set(json.load(io.open(CONTRACT, encoding='utf-8'))
                      ['fields']['status']['enum'])
        for want in ts.FROM_VERDICT.values():
            self.assertIn(want, allowed,
                          '%r не в enum контракта — линтер 12.14 отвергнет' % want)

    def test_apply_writes_the_file_and_journals_every_move(self):
        self.write_tasks(task_md('M1-T1', 'Выдача', 'todo', 'K-01'))
        self.write_audit(('K-01', 'implemented', NEW))
        res = self.run_it(apply=True)
        self.assertTrue(res['applied'])

        # Утверждается РАЗОБРАННОЕ значение, а не байты строки: писатель сам решает,
        # брать ли ASCII-токен в обратные кавычки, и правило 12.14 судит по тому же
        # разобранному значению. Тест на форматирование ломался бы от смены
        # эмиттера, ничего не говоря о том, сломалось ли поведение.
        path = os.path.join(self.ms, 'history', 'TASKS.md')
        sys.path.insert(0, os.path.join(PLUGIN_DIR, 'skills', 'documents',
                                        'references'))
        import v3                                              # noqa: PLC0415
        again = v3.load_doc(path).item('M1-T1')
        self.assertEqual(str(again.get('status')).strip().lower(), 'done')
        self.assertTrue(again.get('finished'),
                        'закрытая задача осталась без даты — следующий прогон не '
                        'отличит свежее доказательство от старого')

        text = io.open(path, encoding='utf-8').read()
        self.assertIn('Проза задачи.', text, 'писатель затёр прозу вместо того, '
                                             'чтобы пропатчить одну строку')

        rows = [json.loads(l) for l in io.open(
            os.path.join(self.ms, 'history', 'ledger.jsonl'), encoding='utf-8')
            if l.strip()]
        changed = [r for r in rows if r.get('kind') == 'changed']
        self.assertEqual(len(changed), 1, 'правка без строки в журнале — дефект, '
                                          'и правило 12.36 это говорит')
        self.assertEqual(changed[0]['item'], 'M1-T1')
        self.assertEqual((changed[0]['was'], changed[0]['now']), ('todo', 'done'))

    def test_a_second_run_finds_nothing_left_to_do(self):
        # Холостой ход: применённый переход не предлагается снова. Иначе отчёт
        # каждый раз показывал бы одну и ту же работу как несделанную.
        self.write_tasks(task_md('M1-T1', 'Выдача', 'todo', 'K-01'))
        self.write_audit(('K-01', 'implemented', NEW))
        self.run_it(apply=True)
        self.assertEqual(self.run_it()['moves'], [])


class LegacyFile(Fixture):
    def test_a_v2_tasks_file_is_an_error_not_a_clean_run(self):
        io.open(os.path.join(self.ms, 'history', 'TASKS.md'), 'w',
                encoding='utf-8').write(
            '# Tasks\n\n<!-- macstack:task=M1-T1 -->\n'
            '```yaml\nstatus: todo\nspec: client/USER-CASES.md#K-01\n```\n')
        self.write_audit(('K-01', 'implemented', NEW))
        res = self.run_it()
        self.assertIn('error', res)
        self.assertIn('migrate', res['error'])


class EveryCommandThatCountsWorkChecksTheStatuses(unittest.TestCase):
    """Команда, называющая объём работ, обязана сперва сверить статусы.

    Требование было сформулировано как «все команды», и такое обещание держится на
    памяти ровно до первой новой команды. Проверяется поэтому не намерение, а вызов:
    если команда печатает список работ, в её тексте есть `task_status.py`.

    `update` и `reconcile` его ПРИМЕНЯЮТ (`--apply`), `check` и `plan` показывают.
    Разница намеренная: `check` объявлен read-only в первой своей строке, и команда,
    тихо начавшая писать, ломает единственное, что о ней знают наверняка.
    """

    COMMANDS = os.path.join(PLUGIN_DIR, 'commands')
    MUST_CALL = ('update.md', 'check.md', 'plan.md', 'reconcile.md')

    def _text(self, name):
        return io.open(os.path.join(self.COMMANDS, name), encoding='utf-8').read()

    def test_each_one_calls_the_reconciler(self):
        for name in self.MUST_CALL:
            self.assertIn('task_status.py', self._text(name),
                          '%s отчитывается о работе, не сверив статусы с вердиктами '
                          '— список либо раздут сделанным, либо короче правды' % name)

    def test_check_stays_read_only(self):
        self.assertNotIn('task_status.py" macstack --apply', self._text('check.md'),
                         'check заявлен read-only в первой строке и начал писать')

    def test_update_and_reconcile_apply(self):
        for name in ('update.md', 'reconcile.md'):
            self.assertIn('--apply', self._text(name),
                          '%s только показывает расхождение статусов, но не закрывает '
                          'его — цикл остаётся разомкнутым' % name)


if __name__ == '__main__':
    unittest.main(verbosity=2)
