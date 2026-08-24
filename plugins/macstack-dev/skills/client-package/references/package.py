#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build the client package: one self-contained HTML the client can edit and send back.

Reads USER-CASES.md and BUSINESS-LOGIC.md, numbers every acceptance bullet, and gives each
one a place to write. Output goes to handoffs/<date>-<slug>.html and is IMMUTABLE from that
moment: the client's comments come back against that exact file, and a package edited after
the fact makes every returned comment unresolvable.

Bullet numbers (C-04.2) are POSITIONAL WITHIN THIS PACKAGE, not global ids. USER-CASES.md
does not carry them, so inserting a bullet shifts the ones below it in the next package.
That is safe only because the handoff file never changes and log.md records which version
went out — a comment is always resolved against the file it was written on, never against
today's document. Do not present these numbers to anyone as stable ids.

Usage: package.py <macstack-dir> [--date YYYY-MM-DD] [--slug user-cases]
"""
import sys, os, io, re, json, datetime, html

def parse_cases(text):
    """-> (version, [ {kind, id, title, priority, intro, bullets[]} ]) в порядке документа."""
    lines = text.split('\n')
    m = re.search(r'\*\*Версия ([\d.]+)', text) or re.search(r'\*\*Version ([\d.]+)', text)
    version = m.group(1) if m else '?'
    items, cur, section = [], None, None
    i = 0
    while i < len(lines):
        ln = lines[i]
        h2 = re.match(r'^## (.+)$', ln)
        if h2:
            section = h2.group(1).strip()
        h = re.match(r'^### ([A-Z]-\d+) · (.+?)(?:\s{2,}\[(.+?)\])?\s*$', ln)
        if h:
            cur = dict(id=h.group(1), title=h.group(2).strip(), priority=(h.group(3) or '').strip(),
                       section=section, intro=[], bullets=[])
            items.append(cur)
            i += 1
            continue
        if cur is not None:
            if ln.strip().startswith('**') and ln.strip().endswith(':**'):
                j = i + 1
                while j < len(lines) and lines[j].strip():
                    if lines[j].startswith('- '):
                        cur['bullets'].append(lines[j][2:].rstrip())
                    elif lines[j].startswith('  ') and cur['bullets']:
                        cur['bullets'][-1] += ' ' + lines[j].strip()
                    j += 1
                i = j
                continue
            if ln.strip() and not ln.startswith('|') and not ln.startswith('#'):
                cur['intro'].append(ln.strip())
        i += 1
    return version, items

def parse_logic(text):
    """-> [(heading, [абзацы])] по разделам.

    Markdown в этих документах перенесён по ~95 символов, поэтому строка НЕ равна абзацу.
    Склеиваем подряд идущие строки; пустая строка и начало списка рвут абзац. Без этого
    клиент получает документ, где каждая строка висит отдельным блоком.
    """
    out, cur, buf = [], None, []
    def flush():
        if cur is not None and buf:
            cur[1].append(' '.join(buf))
        del buf[:]
    for ln in text.split('\n'):
        if ln.startswith('<!--'):
            continue
        h = re.match(r'^## (.+)$', ln)
        if h:
            flush()
            cur = (h.group(1).strip(), [])
            out.append(cur)
            continue
        if cur is None:
            continue
        s = ln.rstrip()
        if not s.strip():
            flush(); continue
        if s.startswith(('- ', '| ', '#')):
            flush()
            if s.startswith('- '):
                cur[1].append(s)
            continue
        if buf and buf[-1].startswith('- '):
            flush()
        buf.append(s.strip())
    flush()
    return [(h, b) for h, b in out if b and not h.lower().startswith(('журнал', 'document journal'))]

def md(s):
    s = html.escape(s)
    s = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', s)
    s = re.sub(r'`(.+?)`', r'<code>\1</code>', s)
    s = re.sub(r'\*(.+?)\*', r'<em>\1</em>', s)
    s = re.sub(r'(?<![A-Za-z0-9_])_(.+?)_(?![A-Za-z0-9_])', r'<em>\1</em>', s)
    return s

CSS = """
:root{--ink:#1a1a1a;--mut:#6b7280;--line:#d4d4d8;--accent:#1d4ed8;--box:#fafafa}
*{box-sizing:border-box}
body{margin:0;padding:0 24px 64px;font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif;color:var(--ink);max-width:900px;margin:0 auto}
h1{font-size:26px;margin:32px 0 4px}h2{font-size:20px;margin:40px 0 8px;padding-bottom:6px;border-bottom:2px solid var(--line)}
h3{font-size:17px;margin:28px 0 4px}
.lead{color:var(--mut);margin:0 0 24px}
.howto{background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:16px 20px;margin:24px 0}
.howto p{margin:6px 0}
.case{margin:24px 0 0;padding-top:8px}
.case .meta{color:var(--mut);font-size:13px;margin:0 0 8px}
.pri{display:inline-block;padding:1px 8px;border-radius:99px;font-size:12px;background:#f3f4f6;border:1px solid var(--line)}
.intro{margin:8px 0 12px}
table.b{width:100%;border-collapse:collapse;margin:8px 0 0}
table.b td{border:1px solid var(--line);padding:8px 10px;vertical-align:top}
td.n{width:74px;white-space:nowrap;font:13px ui-monospace,SFMono-Regular,Menlo,monospace;color:var(--accent);background:var(--box)}
td.t{width:auto}
td.c{width:34%;background:var(--box)}
td.c:focus{outline:2px solid var(--accent);background:#fff}
.chdr td{background:#f3f4f6;font-size:12px;color:var(--mut);font-weight:600}
code{background:#f3f4f6;padding:1px 4px;border-radius:3px;font-size:.9em}
footer{margin-top:48px;padding-top:16px;border-top:1px solid var(--line);color:var(--mut);font-size:13px}
@media print{
 body{padding:0;font-size:11pt;max-width:none}
 .howto{background:#fff}
 h2{page-break-after:avoid}h3{page-break-after:avoid}
 .case{page-break-inside:avoid}
 table.b{page-break-inside:auto}
 td.c{min-height:44px}
}
"""

HOWTO_RU = """<p><strong>Как пользоваться этим документом.</strong> Слева — что платформа должна вам дать.
Справа — пустая колонка: напишите в ней всё, с чем не согласны или что хотите изменить.</p>
<p>Можно двумя способами: печатать прямо в браузере в белые ячейки, потом «Печать» → «Сохранить как PDF»;
или сразу распечатать и написать от руки.</p>
<p>Номер слева (например <code>C-04.2</code>) — это адрес пункта <em>в этом файле</em>. Ссылайтесь на него,
и мы точно поймём, о чём речь.</p>"""

HOWTO_EN = """<p><strong>How to use this.</strong> On the left, what the platform must give you. On the right, an
empty column: write there anything you disagree with or want changed.</p>
<p>Either type straight into the white cells in your browser and then Print → Save as PDF, or print it and
write by hand.</p>
<p>The number on the left (<code>C-04.2</code>) is that item's address <em>in this file</em>. Quote it and we
will know exactly what you mean.</p>"""

def build(root, date, slug):
    spec = json.load(io.open(os.path.join(root, 'macstack.json'), encoding='utf-8'))
    lang = ((spec.get('docs') or {}).get('language')) or 'en'
    ru = lang == 'ru'
    name = spec.get('description', '').split('.')[0] or spec.get('name', '')
    uc = io.open(os.path.join(root, 'client', 'USER-CASES.md'), encoding='utf-8').read()
    version, cases = parse_cases(uc)
    bl_path = os.path.join(root, 'client', 'BUSINESS-LOGIC.md')
    logic = parse_logic(io.open(bl_path, encoding='utf-8').read()) if os.path.exists(bl_path) else []

    T = dict(
        title='Что платформа должна делать — на согласование' if ru else 'What the platform must do — for review',
        lead='{n}. Версия документа {v} · {d}' if ru else '{n}. Document version {v} · {d}',
        logic='Как это работает в целом' if ru else 'How it works, in short',
        cases='Что должно быть сделано' if ru else 'What must be delivered',
        chdr_n='пункт' if ru else 'item', chdr_t='что должно быть' if ru else 'what must be true',
        chdr_c='ваш комментарий' if ru else 'your comment',
        foot=('Верните этот файл нам — с комментариями в правой колонке или сканом, если писали от руки. '
              'Мы разберём каждый пункт и вернёмся с решением по каждому.') if ru else
             ('Send this file back — with comments in the right column, or a scan if you wrote by hand. '
              'We will work through every item and come back with a decision on each.'))

    P = ['<!doctype html><html lang="%s"><head><meta charset="utf-8">' % lang,
         '<meta name="viewport" content="width=device-width,initial-scale=1">',
         '<title>%s — %s</title><style>%s</style></head><body>' % (html.escape(name), html.escape(T['title']), CSS),
         '<h1>%s</h1>' % html.escape(T['title']),
         '<p class="lead">%s</p>' % html.escape(T['lead'].format(n=name, v=version, d=date)),
         '<div class="howto">%s</div>' % (HOWTO_RU if ru else HOWTO_EN)]

    if logic:
        P.append('<h2>%s</h2>' % html.escape(T['logic']))
        for h, body in logic:
            P.append('<h3>%s</h3>' % md(h))
            for b in body:
                if b.startswith('- '):
                    P.append('<p>• %s</p>' % md(b[2:]))
                elif not b.startswith('|'):
                    P.append('<p>%s</p>' % md(b))

    P.append('<h2>%s</h2>' % html.escape(T['cases']))
    seen_section = None
    for c in cases:
        if c['section'] and c['section'] != seen_section:
            seen_section = c['section']
            P.append('<h3>%s</h3>' % md(seen_section))
        P.append('<div class="case">')
        P.append('<p class="meta"><strong>%s</strong> · %s %s</p>' % (
            html.escape(c['id']), md(c['title']),
            ('<span class="pri">%s</span>' % html.escape(c['priority'])) if c['priority'] else ''))
        if c['intro']:
            P.append('<p class="intro">%s</p>' % md(' '.join(c['intro'])))
        P.append('<table class="b"><tr class="chdr"><td>%s</td><td>%s</td><td>%s</td></tr>' % (
            html.escape(T['chdr_n']), html.escape(T['chdr_t']), html.escape(T['chdr_c'])))
        for k, b in enumerate(c['bullets'], 1):
            P.append('<tr><td class="n">%s.%d</td><td class="t">%s</td><td class="c" contenteditable="true"></td></tr>'
                     % (html.escape(c['id']), k, md(b.rstrip(';.'))))
        P.append('</table></div>')

    P.append('<footer>%s</footer></body></html>' % html.escape(T['foot']))

    outdir = os.path.join(root, 'history', 'handoffs')
    os.makedirs(outdir, exist_ok=True)
    out = os.path.join(outdir, '%s-%s.html' % (date, slug))
    io.open(out, 'w', encoding='utf-8').write('\n'.join(P) + '\n')
    return out, version, len(cases), sum(len(c['bullets']) for c in cases), ru

def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    root = args[0] if args else 'macstack'
    date = slug = None
    for i, a in enumerate(sys.argv):
        if a == '--date' and i + 1 < len(sys.argv): date = sys.argv[i + 1]
        if a == '--slug' and i + 1 < len(sys.argv): slug = sys.argv[i + 1]
    date = date or datetime.date.today().isoformat()
    slug = slug or 'user-cases'
    out, version, ncases, nbullets, ru = build(root, date, slug)
    print('%s — %d кейсов, %d пунктов, версия %s' % (out, ncases, nbullets, version) if ru
          else '%s — %d cases, %d items, version %s' % (out, ncases, nbullets, version))
    print()
    print('Запись для log.md:' if ru else 'Entry for log.md:')
    print('## [%s] handoff | %s' % (date, 'Пакет на согласование клиенту' if ru else 'Client review package'))
    print()
    print('- **document:** USER-CASES.md' + (' + BUSINESS-LOGIC.md'))
    print('- **version:** %s' % version)
    print('- **file:** `history/handoffs/%s-%s.html`' % (date, slug))
    print('- **to:** ')
    return 0

if __name__ == '__main__':
    sys.exit(main())
