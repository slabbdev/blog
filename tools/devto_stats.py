#!/usr/bin/env python3
"""devto_stats.py — récupère les métriques dev.to (vues, réactions) et écrit devto-stats.json.

Appelle GET /articles/me avec la clé API (header api-key), agrège par article
et écrit un JSON public : uniquement des slugs et des compteurs — jamais la clé,
pas de referrers (ils peuvent contenir des URLs privées).

Usage : python3 tools/devto_stats.py [--dry-run]
Secret (env) : DEVTO_API_KEY (dev.to → Settings → Extensions → DEV Community API Keys).
               Manquante = sortie honnête, code 1.
               DEVTO_API surcharge la base (tests locaux, défaut https://dev.to/api).
"""
import json, os, pathlib, sys, datetime, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'devto-stats.json'
BASE = os.environ.get('DEVTO_API', 'https://dev.to/api')
DRY = '--dry-run' in sys.argv

def me(key):
    """Tous mes articles publiés, pagination comprise."""
    out, page = [], 1
    while True:
        req = urllib.request.Request(f'{BASE}/articles/me?per_page=100&page={page}',
            headers={'api-key': key, 'accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=30) as r:
            batch = json.load(r)
        out.extend(batch)
        if len(batch) < 100:
            return out
        page += 1

def main():
    key = os.environ.get('DEVTO_API_KEY')
    if not key:
        print('DEVTO_API_KEY manquante — dev.to → Settings → Extensions → DEV Community API Keys.')
        sys.exit(1)
    arts = me(key)
    articles, tv, tr = {}, 0, 0
    for a in arts:
        v, r = a.get('page_views_count') or 0, a.get('positive_reactions_count') or 0
        articles[a['slug']] = {'views': v, 'reactions': r}
        tv += v
        tr += r
    data = {
        'generated_at': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'totals': {'views': tv, 'reactions': tr},
        'articles': articles,
    }
    print(f'{len(articles)} articles dev.to · {tv} vues · {tr} réactions')
    if DRY:
        print('dry-run — rien écrit.')
        return
    OUT.write_text(json.dumps(data, indent=1, ensure_ascii=False) + '\n')
    print(f'→ {OUT.name}')

if __name__ == '__main__':
    main()
