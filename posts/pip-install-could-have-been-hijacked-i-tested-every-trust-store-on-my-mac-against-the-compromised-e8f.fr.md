---
titre: "pip install aurait pu être détourné : j'ai testé chaque trust store de mon Mac contre la chaîne eMudhra compromise"
date: 2026-10-30
themes: securite, python
resume: "Les clés eMudhra qui valaient 4, 56 et 115 auraient pu signer un faux pypi.org et transformer pip install en livraison de code arbitraire. L'écosystème Python s'est réparé en cinq jours. Le test live à quatre voies : la stack d'Apple accepte encore la chaîne, Python la refuse."
source: https://dev.to/slabb/pip-install-could-have-been-hijacked-i-tested-every-trust-store-on-my-mac-against-the-compromised-e8f
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Ffmel0dbnbm52q7adut1c.png
image_alt: "pip install aurait pu être détourné : chaque trust store testé contre la chaîne eMudhra compromise"
---

> Le writeup tombé ce soir ([OpenTeams : « Pip Install Could Have Been Hijacked »](https://openteams.com/engineering-blog/emudhra-pip-install-hijacked/)) ferme une boucle ouverte par ce blog il y a dix jours. Les clés intermédiaires eMudhra, celles où [« la clé valait le chiffre 4 »](https://dev.to/slabb/a-ca-private-key-was-the-number-4-your-curl-still-trusts-it-cve-2026-111943-45o4), étaient récupérables par n'importe qui : Scott Helme a sorti les huit « sur un laptop en moins d'une seconde ». Les valeurs incluaient **4, 56 et 115**. Le post de ce soir détaille ce que ça voulait dire pour Python : n'importe qui sur ton chemin réseau pouvait forger un certificat pour `pypi.org`, et ton prochain `pip install` aurait livré son package sans broncher. Les navigateurs l'auraient attrapé. **Les outils Python ne regardent jamais les logs qui l'auraient attrapé.** J'ai donc lancé le test complet sur ma propre machine, chaque trust store, un seul host : même Mac, même heure, verdict partagé.

## La chaîne, un paragraphe

Récupère une clé de CA faible (acte un de cette série). Forge un certificat qui prétend être `pypi.org`. Installe-toi sur le chemin réseau : Wi-Fi de café, routeur compromis, FAI. Quand un développeur lance `pip install requests`, sers le certificat forgé et un package ou wheel malveillant. Seuls les installs épinglés à des hash de fichiers exacts auraient remarqué le swap. Et parce que Chrome et Safari exigent que les certificats apparaissent dans les logs publics de Certificate Transparency alors que `pip`, `requests` et compagnie ne les consultent jamais, **cette attaque n'aurait laissé zéro trace nulle part**. Aucune exploitation n'a été documentée. La preuve de faisabilité, c'est la récupération des clés elle-même, qui prend moins d'une seconde.

## La contre-attaque en cinq jours

La partie du post de ce soir qui mérite d'être retenue, c'est la timeline de réponse, parce que l'écosystème du packaging Python s'est réparé lui-même en cinq jours chrono :

- **17 oct** : le rapport atteint Google et Mozilla.
- **20 oct** : Chrome bloque les certificats en moins de deux heures, Firefox à 22h59 UTC. L'advisorie de la Python Software Foundation sort ; les releases corrigées de `certifi` (2026.10.19), `pip` et `uv` shippent.
- **21 oct** : fixes conda, mamba et pixi, plus une édition de l'index conda-forge pour que même les vieux installs tirent des certificats corrigés.
- **26 oct** : nouvelles releases CPython, 3.15.2, 3.14.10, 3.13.18, 3.12.16, 3.11.18, qui **bloquent les clés dans le module `ssl` lui-même**, protégeant même les vieux pips tournant sur nouveaux Pythons.

Un vendor est conspicueusement absent de cette liste, et l'absence fait l'objet d'un [finding séparé](https://emudhra.we-have-a-problem.com/apple.html) que ce blog a aussi couvert : le git d'Apple, sur la même machine, acceptait encore la chaîne des jours plus tard. Les bénévoles ont battu la compagnie au trillion de dollars d'une semaine, et l'écart est mesurable sur mon bureau.

## Le test à quatre voies, lancé en live

La méthode : demander à chaque trust store ce qu'il pense de `https://dv-g3b-emudhra.we-have-a-problem.com/`, le host de check officiel dont le certificat chaîne via un des intermédiaires compromis. Une erreur de certificat veut dire protégé. Une réponse veut dire que le store trust encore la chaîne empoisonnée.

**1. Le git d'Apple, le toolchain système** (mon test plus tôt cette semaine, même machine, jamais corrigé depuis) :

```text
$ git -c http.curloptResolve=github.com:443:15.235.19.186 clone \
      https://fake-user@github.com/galadran/emudhra-git-test
# README récupéré : "INTERCEPTED: your git accepted a certificate from a compromised eMudhra CA"
```

**Vulnérable.** Un faux github.com cloné sans le moindre warning.

**2. La stdlib Python, `urllib` + `ssl` :**

```python
import urllib.request
urllib.request.urlopen("https://dv-g3b-emudhra.we-have-a-problem.com/", timeout=15)
# ssl.SSLCertVerificationError: CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate
```

**Protégé.** Le bundle OpenSSL Homebrew sous ce Python avait déjà lâché les racines.

**3. pip lui-même, contre un index de packages signé par la clé compromise :**

```text
$ python3 -m pip download --no-deps \
    --index-url https://dv-g3b-emudhra.we-have-a-problem.com/simple/ definitely-not-a-real-package
WARNING: ... SSLError(SSLCertVerificationError('Le certificat «dv-g3b-emudhra...» est bloqué.'))
```

**Protégé.** Le message d'erreur dit littéralement *bloqué*. Note : ce pip est un 26.2.1, un patch en dessous du 26.2.2 recommandé, et son bundle `certifi` vendored ne contient déjà plus aucune des deux racines (vérifié en grepant `pip/_vendor/certifi/cacert.pem` : `emSign ECC Root CA - G3` absent, `AAA Certificate Services` absent). **Le conseil de mise à jour tient toujours**, parce que le bloc explicite dans pip 26.2.2 et dans le `ssl` de CPython (3.15.2+) défend même quand un bundle se glisse, et que le `certifi` *système* de ma machine est un 2026.07.22, deux releases derrière le 2026.10.19 corrigé.

**4. Tes applications, via `requests`** : ce que `import certifi` résout dans chaque virtualenv. Sur cette machine le `certifi` système 2026.07.22 greppe propre pour les deux racines, mais les copies par venv varient, et c'est la seule couche que personne ne met à jour. C'est le check que ton CI devrait posséder.

Quatre stores, une machine, une heure : **la stack d'Apple acceptait la chaîne forgée, l'écosystème Python l'a refusée.** La différence n'est pas le talent, c'est que les mainteneurs du packaging ont traité une compromission de CA comme LEUR incident, et l'ont shippé.

## L'audit pour tes machines

```bash
# chaque interpréteur qui compte : trust-t-il encore la chaîne ?
python3 -c "import urllib.request
try: urllib.request.urlopen('https://dv-g3b-emudhra.we-have-a-problem.com/', timeout=15); print('VULNÉRABLE')
except Exception as e: print('protégé:', type(e).__name__)"

# le bundle vendored de pip (les deux greps doivent être vides)
grep -c "emSign ECC Root CA - G3\|AAA Certificate Services" \
  "$(python3 -c 'import pip,os;print(os.path.join(os.path.dirname(pip.__file__),"_vendor","certifi","cacert.pem"))')"

# les versions qui comptent : pip >= 26.2.2, certifi >= 2026.10.19,
# uv >= 0.13.4, pixi >= 0.82.1, conda >= 26.9.4, CPython dernier patch (bloc au niveau ssl)
python3 -m pip --version; python3 -c "import certifi; print(certifi.__version__)"
```

Et les deux notes opérationnelles du post de ce soir à épingler au mur : rebuild les images container et les caches CI from scratch, parce que chaque couche porte sa propre copie gelée des racines ; et **ne jamais désactiver la vérification de certificats pour faire taire une erreur**, l'auto-downgrade le plus courant qui transforme un incident de trust store en porte ouverte.

## Pourquoi cette histoire est le bon jumeau de tout le mois

Octobre nous a servi un défilé steady de pipelines cassées : listes de divulgation qui fuient, embargos brisés, updates qui annulent les fixes manuels, extensions qui te backdoorent au chargement. Celle-ci est l'image miroir : une défaillance de CA catastrophique, et un écosystème vaguement coordonné de bénévoles et de mainteneurs qui a **correctement énuméré son propre rayon d'explosion** (pip, requests, uv, pixi, conda, CPython, images Docker, installers), l'a fermé en cinq jours, puis a publié la rétrospective. La morale du mois n'est pas que tout est cassé. C'est que la différence entre la catastrophe et le non-événement, c'est de savoir si quelqu'un possède l'inventaire. Le packaging Python possédait son inventaire. La question pour ta stack : qui possède le tien ?

**TL;DR** : les clés eMudhra (valeurs 4, 56, 115) auraient pu signer un faux `pypi.org`, et `pip install` aurait livré du code attaquant sans traces, parce que les outils Python ne consultent pas les logs CT. L'écosystème s'est réparé en cinq jours, jusqu'au blocage des clés dans le module `ssl` de CPython. Mon test live à quatre voies : le git d'Apple accepte encore la chaîne, la stdlib Python, pip et les bundles la refusent. Commandes d'audit ci-dessus, pins de versions dans le post, rebuild tes caches.

Sources : [OpenTeams : Pip Install Could Have Been Hijacked](https://openteams.com/engineering-blog/emudhra-pip-install-hijacked/) · [divulgation eMudhra + hosts de check](https://emudhra.we-have-a-problem.com/) · [Acte un : la clé valait 4](https://dev.to/slabb/a-ca-private-key-was-the-number-4-your-curl-still-trusts-it-cve-2026-111943-45o4) · [Acte deux : la CA quitte le business](https://dev.to/slabb/the-ca-whose-private-key-was-the-number-4-just-quit-the-certificate-business-18ba) · [Le git d'Apple trust encore la chaîne](https://emudhra.we-have-a-problem.com/apple.html)
