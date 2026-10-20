#!/usr/bin/env python3
"""Diffuse les articles du blog sur dev-null.sh via navette (composer).
État : tools/devnull-state.json — les slugs déjà postés ne le seront pas deux fois."""
import json, os, pathlib, subprocess, time, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
NAV = 'http://127.0.0.1:8890'
STATE = ROOT / 'tools/devnull-state.json'
DELAY = int(os.environ.get('DELAY', '12'))

def nav(payload, wait_after=2.5):
    r = subprocess.run(['curl','-s','-X','POST',NAV+'/navigate','-H','content-type: application/json',
                        '--data-binary', json.dumps(payload)], capture_output=True, text=True, timeout=90)
    time.sleep(wait_after)
    return r.stdout

def ev(js):
    r = subprocess.run(['curl','-s','-X','POST',NAV+'/evaluate','-H','content-type: application/json',
                        '--data-binary', json.dumps({"js":js})], capture_output=True, text=True, timeout=60)
    try: return json.loads(r.stdout).get('result','')
    except Exception: return 'ERR '+r.stdout[:120]

commits = json.load(open(ROOT/'tools/devnull-commits.json'))
state = json.loads((ROOT/'tools/devnull-state.json').read_text()) if (ROOT/'tools/devnull-state.json').exists() else {'posted':{}}
posted = state.get('posted',{})

todo = [c for c in commits if c['slug'] not in posted]
print(f'{len(commits)} articles · {len(posted)} déjà postés · {len(todo)} à diffuser', flush=True)

ok, fail = 0, 0
for i, c in enumerate(todo):
    nav({'url':'https://dev-null.sh/'}, wait_after=3)
    tj = json.dumps(c['text_commit'], ensure_ascii=False)
    import base64 as b64mod
    b64 = b64mod.b64encode(c['text_commit'].encode('utf-8')).decode('ascii')
    fill = ("(function(){var ta=document.querySelector('textarea');if(!ta)return 'PAS DE TEXTAREA';"
            "var b64='"+b64+"';"
            "var bytes=Uint8Array.from(atob(b64),function(c){return c.charCodeAt(0)});"
            "var text=new TextDecoder().decode(bytes);"
            "var st=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;"
            "st.call(ta,text);ta.dispatchEvent(new Event('input',{bubbles:true}));return 'ok:'+text.length})()")
    r1 = ev(fill)
    if not str(r1).startswith('ok:'):
        print(f'  ✗ {c["slug"]} : remplissage KO — {str(r1)[:120]}', flush=True); fail += 1; continue
    click = ("(function(){var f=document.querySelector('form[action=\"/commits\"]');"
             "if(!f)return 'pas de form';"
             "var b=[].slice.call(f.querySelectorAll('button')).find(function(x){return /commit/i.test(x.textContent||'')});"
             "if(!b)return 'pas de bouton';b.click();return 'ok'})()")
    r2 = ev(click)
    time.sleep(6)
    posted[c['slug']] = {'devnull': str(r2)[:60]}
    state['posted'] = posted
    pathlib.Path(STATE).write_text(json.dumps(state, ensure_ascii=False, indent=1)+'\n')
    ok += 1
    print(f'  ✓ {i+1}/{len(todo)} {c["slug"]}', flush=True)
    if i < len(todo)-1: time.sleep(DELAY)
print(f'TERMINÉ : {ok} postés, {fail} échecs', flush=True)
