#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Reconcile the BUSINESS half of macstack.json against the client's authored v2 documents.

client/AUTOMATION.md and client/UX-UI.md are written by a human and corrected by the
client; this reads their entities (roles, role tasks, triggers, screens) and reports
exactly where the spec disagrees. v1 read two tables by column POSITION and applied
value changes by regex substitution over the raw JSON text; both are gone here — entities
carry ids now (mdblocks), and the spec is edited as a Python structure
(`json.load(object_pairs_hook=collections.OrderedDict)` -> mutate -> `json.dump`) so
formatting and key order survive the round trip.

WILL change — values of entities matched unambiguously BY ID: a role_task's gate, a
trigger's schedule, a screen's path/roles, and any entity's name (its heading title).
Will NOT change anything else this script also compares (a role's cases/isolation, a
role_task's workflow, a trigger's type or its non-schedule config keys) — those are
REPORTED as `changed` but never applied. A wider "changed" report than "applied" is
deliberate: it says what differs, not just what is safe to write back automatically.

Will NOT create or delete anything, ever. A new entity needs an id, and an id is a
decision: workflows, tests and prose reference it, so a machine that invents one is a
machine that silently orphans a reference on the next rename. New and missing entities
are reported as `add` / `gone` for a human to resolve.

v1 -> v2: the document entity now carries an id in its heading, so unlike v1 (where a
task was matched by normalizing its NAME text, because no id existed anywhere) a v2
entity is matched by id alone. That makes a TITLE rename detectable and applicable — it
shows up as a `changed` `name`. Changing the ID itself still looks like one `add` plus
one `gone`, and this script reports that rather than guessing a rename.

Usage: sync-spec.py <macstack-dir> [--apply]
"""
import sys, os, io, re, json, collections

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'documents', 'references')))
from mdblocks import parse, entities  # noqa: E402
import jsonedit as J  # noqa: E402
from i18n import doc_lang, msg  # noqa: E402

CONFIG_KEYS = ('schedule', 'entity', 'event', 'condition', 'path')

ROLE_FIELDS = ('name', 'sees', 'can', 'cases', 'isolation')
SCREEN_FIELDS = ('name', 'path', 'roles')

# The rule, rather than a list somebody has to keep in step with the contract:
# APPLY any value the client document OWNS; refuse anything that would create an id or
# point at one that does not exist. The document owns the business half — roles, their
# tasks and gates, triggers and what they raise, screens and their addresses. It does
# not own what the contract's feeds.not names, and that list is short and stable.
ROLE_APPLIABLE = {'name', 'sees', 'can', 'cases', 'isolation'}
TASK_APPLIABLE = {'name', 'gate', 'role', 'workflow'}
TRIGGER_APPLIABLE = {'name', 'type', 'source', 'schedule', 'entity', 'event', 'condition', 'path'}
SCREEN_APPLIABLE = {'name', 'path', 'roles'}

# Never written from a client document, whatever it says. These are the architect's,
# measured against the code; generating them from a client's words would be a promise
# the format cannot keep, and the failure would be silent.
NEVER = {'location', 'engine', 'software', 'entities', 'status', 'instances'}

# An interface a person does not open cannot appear in UX-UI.md, so its absence there is
# not a disagreement. v1 carried this whitelist and v2 lost it, which made every API and
# channel interface report as `gone` forever.
SCREENISH = ('web', 'admin_ui', 'dashboard', 'approval_center', 'form')


def is_screen(iface):
    if (iface.get('type') or '') not in SCREENISH:
        return False
    if (iface.get('mode') or 'ui') not in ('ui', ''):
        return False
    return (iface.get('audience') or 'human') in ('human', 'both', '')


def read(path):
    with io.open(path, encoding='utf-8') as f:
        return f.read()


def title_of(block):
    h = (block.heading or '').strip()
    if '·' in h:
        return h.split('·', 1)[1].strip()
    return h


def text_of(block):
    if block is None:
        return None
    t = block.text()
    return t if t else None


# ------------------------------------------------------------------- documents
def doc_role(b):
    return {
        'id': b.id,
        'name': title_of(b),
        'cases': b.yaml.get('cases'),
        'isolation': b.yaml.get('isolation'),
        'sees': text_of(b.field('sees')),
        'can': text_of(b.field('can')),
    }


def doc_task(b):
    return {
        'id': b.id,
        'name': title_of(b),
        'role': b.yaml.get('role'),
        'gate': b.yaml.get('gate'),
        'workflow': b.yaml.get('workflow'),
    }


def doc_trigger(b):
    config = dict((k, b.yaml.get(k)) for k in CONFIG_KEYS if b.yaml.get(k) is not None)
    return {
        'id': b.id,
        'name': title_of(b),
        'type': b.yaml.get('type'),
        'config': config,
    }


def doc_screen(b):
    return {
        'id': b.id,
        'name': title_of(b),
        'path': b.yaml.get('path'),
        'roles': b.yaml.get('roles'),
    }


# --------------------------------------------------------------------- diffing
# Not "non-ASCII" — that would refuse Träger, Auswertung and every other proper noun a
# German or French project legitimately carries in an English sentence. The rule is
# SCRIPT: macstack.json is written in the Latin script.
NON_LATIN = re.compile(
    u'[\u0370-\u03FF\u0400-\u052F\u0590-\u05FF\u0600-\u06FF\u0900-\u097F'
    u'\u0E00-\u0E7F\u1100-\u11FF\u2E80-\u9FFF\uAC00-\uD7AF\uF900-\uFAFF]')


def is_english(v):
    """macstack.json is ALWAYS English — the standard says so and every downstream
    consumer assumes it.

    The client documents are not: docs.language is exactly the field that says so. So a
    value can only cross from a Russian, German or Ukrainian document into the spec if it
    carries no non-ASCII letter. That admits everything structural — a path, a cron
    expression, a gate, a role id, an enum member — and refuses everything that is prose
    in the document's own language.

    Caught by running --apply on the live project: applying screen names from the
    migrated Russian document rewrote thirteen English `interfaces[].name` values into
    Cyrillic. Nothing failed; the spec simply stopped being what the standard promises.

    The test is the SCRIPT, not the byte range. A first cut refused every non-ASCII
    character and would have blocked `Träger` and `Auswertung` — words that were already
    in the spec, in English sentences, because they are the client's own proper nouns."""
    if isinstance(v, (list, tuple)):
        return all(is_english(x) for x in v)
    if isinstance(v, dict):
        return all(is_english(x) for x in v.values())
    return not NON_LATIN.search(str(v or ''))


def is_blank(v):
    """A value a converter or a seed left unfilled."""
    if v is None:
        return True
    if isinstance(v, (list, tuple, dict)):
        return len(v) == 0
    s = str(v).strip()
    return s in ('', '—', '-', '~') or s.startswith('_TODO')


def would_erase(doc_value, spec_value):
    """A blank in the document over a populated spec value is not a correction.

    Seen live: the migrator could not turn the prose cell "все без входа" into role ids,
    so the screen came out with `roles: []`. Applying that would have deleted a correct
    list from the spec on the authority of a cell nobody had rewritten yet. A blank is a
    gap in the document, and a gap is reported, never propagated."""
    return is_blank(doc_value) and not is_blank(spec_value)


def id_exists(spec, coll, ident):
    if not ident:
        return True
    if coll == 'workflows':
        return any(w.get('id') == ident for w in (spec.get('workflows') or []))
    if coll == 'roles':
        return any(r.get('id') == ident for r in (spec.get('roles') or []))
    return True


def mk_change(kind, id_, field, have, want, appliable, apply_fn):
    if would_erase(want, have) or not is_english(want):
        appliable, apply_fn = False, None
    return {'kind': kind, 'id': id_, 'field': field, 'have': have, 'want': want,
            'appliable': appliable, 'apply': apply_fn}


CONFIG_FIELDS = ('schedule', 'entity', 'event', 'condition', 'path')


def path_of(spec, rec):
    """The JSON path of a change, so it can be written as TEXT rather than by
    reserializing the file.

    json.dump(indent=2) on a live spec turned 959 lines into 4119 — the file is
    hand-formatted, short objects inlined, and a whole-file reformat makes a one-value
    change unreviewable. The parse decides WHAT to change; the path says WHERE."""
    kind, ident, field = rec['kind'], rec['id'], rec['field']
    if kind == 'role':
        for i, r in enumerate(spec.get('roles') or []):
            if r.get('id') == ident:
                return ['roles', i, field]
    elif kind == 'role_task':
        for pi, pr in enumerate(spec.get('processes') or []):
            for ti, tk in enumerate(pr.get('tasks') or []):
                if tk.get('id') == ident:
                    base = ['processes', pi, 'tasks', ti]
                    if field in ('gate', 'role'):
                        return base + ['human', field]
                    return base + [field]
    elif kind == 'trigger':
        for i, x in enumerate(spec.get('triggers') or []):
            if x.get('id') == ident:
                if field in CONFIG_FIELDS:
                    return ['triggers', i, 'config', field]
                return ['triggers', i, field]
    elif kind == 'screen':
        for i, x in enumerate(spec.get('interfaces') or []):
            if x.get('id') == ident:
                return ['interfaces', i, field]
    return None


SPEC = {}


def compare_roles(doc_roles, spec_roles):
    add, gone, changed = [], [], []
    spec_by_id = dict((r.get('id'), r) for r in spec_roles)
    doc_by_id = dict((r['id'], r) for r in doc_roles)
    for rid, d in doc_by_id.items():
        if rid not in spec_by_id:
            add.append(('role', rid, d['name']))
            continue
        s = spec_by_id[rid]
        for f in ROLE_FIELDS:
            dv, sv = d.get(f), s.get(f)
            if dv is not None and dv != sv:
                appliable = f in ROLE_APPLIABLE
                fn = (lambda s=s, f=f, dv=dv: s.__setitem__(f, dv)) if appliable else None
                changed.append(mk_change('role', rid, f, sv, dv, appliable, fn))
    for rid, s in spec_by_id.items():
        if rid not in doc_by_id:
            gone.append(('role', rid, s.get('name')))
    return add, gone, changed


def all_spec_tasks(spec):
    for p in (spec.get('processes') or []):
        for t in (p.get('tasks') or []):
            if t.get('id'):
                yield t


def compare_tasks(doc_tasks, spec):
    add, gone, changed = [], [], []
    spec_by_id = dict((t['id'], t) for t in all_spec_tasks(spec))
    doc_by_id = dict((t['id'], t) for t in doc_tasks)
    for tid, d in doc_by_id.items():
        if tid not in spec_by_id:
            add.append(('role_task', tid, d['name']))
            continue
        t = spec_by_id[tid]
        human = t.get('human') or {}
        if d.get('name') is not None and d['name'] != t.get('name'):
            changed.append(mk_change('role_task', tid, 'name', t.get('name'), d['name'], True,
                                      lambda t=t, dv=d['name']: t.__setitem__('name', dv)))
        if d.get('gate') is not None and d['gate'] != human.get('gate'):
            def apply_gate(t=t, dv=d['gate']):
                h = t.get('human')
                if h is None:
                    h = type(t)()
                    t['human'] = h
                h['gate'] = dv
            changed.append(mk_change('role_task', tid, 'gate', human.get('gate'), d['gate'], True, apply_gate))
        if d.get('role') is not None and d['role'] != human.get('role'):
            def apply_role(t=t, dv=d['role']):
                h = t.get('human')
                if h is None:
                    h = type(t)()
                    t['human'] = h
                h['role'] = dv
            changed.append(mk_change('role_task', tid, 'role', human.get('role'), d['role'],
                                     'role' in TASK_APPLIABLE, apply_role))
        if d.get('workflow') is not None and d['workflow'] != t.get('workflow'):
            # a workflow id the spec does not declare is a dangling reference, not a value
            ok = 'workflow' in TASK_APPLIABLE and id_exists(SPEC, 'workflows', d['workflow'])
            changed.append(mk_change('role_task', tid, 'workflow', t.get('workflow'), d['workflow'],
                                     ok, (lambda t=t, dv=d['workflow']: t.__setitem__('workflow', dv)) if ok else None))
    for tid, t in spec_by_id.items():
        if tid not in doc_by_id:
            gone.append(('role_task', tid, t.get('name')))
    return add, gone, changed


def compare_triggers(doc_triggers, spec_triggers):
    add, gone, changed = [], [], []
    spec_by_id = dict((t.get('id'), t) for t in spec_triggers)
    doc_by_id = dict((t['id'], t) for t in doc_triggers)
    for tid, d in doc_by_id.items():
        if tid not in spec_by_id:
            add.append(('trigger', tid, d['name']))
            continue
        s = spec_by_id[tid]
        if d.get('name') is not None and d['name'] != s.get('name'):
            changed.append(mk_change('trigger', tid, 'name', s.get('name'), d['name'], True,
                                      lambda s=s, dv=d['name']: s.__setitem__('name', dv)))
        if d.get('type') is not None and d['type'] != s.get('type'):
            changed.append(mk_change('trigger', tid, 'type', s.get('type'), d['type'],
                                     'type' in TRIGGER_APPLIABLE,
                                     lambda s=s, dv=d['type']: s.__setitem__('type', dv)))
        s_config = s.get('config') or {}
        for k in CONFIG_KEYS:
            dv = d['config'].get(k)
            sv = s_config.get(k)
            if dv is not None and dv != sv:
                appliable = k in TRIGGER_APPLIABLE

                def apply_cfg(s=s, k=k, dv=dv):
                    cfg = s.get('config')
                    if cfg is None:
                        cfg = type(s)()
                        s['config'] = cfg
                    cfg[k] = dv
                changed.append(mk_change('trigger', tid, k, sv, dv, appliable, apply_cfg if appliable else None))
    for tid, s in spec_by_id.items():
        if tid not in doc_by_id:
            gone.append(('trigger', tid, s.get('name')))
    return add, gone, changed


def compare_screens(doc_screens, spec_interfaces):
    spec_interfaces = [i for i in spec_interfaces if is_screen(i)]
    add, gone, changed = [], [], []
    spec_by_id = dict((i.get('id'), i) for i in spec_interfaces)
    doc_by_id = dict((s['id'], s) for s in doc_screens)
    for sid, d in doc_by_id.items():
        if sid not in spec_by_id:
            add.append(('screen', sid, d['name']))
            continue
        s = spec_by_id[sid]
        for f in SCREEN_FIELDS:
            dv, sv = d.get(f), s.get(f)
            if dv is not None and dv != sv:
                appliable = f in SCREEN_APPLIABLE
                fn = (lambda s=s, f=f, dv=dv: s.__setitem__(f, dv)) if appliable else None
                changed.append(mk_change('screen', sid, f, sv, dv, appliable, fn))
    for sid, s in spec_by_id.items():
        if sid not in doc_by_id:
            gone.append(('screen', sid, s.get('name')))
    return add, gone, changed


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    root = args[0] if args else 'macstack'
    apply_ = '--apply' in sys.argv
    lang = doc_lang(root)

    spec_p = os.path.join(root, 'macstack.json')
    if not os.path.exists(spec_p):
        print(msg(lang, 'no_spec', dir=root))
        return 1
    with io.open(spec_p, encoding='utf-8') as f:
        spec = json.load(f, object_pairs_hook=collections.OrderedDict)
    global SPEC
    SPEC = spec

    auto_p = os.path.join(root, 'client', 'AUTOMATION.md')
    if not os.path.exists(auto_p):
        print('missing: %s' % auto_p)
        return 1
    _, auto_blocks = parse(read(auto_p))
    doc_roles = [doc_role(b) for b in entities(auto_blocks, 'role')]
    doc_tasks = [doc_task(b) for b in entities(auto_blocks, 'task')]
    doc_triggers = [doc_trigger(b) for b in entities(auto_blocks, 'trigger')]

    doc_screens = []
    ux_p = os.path.join(root, 'client', 'UX-UI.md')
    if os.path.exists(ux_p):
        _, ux_blocks = parse(read(ux_p))
        doc_screens = [doc_screen(b) for b in entities(ux_blocks, 'screen')]

    add, gone, changed = [], [], []
    for a, g, c in (
        compare_roles(doc_roles, spec.get('roles') or []),
        compare_tasks(doc_tasks, spec),
        compare_triggers(doc_triggers, spec.get('triggers') or []),
        compare_screens(doc_screens, spec.get('interfaces') or []),
    ):
        add += a
        gone += g
        changed += c

    print('=== add (%d) — in the document, not in the spec ===' % len(add))
    for kind, id_, name in add:
        print('  + %-10s %-20s %s' % (kind, id_, name or ''))
    print('\n=== gone (%d) — in the spec, not in the document ===' % len(gone))
    for kind, id_, name in gone:
        print('  - %-10s %-20s %s' % (kind, id_, name or ''))
    print('\n=== changed (%d) — id matched, values differ ===' % len(changed))
    for rec in changed:
        if rec['appliable']:
            tag = ''
        elif not is_english(rec['want']):
            tag = '  [not applied — macstack.json stays in the Latin script]'
        elif would_erase(rec['want'], rec['have']):
            tag = '  [not applied — a blank in the document would erase the spec]'
        else:
            tag = '  [report only, not applied]'
        print('  ~ %-10s %-16s %-10s spec=%r  doc=%r%s' %
              (rec['kind'], rec['id'], rec['field'], rec['have'], rec['want'], tag))

    if apply_:
        raw = io.open(spec_p, encoding='utf-8').read()
        before = len(raw.splitlines())
        applied, skipped = 0, []
        for r in changed:
            if not r['appliable']:
                continue
            path = path_of(spec, r)
            if path is None:
                skipped.append('%s %s.%s — could not locate it in the spec' % (r['kind'], r['id'], r['field']))
                continue
            try:
                raw = J.set_value(raw, path, r['want'])
                applied += 1
            except Exception as e:
                # a refused edit is reported, never forced: the alternative is a spec
                # that parses and says something nobody asked for
                skipped.append('%s %s.%s — %s' % (r['kind'], r['id'], r['field'], e))
        if applied:
            io.open(spec_p, 'w', encoding='utf-8').write(raw)
            print('\n  %d lines before, %d after — formatting preserved' % (before, len(raw.splitlines())))
        for s in skipped:
            print('  not written: %s' % s)
        print('\n%s: %d' % (msg(lang, 'applied'), applied))
    elif changed:
        print('\n' + msg(lang, 'dry_run'))

    if add or gone:
        print('\nadd/gone are never applied automatically — a new id is a decision for a human.')

    return 0


if __name__ == '__main__':
    sys.exit(main())
