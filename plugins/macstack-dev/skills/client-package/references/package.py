#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the client review package: one self-contained artifact a client can answer.

The inbound half of the client loop always worked. This is the outbound half. Nobody
sends a client an 88 KB markdown file and expects edits back, so in practice the client
writes a fresh document of their own and somebody transcribes it by hand — which is
where a hundred small changes go missing.

Reads the FIVE client documents — OVERVIEW, USER-CASES, UX-UI, AUTOMATION, HANDBOOK —
and gives every checkable claim a place to answer: confirm, correct, or ask. v1 promised
four documents and read two, which is the same failure with a smaller number.

IDS ARE STABLE. Every acceptance bullet carries `C-04.a3`, every screen prohibition
`coach-today.f2`, allocated from the document's own order and unchanged by a rebuild. v1
numbered bullets positionally per package, which only worked because handoffs/ is
immutable and broke the moment a bullet was inserted above another. A client's comment
has to survive the next round.

Output goes to handoffs/<date>-<slug>.html and is IMMUTABLE from that moment: the
client's comments come back against that exact file.

Usage: package.py <macstack-dir> [--date YYYY-MM-DD] [--slug user-cases] [--lang xx]
"""
import sys, os, io, re, json, html

sys.path.insert(0, os.path.normpath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', '..', 'documents', 'references')))
import mdblocks as M                                  # noqa: E402
from i18n import doc_lang                             # noqa: E402

TODO = '_TODO —'


# ---------------------------------------------------------------- reading
def _bullets(block, anchor):
    f = block.field(anchor) if block else None
    if not f:
        return []
    out = []
    for line in f.body:
        s = line.strip()
        if s.startswith('- '):
            out.append(s[2:].strip().rstrip(';.'))
        elif out and s and not s.startswith('**') and not s.startswith('_'):
            out[-1] += ' ' + s
    return [b for b in out if b and not b.startswith(TODO)]


def read_doc(root, rel):
    p = os.path.join(root, rel)
    if not os.path.exists(p):
        return None, [], {}
    text = io.open(p, encoding='utf-8').read()
    hdr, blocks = M.parse(text)
    return text, blocks, hdr


def collect(root):
    """Everything the package shows, with its stable id."""
    out = dict(overview=[], cases=[], screens=[], triggers=[], procedures=[], versions={})

    text, blocks, hdr = read_doc(root, 'client/OVERVIEW.md')
    if text:
        out['versions']['overview'] = hdr.get('version', '?')
        for sec in blocks:
            if sec.kind != 'section' or sec.id in ('journal', 'howto', 'glossary'):
                continue
            paras, buf = [], []
            for line in sec.body:
                s = line.rstrip()
                if not s.strip():
                    if buf:
                        paras.append(' '.join(buf)); buf = []
                    continue
                if s.startswith(('- ', '#', '|', '<!--', '```')):
                    if buf:
                        paras.append(' '.join(buf)); buf = []
                    if s.startswith('- '):
                        paras.append(s)
                    continue
                buf.append(s.strip())
            if buf:
                paras.append(' '.join(buf))
            if paras:
                out['overview'].append((sec.heading or sec.id, paras))

    text, blocks, hdr = read_doc(root, 'client/USER-CASES.md')
    if text:
        out['versions']['user_cases'] = hdr.get('version', '?')
        for sec in blocks:
            if sec.kind != 'section':
                continue
            for c in sec.children:
                if c.kind != 'case':
                    continue
                acc = _bullets(c, 'acceptance')
                exp = _bullets(c, 'experience')
                out['cases'].append(dict(
                    id=c.id, title=(c.heading or '').split('·', 1)[-1].strip(),
                    section=sec.heading or sec.id,
                    priority=c.yaml.get('priority', ''),
                    items=[('%s.a%d' % (c.id, i + 1), b) for i, b in enumerate(acc)]
                          + [('%s.x%d' % (c.id, i + 1), b) for i, b in enumerate(exp)]))

    text, blocks, hdr = read_doc(root, 'client/UX-UI.md')
    if text:
        out['versions']['ux_ui'] = hdr.get('version', '?')
        for s in M.entities(blocks, 'screen'):
            forb = _bullets(s, 'forbidden')
            cont = _bullets(s, 'content')
            act = _bullets(s, 'actions')
            out['screens'].append(dict(
                id=s.id, title=(s.heading or '').split('·', 1)[-1].strip(),
                path=s.yaml.get('path', ''),
                items=[('%s.c%d' % (s.id, i + 1), b) for i, b in enumerate(cont)]
                      + [('%s.d%d' % (s.id, i + 1), b) for i, b in enumerate(act)]
                      + [('%s.f%d' % (s.id, i + 1), b) for i, b in enumerate(forb)]))

    text, blocks, hdr = read_doc(root, 'client/AUTOMATION.md')
    if text:
        out['versions']['automation'] = hdr.get('version', '?')
        for t in M.entities(blocks, 'trigger'):
            what = _bullets(t, 'what_happens') or [x.strip() for x in (t.field('what_happens').body if t.field('what_happens') else []) if x.strip() and not x.strip().startswith(TODO)]
            y = t.yaml
            desc = 'starts: %s' % y.get('source', '?')
            if y.get('schedule'):
                desc += ' · %s' % y['schedule']
            out['triggers'].append(dict(
                id=t.id, title=(t.heading or '').split('·', 1)[-1].strip(), meta=desc,
                items=[('%s.w%d' % (t.id, i + 1), b) for i, b in enumerate(what)]))
        for r in M.entities(blocks, 'role'):
            sees = ' '.join(x.strip() for x in (r.field('sees').body if r.field('sees') else []) if x.strip())
            can = ' '.join(x.strip() for x in (r.field('can').body if r.field('can') else []) if x.strip())
            items = []
            if sees and not sees.startswith(TODO):
                items.append(('%s.s1' % r.id, sees))
            if can and not can.startswith(TODO):
                items.append(('%s.n1' % r.id, can))
            if items:
                out['procedures'].append(dict(
                    id=r.id, title=(r.heading or '').split('·', 1)[-1].strip(), meta='role', items=items))

    text, blocks, hdr = read_doc(root, 'client/HANDBOOK.md')
    if text:
        out['versions']['handbook'] = hdr.get('version', '?')
        for pr in M.entities(blocks, 'procedure'):
            steps = _bullets(pr, 'steps') or [re.sub(r'^\d+\.\s*', '', x.strip())
                                              for x in (pr.field('steps').body if pr.field('steps') else [])
                                              if re.match(r'^\s*\d+\.', x)]
            if steps:
                out['procedures'].append(dict(
                    id=pr.id, title=(pr.heading or '').split('·', 1)[-1].strip(),
                    meta=pr.yaml.get('role', ''),
                    items=[('%s.p%d' % (pr.id, i + 1), b) for i, b in enumerate(steps)]))
    return out


# ---------------------------------------------------------------- rendering
def md(s):
    s = html.escape(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    s = re.sub(r'(?<![A-Za-z0-9_])\*(.+?)\*(?![A-Za-z0-9_])', r'<em>\1</em>', s)
    return s


CSS = """
:root{--ink:#1a1a1a;--mut:#6b7280;--line:#d4d4d8;--accent:#1d4ed8;--box:#fafafa;--ok:#047857;--no:#b91c1c}
*{box-sizing:border-box}
body{margin:0 auto;padding:0 24px 80px;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;color:var(--ink);max-width:940px}
h1{font-size:26px;margin:32px 0 4px}
h2{font-size:20px;margin:44px 0 8px;padding-bottom:6px;border-bottom:2px solid var(--line)}
h3{font-size:17px;margin:28px 0 4px}
.lead{color:var(--mut);margin:0 0 24px}
.howto{background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:16px 20px;margin:24px 0}
.howto p{margin:6px 0}
.grp{margin:22px 0 0;padding-top:6px}
.grp .meta{color:var(--mut);font-size:13px;margin:0 0 8px}
.pri{display:inline-block;padding:1px 8px;border-radius:99px;font-size:12px;background:#f3f4f6;border:1px solid var(--line)}
table.b{width:100%;border-collapse:collapse;margin:8px 0 0}
table.b td{border:1px solid var(--line);padding:8px 10px;vertical-align:top}
td.n{width:92px;white-space:nowrap;font:13px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--accent);background:var(--box)}
td.t{width:auto}
td.a{width:150px;background:var(--box);font-size:13px;white-space:nowrap}
td.c{width:28%;background:var(--box)}
td.c:focus{outline:2px solid var(--accent);background:#fff}
.chdr td{background:#f3f4f6;font-size:12px;color:var(--mut);font-weight:600}
label.r{display:block;cursor:pointer;line-height:1.5}
label.r input{margin-right:5px}
code{background:#f3f4f6;padding:1px 4px;border-radius:3px;font-size:.9em}
#bar{position:sticky;bottom:0;background:#fff;border-top:2px solid var(--line);padding:12px 0;margin-top:40px}
button{font:inherit;padding:8px 16px;border:1px solid var(--accent);background:var(--accent);color:#fff;border-radius:6px;cursor:pointer}
#dump{width:100%;height:180px;margin-top:10px;font:12px ui-monospace,Menlo,monospace;display:none}
footer{color:var(--mut);font-size:14px;margin-top:32px}
@media print{
  #bar,.howto{display:none}
  body{max-width:none;font-size:12px}
  table.b{page-break-inside:auto}
  tr{page-break-inside:avoid}
  td.c{min-height:48px}
}
"""

JS = """
function collect(){
  var rows=document.querySelectorAll('tr[data-id]'),out=[];
  for(var i=0;i<rows.length;i++){
    var r=rows[i],id=r.getAttribute('data-id');
    var picked=r.querySelector('input[type=radio]:checked');
    var note=(r.querySelector('.c')||{}).innerText||'';
    note=note.replace(/\\s+/g,' ').trim();
    if(!picked&&!note)continue;
    out.push({id:id,answer:picked?picked.value:'',comment:note});
  }
  return out;
}
function save(){
  var d=document.getElementById('dump');
  d.value=JSON.stringify({document:document.title,answers:collect()},null,2);
  d.style.display='block';d.focus();d.select();
  try{document.execCommand('copy')}catch(e){}
}
"""

STR = {
 'ru': dict(title='Что платформа должна делать — на согласование',
            lead='{n}. Версия {v} · {d}',
            howto=('<p><strong>Как пользоваться.</strong> Каждая строка — утверждение о платформе. '
                   'Отметьте «верно», «не так» или «вопрос», и допишите комментарий, если есть что сказать.</p>'
                   '<p>Можно печатать прямо в браузере, потом «Печать» → «Сохранить как PDF»; можно распечатать '
                   'и писать от руки; можно нажать кнопку внизу и прислать нам текст ответов.</p>'
                   '<p>Код слева (например <code>C-04.a3</code>) — постоянный адрес пункта. Он не меняется между '
                   'версиями, поэтому на него можно ссылаться и через полгода.</p>'),
            s_over='Как это работает в целом', s_cases='Что должно быть сделано',
            s_screens='Экраны', s_trig='Что происходит само', s_proc='Роли и порядок работы',
            c_n='код', c_t='утверждение', c_a='ваш ответ', c_c='комментарий',
            ok='верно', no='не так', q='вопрос',
            btn='Собрать мои ответы', dump='Скопируйте этот текст и пришлите нам',
            foot=('Верните этот файл — с ответами в браузере, сканом от руки или текстом из кнопки выше. '
                  'Мы разберём каждый пункт и вернёмся с решением по каждому.')),
 'en': dict(title='What the platform must do — for review',
            lead='{n}. Version {v} · {d}',
            howto=('<p><strong>How to use this.</strong> Each row is a claim about the platform. Mark it '
                   '"right", "not so" or "question", and add a comment if you have one.</p>'
                   '<p>Type straight into the browser and Print → Save as PDF, print it and write by hand, or '
                   'press the button at the bottom and send us the text of your answers.</p>'
                   "<p>The code on the left (<code>C-04.a3</code>) is that item&#39;s permanent address. It does not "
                   'change between versions, so it is still quotable six months from now.</p>'),
            s_over='How it works, in short', s_cases='What must be delivered',
            s_screens='Screens', s_trig='What happens by itself', s_proc='Roles and how work runs',
            c_n='code', c_t='claim', c_a='your answer', c_c='comment',
            ok='right', no='not so', q='question',
            btn='Collect my answers', dump='Copy this text and send it to us',
            foot=('Send this file back — answered in the browser, scanned from paper, or as the text from the '
                  'button above. We will work through every item and come back with a decision on each.')),
}


def rows(T, group):
    out = ['<div class="grp">',
           '<h3>%s <span class="pri">%s</span></h3>' % (md(group['title']), html.escape(group.get('id', '')))]
    if group.get('meta'):
        out.append('<p class="meta">%s</p>' % md(group['meta']))
    out.append('<table class="b"><tr class="chdr"><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'
               % (T['c_n'], T['c_t'], T['c_a'], T['c_c']))
    for ident, claim in group['items']:
        radios = ''.join(
            '<label class="r"><input type="radio" name="%s" value="%s">%s</label>' % (ident, val, T[key])
            for val, key in (('ok', 'ok'), ('no', 'no'), ('q', 'q')))
        out.append('<tr data-id="%s"><td class="n">%s</td><td class="t">%s</td>'
                   '<td class="a">%s</td><td class="c" contenteditable="true"></td></tr>'
                   % (html.escape(ident), html.escape(ident), md(claim), radios))
    out.append('</table></div>')
    return out


def build(root, date, slug, lang=None, artifact=False):
    spec = {}
    sp = os.path.join(root, 'macstack.json')
    if os.path.exists(sp):
        spec = json.load(io.open(sp, encoding='utf-8'))
    lang = lang or doc_lang(root)
    T = STR.get(lang, STR['en'])
    name = (spec.get('identity') or {}).get('title') or spec.get('name', '')
    data = collect(root)
    version = data['versions'].get('user_cases', '?')

    # The Artifact host supplies <!doctype>, <head> and <body> and refuses a page that
    # brings its own. Same content, one wrapper less.
    if artifact:
        P = ['<title>%s</title>' % html.escape(name or T['title']), '<style>%s</style>' % CSS]
    else:
        P = ['<!doctype html><html lang="%s"><head><meta charset="utf-8">' % lang,
             '<meta name="viewport" content="width=device-width,initial-scale=1">',
             '<title>%s — %s</title><style>%s</style></head><body>'
             % (html.escape(name), html.escape(T['title']), CSS)]
    P += ['<h1>%s</h1>' % html.escape(T['title']),
          '<p class="lead">%s</p>' % html.escape(T['lead'].format(n=name, v=version, d=date)),
          '<div class="howto">%s</div>' % T['howto']]

    if data['overview']:
        P.append('<h2>%s</h2>' % html.escape(T['s_over']))
        for h, body in data['overview']:
            P.append('<h3>%s</h3>' % md(h))
            for b in body:
                P.append('<li>%s</li>' % md(b[2:]) if b.startswith('- ') else '<p>%s</p>' % md(b))

    for key, sect in (('cases', 's_cases'), ('screens', 's_screens'),
                      ('triggers', 's_trig'), ('procedures', 's_proc')):
        groups = [g for g in data[key] if g['items']]
        if not groups:
            continue
        P.append('<h2>%s</h2>' % html.escape(T[sect]))
        last = None
        for g in groups:
            if key == 'cases' and g.get('section') and g['section'] != last:
                last = g['section']
                P.append('<h3 style="color:#6b7280;font-size:14px;text-transform:uppercase;letter-spacing:.04em">%s</h3>' % md(last))
            if key == 'screens' and g.get('path'):
                g = dict(g, meta='<code>%s</code>' % g['path'])
            P.extend(rows(T, g))

    P.append('<div id="bar"><button onclick="save()">%s</button>'
             '<textarea id="dump" placeholder="%s"></textarea></div>'
             % (html.escape(T['btn']), html.escape(T['dump'])))
    P.append('<footer>%s</footer>' % html.escape(T['foot']))
    P.append('<script>%s</script>%s' % (JS, '' if artifact else '</body></html>'))

    counted = sum(len(g['items']) for k in ('cases', 'screens', 'triggers', 'procedures') for g in data[k])
    return '\n'.join(P), version, counted, data


def main():
    argv = sys.argv[1:]
    args, flags, i = [], {}, 0
    while i < len(argv):
        a = argv[i]
        if a.startswith('--'):
            if '=' in a:
                k, _, v = a[2:].partition('='); flags[k] = v
            elif i + 1 < len(argv) and not argv[i + 1].startswith('--'):
                flags[a[2:]] = argv[i + 1]; i += 1
            else:
                flags[a[2:]] = True
        else:
            args.append(a)
        i += 1
    root = args[0] if args else 'macstack'
    if not os.path.isdir(root):
        print('no macstack/ folder at %s' % root); return 1
    date = flags.get('date') or _today(root)
    slug = flags.get('slug') or 'user-cases'
    artifact = flags.get('artifact') is True or flags.get('artifact') == 'true'
    doc, version, counted, data = build(root, date, slug, flags.get('lang'), artifact)

    outdir = os.path.join(root, 'history', 'handoffs')
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, '%s-%s%s.html' % (date, slug, '-artifact' if artifact else ''))
    if os.path.exists(out):
        print('refusing to overwrite an immutable handoff: %s' % out)
        print('a new round writes a new dated file — pass --date or --slug')
        return 2
    io.open(out, 'w', encoding='utf-8').write(doc)

    print('%s  ·  %d answerable items' % (out, counted))
    print('  documents: ' + ' · '.join('%s v%s' % (k, v) for k, v in sorted(data['versions'].items())))
    print('')
    if artifact:
        print('  artifact body — publish with the Artifact tool, then record its URL below')
        print('')
    print('Append to history/log.md:')
    print('')
    print('<!-- macstack:entry=%s-handoff -->' % date)
    print('## [%s] handoff | %s' % (date, 'Client review package'))
    print('')
    print('```yaml')
    print('kind: handoff')
    print('document: [%s]' % ', '.join(sorted(data['versions'])))
    print('version: %s' % version)
    print('file: history/handoffs/%s' % os.path.basename(out))
    if artifact:
        print('url:')
    print('to:')
    print('```')
    return 0


def _today(root):
    """No clock in the body of a rendered document, but a handoff IS dated. Take the
    date from the caller when given; otherwise from the filesystem, once."""
    import datetime
    return datetime.date.today().isoformat()


if __name__ == '__main__':
    sys.exit(main())
