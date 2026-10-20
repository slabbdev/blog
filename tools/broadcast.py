#!/usr/bin/env python3
"""broadcast.py — annonce les nouveaux articles du blog sur Bluesky et X.

Lit INDEX.md + les front-matters, compare à broadcast-state.json (committé),
publie les articles non encore annoncés, note le résultat dans l'état.

Usage : python3 tools/broadcast.py [--dry-run] [--max N]
Secrets (env) : BSKY_IDENTIFIER (handle.bsky.social), BSKY_APP_PASSWORD (app password),
                X_BEARER_TOKEN (token API v2). Manquants = réseau skippé, dit honnêtement.
"""
import json, os, pathlib, sys, datetime, urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = 'https://blog.slabb.dev'
STATE = ROOT / 'broadcast-state.json'
MAX_BACKFILL = int(os.environ.get('MAX_BACKFILL', '2'))
DRY = '--dry-run' in sys.argv

args = [a for a in sys.argv[1:] if not a.startswith('--')]
MAX_BACKFILL = int(args[0]) if args else MAX_BACKFILL

def http(url, data=None, token=None):
    req = urllib.request.Request(url, data=json.dumps(data).encode() if data else None,
        headers={'content-type': 'application/json', **({'authorization': 'Bearer ' + token} if token else {})})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def front(path):
    txt = path.read_text(); fm = {}
    if txt.startswith('---'):
        block = txt[3:txt.index('---', 3)]
        for l in block.splitlines():
            if ':' in l: k, v = l.split(':', 1); fm[k.strip()] = v.strip().strip('"')
    return fm

def bsky(identifier, password, text, link, title, desc):
    sess = http('https://bsky.social/xrpc/com.atproto.server.createSession',
                {'identifier': identifier, 'app_password': password})
    rec = {'$type': 'app.bsky.feed.post', 'text': text,
           'createdAt': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%S.000Z'),
           'embed': {'$type': 'app.bsky.embed.external',
                     'external': {'uri': link, 'title': title[:200], 'description': (desc or '')[:300]}}}
    r = http('https://bsky.social/xrpc/com.atproto.repo.createRecord',
             {'repo': sess['did'], 'collection': 'app.bsky.feed.post', 'record': rec}, token=sess['accessJwt'])
    return 'posté → ' + r.get('uri', 'ok')[:60]

def x_post(bearer, text):
    r = http('https://api.twitter.com/2/tweets', {'text': text[:278]}, token=bearer)
    return 'tweeté → id ' + str(r.get('data', {}).get('id', 'ok'))

def main():
    state = json.loads(STATE.read_text()) if STATE.exists() else {'posted': {}}
    idx = (ROOT / 'INDEX.md').read_text()
    slugs = [l.strip()[2:] for l in idx.splitlines() if l.strip().startswith('- ')]
    fresh = [s for s in slugs if s not in state['posted']][:MAX_BACKFILL]
    print(f'{len(slugs)} articles · {len(state["posted"])} déjà annoncés · {len(fresh)} à diffuser :')
    for s in fresh: print('  →', s)
    if DRY: print('dry-run — rien publié.'); return
    bs_id, bs_pw, x_tok = os.environ.get('BSKY_IDENTIFIER'), os.environ.get('BSKY_APP_PASSWORD'), os.environ.get('X_BEARER_TOKEN')
    for slug in fresh:
        fm, _ = front(ROOT / f'posts/{slug}.fr.md')
        title = fm.get('titre', slug); link = f'{BASE}/posts/{slug}'; desc = fm.get('resume', '')
        res = {}
        if bs_id and bs_pw:
            text = f'{title}\n\n{link}'
            try: res['bsky'] = bsky(bs_id, bs_pw, text, link, title, desc)
            except Exception as e: res['bsky'] = 'erreur : ' + str(e)[:120]
        else: res['bsky'] = 'skipped (pas de creds Bluesky)'
        if x_tok:
            xt = (title[:250] + ' ' + link) if len(title) < 250 else (title[:220] + '… ' + link)
            try: res['x'] = x_post(x_tok, xt)
            except Exception as e: res['x'] = 'erreur : ' + str(e)[:120]
        else: res['x'] = 'skipped (pas de token X)'
        state['posted'][slug] = res
        print(f'  {slug} :', res)
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + '\n')
    print('état écrit → broadcast-state.json')

main()
