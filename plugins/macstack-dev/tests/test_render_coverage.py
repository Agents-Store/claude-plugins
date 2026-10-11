#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Генератор: тесты на shell видны покрытию, а сущности при нескольких master не
несут незаявленного поля.

Run: python3 tests/test_render_coverage.py

Два дефекта, найденные на живом проекте, чьи тесты — наборы на bash:

  * **Покрытие не видело shell.** `scan_tests` читал только файлы с расширениями
    JS/TS/Python/Ruby. Сценарный тест, написанный на bash или bats, не мог доказать
    кейс в принципе — 12.11 называл «не покрыт» каждый кейс проекта, сколько бы
    тестов там ни было. Название теста в shell — первая строка-аргумент вызова
    (`ok "C-04 …"`, `expect_fail "C-04 …"`) или `@test "…"` у bats.
  * **`master` в ARCHITECTURE.md.** При нескольких master сущности сгруппированы
    под заголовком `**master:** …`, и каждая ещё раз несла `- **master:**`. Метка не
    заявлена в doc-contracts.json, и 12.31 ругался на каждую сущность — на
    сгенерированный файл, который человек поправить не может.
"""
import os
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN_DIR = os.path.dirname(HERE)
DOCS = os.path.join(PLUGIN_DIR, 'skills', 'documents', 'references')

sys.path.insert(0, DOCS)
import render                                                  # noqa: E402


def _write(root, rel, text):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)


class ShellTestsCount(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def test_bash_suite_title_names_a_case(self):
        _write(self.root, 'scripts/tests/e2e/onboarding.test.sh',
               'ok "C-04 colleague gets every account"\n'
               'expect_fail "C-05.a2 a second invite is refused" \'.x\' "refused"\n')
        hits = render.scan_tests(self.root)
        self.assertIn('C-04', hits)
        self.assertIn('C-05.a2', hits)
        self.assertEqual(hits['C-04'][0][0],
                         os.path.join('scripts', 'tests', 'e2e', 'onboarding.test.sh'))

    def test_bats_title_names_a_case(self):
        _write(self.root, 'test/scenario/sign.bats',
               '@test "C-07 a signed PDF carries the seal" {\n  run true\n}\n')
        self.assertIn('C-07', render.scan_tests(self.root))

    def test_shell_line_without_a_case_id_counts_nothing(self):
        _write(self.root, 'scripts/tests/run.test.sh',
               'echo "the read-only workflow"\nok "passes"\n')
        self.assertEqual(render.scan_tests(self.root), {})

    def test_plain_shell_script_is_not_a_test(self):
        _write(self.root, 'scripts/deploy.sh', 'ok "C-04 not a test file"\n')
        self.assertEqual(render.scan_tests(self.root), {})

    def test_js_titles_still_count(self):
        _write(self.root, 'tests/e2e/entry.spec.ts', "it('C-06 marks the session', () => {})\n")
        self.assertIn('C-06', render.scan_tests(self.root))


class SeveralMastersNoMasterBullet(unittest.TestCase):
    SPEC = {'entities': [
        {'id': 'candidate', 'name': 'Candidate', 'master': 'nocobase',
         'stores': [{'software': 'nocobase'}]},
        {'id': 'secret', 'name': 'Secret', 'master': 'infisical',
         'stores': [{'software': 'infisical'}]},
    ]}

    def test_entities_grouped_without_a_master_bullet(self):
        for lang in ('en', 'ru'):
            text = render.render_architecture(self.SPEC, lang)
            bullets = [l for l in text.split('\n') if l.startswith('- **master:**')]
            self.assertEqual(bullets, [], lang)
            self.assertIn('`nocobase`', text)
            self.assertIn('`infisical`', text)


if __name__ == '__main__':
    unittest.main()
