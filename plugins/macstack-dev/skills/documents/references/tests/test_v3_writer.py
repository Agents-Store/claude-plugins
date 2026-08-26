#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""The three properties that define the v3 writer, plus the two regressions
the cardinality census exists to hold.

Run: python3 skills/documents/references/tests/test_v3_writer.py

Why unittest and not pytest: this plugin ships with no dependencies, and a test
suite that cannot run on the machine it validates is not a test suite.

P1  identity          — load_doc(p).text() is the file, byte for byte.
P2  idempotent write  — writing a field its current value changes nothing.
P3  emit determinism  — same arguments, same bytes.

P1 is nearly free and only guards the reader. P2 is the one that can break, and
it is the property that makes `sync --write` safe: 75% of a live client document
is prose no model represents, so a writer that re-renders destroys it. The
comparison is on the PARSED value, never on bytes — 'критично' and 'Критично.'
are the same priority, and a cron the human wrote bare must not gain backticks.
"""
import glob, io, os, sys, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import v3

CLIENT = os.environ.get('MACSTACK_FIXTURE') or (
    '/Users/valentynkubrak/STACKS/stackmakers-dev-ops/'
    'projects/ohawo-payload-nextjs/macstack/client')
DOCS = sorted(glob.glob(os.path.join(CLIENT, '*.md')))

# Measured 2026-08-26 on the live corpus. A change here is never a test to
# relax: it means a pointer relation moved, and the only way that happens
# quietly is somebody inventing a spec entry to satisfy a lint rule.
CENSUS = {
    'AUTOMATION.md':     dict(headings=57, pointers=57, targets=57, same=57, none=0),
    'HANDBOOK.md':       dict(headings=0,  pointers=0,  targets=0,  same=0,  none=0),
    'OPEN-QUESTIONS.md': dict(headings=26, pointers=22, targets=22, same=22, none=4),
    'OVERVIEW.md':       dict(headings=10, pointers=10, targets=10, same=10, none=0),
    'USER-CASES.md':     dict(headings=78, pointers=78, targets=78, same=78, none=0),
    'UX-UI.md':          dict(headings=37, pointers=37, targets=9,  same=9,  none=0),
}


def read(p):
    return io.open(p, encoding='utf-8').read()


class P1Identity(unittest.TestCase):
    """The document is its lines. Reading then writing changes nothing."""


class P2IdempotentWrite(unittest.TestCase):
    """Writing a field the value it already holds must not touch the file."""


class P3EmitDeterminism(unittest.TestCase):
    def test_emit_entity_is_deterministic(self):
        a = v3.emit_entity('case', 'C-16', u'Проверка',
                           fields={'priority': 'important', 'screens': ['a', 'b']},
                           lang='ru')
        b = v3.emit_entity('case', 'C-16', u'Проверка',
                           fields={'priority': 'important', 'screens': ['a', 'b']},
                           lang='ru')
        self.assertEqual(a, b)


class LabelsDeclared(unittest.TestCase):
    """Every bullet label in the corpus reverses to a field key.

    Measured before the fix: 103 of 430 labels did not — 66 in AUTOMATION.md
    alone, where the table said 'что требуется от человека' and all 33 live
    bullets say 'что от человека требуется'. Each one became a raw Cyrillic
    dict key that no consumer reads, and nothing reported it.
    """

    def test_no_unmapped_labels(self):
        bad = []
        for p in DOCS:
            txt = read(p)
            lang = v3.header(txt).get('lang', 'ru')
            tbl = v3.LABELS.get(lang) or v3.LABELS['en']
            for n, line in enumerate(txt.splitlines(), 1):
                m = v3.BULLET.match(line)
                if m and m.group(1).strip().lower() not in tbl:
                    bad.append('%s:%d %s' % (os.path.basename(p), n, m.group(1)))
        self.assertEqual(bad, [], '%d unmapped labels\n%s'
                         % (len(bad), '\n'.join(bad[:12])))


class CardinalityCensus(unittest.TestCase):
    """Pointer binding is not one relation, and this is the proof.

    identity  AUTOMATION, OVERVIEW, USER-CASES   heading id == pointer id
    container UX-UI                              37 headings -> 9 interfaces[]
    none      4 closed open items                struck through, no longer owed

    Schema rev 13 changed two of these on purpose. Before it there was no cases[] to
    point at, so a case pointed at the ROLE that owned it — membership in the glob
    'C-*' — and the 27 cross-cutting cases and prohibitions, which belong to no role,
    carried no pointer at all. Now every case names its own record, and the member
    binding has no user left in this corpus. It stays in the contract because the
    relation is real; a project whose documents predate rev 13 will still use it.

    The eight processes that OVERVIEW.md used to head are now a list: the heading and
    the id were duplicated verbatim in two documents, which is one rename away from a
    disagreement nobody would notice.
    """

    def test_census_unchanged(self):
        import re
        for p in DOCS:
            name = os.path.basename(p)
            if name not in CENSUS:
                continue
            items = v3.load(p)
            ids = [i.id for i in items if i.id]
            ptr = [(i.id, i.ref) for i in items if i.id and i.ref]
            last = []
            for _id, q in ptr:
                m = re.findall(r'\[id=([^\]]+)\]', q or '')
                last.append(m[-1] if m else None)
            got = dict(headings=len(ids), pointers=len(ptr),
                       targets=len(set(x for x in last if x)),
                       same=sum(1 for (i, _), l in zip(ptr, last) if i == l),
                       none=len(ids) - len(ptr))
            self.assertEqual(got, CENSUS[name], name)


def _bind(cls, name, fn):
    setattr(cls, name, fn)


for _p in DOCS:
    _n = os.path.basename(_p).replace('.', '_').replace('-', '_').lower()

    def _p1(self, p=_p):
        self.assertEqual(v3.load_doc(p).text(), read(p))
    _bind(P1Identity, 'test_identity_' + _n, _p1)

    def _p2(self, p=_p):
        doc = v3.load_doc(p)
        for it in doc.items:
            for k, v in list(it.fields.items()):
                self.assertIs(v3.set_field(doc, it, k, v), False,
                              '%s %s.%s rewrote an unchanged value' %
                              (os.path.basename(p), it.id, k))
        self.assertFalse(doc.dirty)
        self.assertEqual(doc.text(), read(p))
    _bind(P2IdempotentWrite, 'test_idempotent_' + _n, _p2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
