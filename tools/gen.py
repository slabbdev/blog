#!/usr/bin/env python3
"""Génère les pages slug (<slug>.html + canonical) et sitemap.xml depuis INDEX.md.
Lancé localement (python3 tools/gen.py) ou automatiquement par l'action GitHub à chaque push."""
import pathlib

root = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://blog.slabb.dev'
slugs = [l.strip()[2:] for l in (root / 'INDEX.md').read_text().splitlines()
         if l.strip().startswith('- ')]
tpl = (root / 'article.html').read_text()

urls = [BASE + '/']
for slug in slugs:
    page = tpl.replace('</head>',
        f'<link rel="canonical" href="{BASE}/{slug}">\n'
        f'<script>window.POST_SLUG="{slug}";window.POST_LANG="fr";</script>\n</head>')
    (root / f'posts/{slug}.html').write_text(page)
    (root / f'{slug}.html').unlink(missing_ok=True)  # stubs racine de l'ancienne organisation
    urls.append(f'{BASE}/posts/{slug}')

sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sm += ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls)
sm += '</urlset>\n'
(root / 'sitemap.xml').write_text(sm)
import datetime
print(f'gen.py : {len(slugs)} pages slug + sitemap.xml ({", ".join(slugs)})')

# ---- rss.xml ----
import email.utils, html as _h
items = []
for slug in slugs:
    f = (root / f'posts/{slug}.fr.md')
    if not f.exists():
        continue
    fm, body = {}, f.read_text()
    if body.startswith('---'):
        block = body[3:body.index('---', 3)]
        for line in block.splitlines():
            if ':' in line:
                k, v = line.split(':', 1)
                fm[k.strip()] = v.strip().strip('"')
    items.append((slug, fm))
rss = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel>\n'
rss += '<title>blog.slabb.dev — Sam Labbe</title>\n<link>https://blog.slabb.dev</link>\n'
rss += '<description>Agents IA, sécurité &amp; preuve — FR d\'abord</description>\n<language>fr</language>\n'
for slug, fm in items:
    t = _h.escape(fm.get('titre', slug))
    d = _h.escape(fm.get('resume', ''))
    dt = fm.get('date', '')
    rfc = email.utils.format_datetime(datetime.datetime.fromisoformat(dt)) if dt else ''
    rss += f'<item><title>{t}</title><link>{BASE}/{slug}</link><guid>{BASE}/{slug}</guid><description>{d}</description>'
    rss += (f'<pubDate>{rfc}</pubDate>' if rfc else '') + '</item>\n'
rss += '</channel></rss>\n'
(root / 'rss.xml').write_text(rss)
print('rss.xml :', len(items), 'items')
