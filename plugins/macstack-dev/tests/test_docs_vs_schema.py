#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Документация плагина говорит о схеме то, что в схеме есть.

Run: python3 tests/test_docs_vs_schema.py

Скиллы, README и агент называют поля спецификации по путям: `workflows[].source`,
`roles[].isolation`, `lifecycle.next_steps[]`. Схема меняется (rev 14–18), а тексты
остаются, и расхождение никому не видно: документ читается гладко и описывает поле,
которого нет. Измерено на волне 2: три скилла и README описывали `triggers[].source`
как поле спецификации — в схеме его нет, `source` существует только как пункт самого
документа AUTOMATION.md, выводимый из `type`; `sync` советовал сверять код с
`workflows[].location`, когда путь к коду называется `workflows[].source` (rev 15);
`planning` ссылался на `lifecycle.tasks[]`, которого нет вовсе (есть
`lifecycle.next_steps[]` и `lifecycle.milestones[]`); `technical` (rev 14) был описан
только для сущностей, хотя схема даёт его ещё `software[]` и `workflows[]`.

Две проверки:

  * ОБЩАЯ: каждый путь вида `a.b[].c` в обратных кавычках, начинающийся с верхнеуровневого
    раздела схемы, существует в схеме. История (`LEARNINGS.md`) и сама схема не
    проверяются; исключения названы поимённо и с причиной.
  * ТОЧЕЧНЫЕ: места, где ошибка уже была, — чтобы она не вернулась словами, которых
    общая проверка не поймает (`source` без пути вокруг него).
"""
import io
import json
import os
import re
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.dirname(HERE)
SKILLS = os.path.join(PLUGIN, 'skills')
SCHEMA = json.load(io.open(os.path.join(SKILLS, 'lint', 'references',
                                        'macstack.schema.json'), encoding='utf-8'))

# Путь, который текст называет намеренно, хотя в схеме его нет.
ALLOWED = {
    'processes[].sla': 'feedback/SKILL.md: пример предложения расширить схему — поле гипотетическое',
}


def read(*parts):
    with io.open(os.path.join(PLUGIN, *parts), encoding='utf-8') as fh:
        return fh.read()


def flat(*parts):
    """Текст с пробельными пробегами, сведёнными к одному пробелу: фраза, перенесённая
    на другую строку, остаётся той же фразой."""
    return re.sub(r'\s+', ' ', read(*parts))


# ---------------------------------------------------------------- схема как дерево
def _deref(node):
    for _ in range(10):
        if isinstance(node, dict) and '$ref' in node:
            cur = SCHEMA
            for part in node['$ref'][2:].split('/'):
                cur = cur[part]
            node = cur
        else:
            break
    return node


def _alts(node):
    node = _deref(node)
    out = [node]
    if isinstance(node, dict):
        for key in ('oneOf', 'anyOf', 'allOf'):
            for sub in node.get(key, []):
                out += _alts(sub)
    return out


def resolves(path):
    nodes = [SCHEMA]
    for seg in path.split('.'):
        arr = seg.endswith('[]')
        name = seg[:-2] if arr else seg
        nxt = []
        for n in nodes:
            for a in _alts(n):
                props = a.get('properties', {})
                if name in props:
                    nxt.append(props[name])
                elif isinstance(a.get('additionalProperties'), dict):
                    nxt.append(a['additionalProperties'])
        if not nxt:
            return False
        if arr:
            nxt = [a['items'] for n in nxt for a in _alts(n) if 'items' in a]
            if not nxt:
                return False
        nodes = nxt
    return True


CITED = re.compile(r'`([a-z_]+(?:\.[a-z_]+)*\[\](?:\.[a-z_]+(?:\[\])?)*)`')
TOP = set(SCHEMA['properties'])


def documents():
    for root, _dirs, files in os.walk(PLUGIN):
        if os.sep + 'tests' in root or '__pycache__' in root:
            continue
        for name in files:
            if name in ('LEARNINGS.md',) or 'macstack.schema' in name:
                continue
            if name.endswith(('.md', '.py', '.json')):
                yield os.path.join(root, name)


class EveryCitedPathExists(unittest.TestCase):
    def test_no_document_cites_a_path_the_schema_does_not_have(self):
        bad = []
        for path in documents():
            text = read(path).replace('macstack.json.', '')
            for m in CITED.finditer(text):
                p = m.group(1)
                if p.split('.')[0].replace('[]', '') not in TOP or p in ALLOWED:
                    continue
                if not resolves(p):
                    bad.append('%s: `%s`' % (os.path.relpath(path, PLUGIN), p))
        self.assertEqual(bad, [], 'путь, которого нет в схеме:\n' + '\n'.join(sorted(set(bad))))

    def test_the_resolver_knows_a_missing_path_from_a_present_one(self):
        # Без этого «всё нашлось» могло бы значить «ничего не проверялось».
        self.assertTrue(resolves('workflows[].source'))
        self.assertTrue(resolves('lifecycle.next_steps[].status'))
        self.assertTrue(resolves('roles[].isolation'))
        self.assertFalse(resolves('triggers[].source'))
        self.assertFalse(resolves('lifecycle.tasks[].status'))


class TheSpotsThatWereWrong(unittest.TestCase):
    def test_triggers_have_no_source_in_the_spec(self):
        # опорный факт, на котором стоят остальные три проверки
        trig = SCHEMA['properties']['triggers']['items']['properties']
        self.assertNotIn('source', trig)

    def test_sync_does_not_list_source_among_the_trigger_fields_it_syncs(self):
        text = flat('skills', 'sync', 'SKILL.md')
        self.assertNotIn('triggers, type, source, schedule', text)

    def test_sync_checks_workflows_against_their_source_path(self):
        text = read('skills', 'sync', 'SKILL.md')
        self.assertIn('workflows[].source', text)
        self.assertNotIn('workflows[].location', text)

    def test_no_text_describes_a_trigger_source_as_a_spec_field(self):
        # В README и documents/SKILL.md `source` законно назван: это пункт документа.
        # Сказано ли это — вот что проверяется.
        for rel in (('README.md',), ('skills', 'documents', 'SKILL.md')):
            text = flat(*rel)
            i = text.index('its `source`')
            window = text[max(0, i - 200):i + 500]
            self.assertRegex(window, r'(?i)document[- ]only|only in the document',
                             '/'.join(rel))

    def test_spec_authoring_does_not_ask_the_trigger_for_a_source(self):
        text = flat('skills', 'spec-authoring', 'SKILL.md')
        self.assertNotIn('of which `type`, from which `source`', text)

    def test_the_dead_trigger_source_entry_is_gone(self):
        text = read('skills', 'sync', 'references', 'sync-spec.py')
        line = [l for l in text.splitlines() if l.startswith('TRIGGER_APPLIABLE')][0]
        self.assertNotIn("'source'", line)

    def test_technical_is_documented_for_software_and_workflows_too(self):
        for rel in (('skills', 'spec-authoring', 'SKILL.md'),
                    ('agents', 'macstack-architect.md')):
            text = read(*rel)
            hits = [m.start() for m in re.finditer(r'technical: true', text)]
            self.assertTrue(hits, '%s: `technical: true` не упомянут' % '/'.join(rel))
            window = ' '.join(text[max(0, i - 400):i + 400] for i in hits)
            for kind in ('software[]', 'workflows[]', 'entities[]'):
                self.assertIn(kind, window, '%s: technical без %s' % ('/'.join(rel), kind))

    def test_planning_names_the_real_mirror_paths(self):
        text = read('skills', 'planning', 'SKILL.md')
        self.assertNotIn('lifecycle.tasks[]', text)
        self.assertIn('lifecycle.next_steps[]', text)

    def test_no_text_still_calls_a_task_doing_or_blocked_a_status(self):
        for rel in (('skills', 'lint', 'SKILL.md'),):
            text = read(*rel)
            self.assertNotIn('sitting in `doing`', text)
            self.assertNotIn('M11 · doing', text)
        self.assertNotIn('`todo`/`doing` tasks', read('skills', 'planning', 'SKILL.md'))

    def test_documents_skill_lists_the_rev18_file_keys_and_not_a_bare_log(self):
        text = read('skills', 'documents', 'SKILL.md')
        for key in ('ledger', 'requirements', 'review', 'inbox_manifest'):
            self.assertIn('`%s`' % key, text)
        self.assertNotIn('`changelog`, `log` —', text)


if __name__ == '__main__':
    unittest.main(verbosity=2)
