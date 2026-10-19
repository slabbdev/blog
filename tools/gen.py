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
    (root / f'{slug}.html').write_text(page)
    urls.append(f'{BASE}/{slug}')

sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
sm += ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls)
sm += '</urlset>\n'
(root / 'sitemap.xml').write_text(sm)
print(f'gen.py : {len(slugs)} pages slug + sitemap.xml ({", ".join(slugs)})')
