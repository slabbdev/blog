#!/usr/bin/env python3
"""Génère depuis INDEX.md : les pages slug FR/EN (/fr/<slug>, /en/<slug>) avec canonical
et hreflang, les redirections des anciens liens (/posts/<slug>), et sitemap.xml + rss.xml.
Lancé localement ou par l'action GitHub à chaque push."""
import datetime, email.utils, pathlib, html as _h

root = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://blog.slabb.dev'
slugs = [l.strip()[2:] for l in (root / 'INDEX.md').read_text().splitlines()
         if l.strip().startswith('- ')]
tpl = (root / 'article.html').read_text()

def head_block(lang, slug, has_en):
    b = BASE
    c = f'<link rel="canonical" href="{b}/{lang}/{slug}">\n'
    if has_en:
        c += f'<link rel="alternate" hreflang="fr" href="{b}/fr/{slug}">\n'
        c += f'<link rel="alternate" hreflang="en" href="{b}/en/{slug}">\n'
        c += f'<link rel="alternate" hreflang="x-default" href="{b}/fr/{slug}">\n'
    c += f'<script>window.POST_SLUG="{slug}";window.POST_LANG="{lang}";window.POST_HAS_EN={"true" if has_en else "false"};</script>\n'
    return c

count = 0
for slug in slugs:
    has_en = (root / f'posts/{slug}.en.md').exists()
    for lang in (['fr', 'en'] if has_en else ['fr']):
        page = tpl.replace('</head>', head_block(lang, slug, has_en) + '</head>')
        d = root / lang
        d.mkdir(exist_ok=True)
        (d / f'{slug}.html').write_text(page)
        count += 1
    # ancien lien /posts/<slug> : redirection vers la version française
    redir = (f'<!DOCTYPE html><meta charset="utf-8"><meta http-equiv="refresh" content="0; url={BASE}/fr/{slug}">'
             f'<script>location.replace("{BASE}/fr/{slug}")</script>')
    (root / f'posts/{slug}.html').write_text(redir)

# sitemap avec alternates
sm = ('<?xml version="1.0" encoding="UTF-8"?>\n'
      '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
      'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n')
for slug in slugs:
    has_en = (root / f'posts/{slug}.en.md').exists()
    for lang in (['fr', 'en'] if has_en else ['fr']):
        u = f'{BASE}/{lang}/{slug}'
        alt = ''
        if has_en:
            alt = (f'<xhtml:link rel="alternate" hreflang="fr" href="{BASE}/fr/{slug}"/>'
                   f'<xhtml:link rel="alternate" hreflang="en" href="{BASE}/en/{slug}"/>')
        sm += f'  <url><loc>{u}</loc>{alt}</url>\n'
sm += '</urlset>\n'
(root / 'sitemap.xml').write_text(sm)

# rss — FR d'abord
items = []
for slug in slugs:
    f = root / f'posts/{slug}.fr.md'
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
rss += '<description>Agents IA, sécurité &amp; preuve — EN first, FR as translations land</description>\n<language>fr</language>\n'
for slug, fm in items:
    t = _h.escape(fm.get('titre', slug))
    d = _h.escape(fm.get('resume', ''))
    dt = fm.get('date', '')
    rfc = email.utils.format_datetime(datetime.datetime.fromisoformat(dt)) if dt else ''
    rss += f'<item><title>{t}</title><link>{BASE}/fr/{slug}</link><guid>{BASE}/fr/{slug}</guid><description>{d}</description>'
    rss += (f'<pubDate>{rfc}</pubDate>' if rfc else '') + '</item>\n'
rss += '</channel></rss>\n'
(root / 'rss.xml').write_text(rss)
print(f'gen.py : {count} pages slug ({len(slugs)} articles) + sitemap + rss ({len(items)} items)')
