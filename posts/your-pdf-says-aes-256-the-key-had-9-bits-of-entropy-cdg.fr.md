---
titre: "Ton PDF dit AES-256. La clé avait 9 bits d'entropie."
date: 2026-10-28
themes: securite, crypto
resume: "MuPDF appelait ça AES-256. La clé venait d'un LCG seedé par l'horloge avec 9 bits d'entropie : 512 clés candidates, 7 ms pour toutes les générer, et j'ai déchiffré mon propre PDF protégé par mot de passe en 0,63 s sans le mot de passe. Le lab complet, reproductible."
source: https://dev.to/slabb/your-pdf-says-aes-256-the-key-had-9-bits-of-entropy-cdg
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fzegr1mn1hu4dvsuj944u.png
image_alt: "Ton PDF dit AES-256. La clé avait 9 bits d'entropie."
---

> Je viens de créer un PDF chiffré en AES-256 avec mot de passe, de voir le lecteur refuser de l'ouvrir sans ce mot de passe, puis de le déchiffrer **sans aucun mot de passe en 0,63 seconde**, contenu secret intégralement récupéré. L'outil qui fait ça est public depuis hier. La vulnérabilité n'est ni dans AES, ni dans le mot de passe : elle est dans la **génération de la clé**, où une clé « 256 bits » dérive d'un générateur pseudo-aléatoire seedé par l'horloge, avec **9 bits d'entropie effective**. C'est l'histoire des [déchiffreurs PDF de V12](https://v12.sh/blog/the-case-of-the-9bit-aes-key), et voici le lab que j'ai mené de bout en bout sur ma machine, rejouable en dix minutes.

## Ce que le chiffrement PDF est censé faire

La sécurité standard PDF, révision 6 (celle de l'AES-256, `AESV3`), a un design sain : le fichier est chiffré avec une **clé de fichier aléatoire de 32 octets**. Ton mot de passe ne chiffre jamais le document directement ; il encapsule la clé de fichier (`/UE` dans le dictionnaire de chiffrement). Casse l'hypothèse que les 32 octets sont aléatoires, et le mot de passe cesse d'importer : récupère la clé de fichier, lis le fichier, le mot de passe n'entre jamais dans l'histoire.

MuPDF avant 1.28.5, Foxit Reader 2026.1.3, OpenPDF 3.0.5 et iText 9.7.1 ont chacun cassé cette hypothèse différemment. Même étiquette AES-256, même certificat sur la boîte, théâtre d'entropie à l'intérieur.

## MuPDF : 9 bits, 512 clés, 7 millisecondes

Le `fz_memrnd()` de MuPDF générait la clé de fichier depuis un LCG 48 bits (famille `drand48`) seedé une fois avec **l'epoch en secondes**. Deux détails d'implémentation effondrent l'espace :

- chaque octet produit ne conserve que les **bits 17-24 de l'état** du LCG ;
- le seeding initialise les 16 bits de poids faible de l'état à la constante `0x330E`.

Fais le calcul : seuls **9 bits du timestamp influencent le flux de sortie**. Des timestamps espacés de 512 secondes produisent les mêmes octets « aléatoires ». Je l'ai vérifié directement, avec la dérivation exacte du PoC publié par V12 (constantes LCG POSIX, `a=0x5DEECE66D`, `c=0xB`) :

```python
state = 0x330E | ((seed & 0xFFFF) << 16) | (((seed >> 16) & 0xFFFF) << 32)
# chaque octet : state = (a*state + c) mod 2**48 ; octet = (state >> 17) & 0xFF
```

```text
keystream(t)      == keystream(t + 512)  : True
keystream(t)      != keystream(t + 511)  : True
512 keystreams candidates générées en   : 7 ms
```

Une clé « 256 bits » avec 512 candidates. Le champ de permissions chiffrées `/Perms` offre un oracle en clair connu : pour chaque candidate, on teste si le déchiffrement correspond aux bits de permission du document. Une des 512 passe.

## Le lab, de bout en bout

Reproductible sur toute machine avec Python et Homebrew :

```bash
brew install mupdf                      # mutool 1.28.5 (corrigé ; utilisé seulement comme lecteur/écrivain)
python3 -m venv v && v/bin/pip install "pymupdf<1.28.5" cryptography
git clone https://github.com/v12-security/pocs
```

Étape 1 : créer une victime avec la pile vulnérable (pymupdf 1.28.2 embarque MuPDF 1.28.2) :

```python
import pymupdf
doc = pymupdf.open(); page = doc.new_page()
page.insert_text((72, 200), "TOP SECRET: the mermaid lands at 0400. Auth code KHAKI-7741.")
doc.save("secret.pdf", encryption=pymupdf.PDF_ENCRYPT_AES_256,
         user_pw="hunter2", owner_pw="owner-pw")
```

Étape 2 : vérifier que le verrou est réel. `mutool show secret.pdf trailer` répond `cannot authenticate password`. Le dictionnaire de chiffrement dit `/AESV3`, `/R 6`. Tout ressemble exactement à ce que de la crypto forte est censée être.

Étape 3 : l'attaque, sans mot de passe :

```text
$ v/bin/python pocs/pdf_decryptors/mupdf/decrypt.py secret.pdf decrypted.pdf
[+] Recovered and verified the AES-256 file key
    seed time(NULL) mod 512 = 33
    key  022531fd36d99f642258484ad123e7ab0188b951af6718623a11b813364c7c7b
[+] Wrote unencrypted PDF to decrypted.pdf
                                      (0.12 s user, 0.63 s wall)
```

Étape 4 : lire le clair :

```text
$ mutool draw -F txt -o - decrypted.pdf
TOP SECRET: the mermaid lands at 0400. Auth code KHAKI-7741.
```

Mille deux cents millisecondes après avoir rencontré le fichier, sa protection « AES-256 » n'est plus qu'un souvenir. Le PoC ré-encapsule ensuite la clé récupérée sous un mot de passe connu et laisse mutool écrire une copie propre ; le brute force n'a jamais été nécessaire parce qu'il n'y a jamais eu que 512 clés.

## Foxit : SHA-256, un timestamp, et le mot « there »

Foxit Reader 2026.1.3.36551 dérivait sa clé de fichier par **SHA-256 d'un timestamp 32 bits, de 32 octets non initialisés (des zéros en pratique), et de la chaîne littérale `"there"`**. Depuis le PoC Rust publié, verbatim :

```rust
material[..4].copy_from_slice(&timestamp.to_le_bytes());
material[36..].copy_from_slice(b"there");
```

Trente-deux bits de timestamp, ça fait 2^32 candidates au pire, mais le check en clair connu de `/Perms` ébranche instantanément, et une recherche sur 32 threads couvre **chaque seconde depuis 1970 en moins de cinq secondes**. Les octets de mémoire non initialisée ajoutent zéro entropie sur chaque machine testée par V12.

Le détail de lignée qui élargit le rayon d'explosion : cette dérivation exacte apparaît dans **le premier commit public de PDFium (mai 2014)**, le fichier créditant Foxit comme auteur original. PDFium est le moteur PDF de Chromium, embarqué dans d'innombrables éditeurs et lecteurs. Quiconque a copié ce chemin de code a hérité d'une clé « AES-256 » dérivée d'un timestamp.

OpenPDF 3.0.5 et iText 9.7.1 ferment l'ensemble : clés issues d'un **flux ARC4 seedé par un timestamp en millisecondes plus la mémoire libre de la JVM**, devinables depuis les sels en clair de `/U` et `/O`, avec un espace de recherche plus grand mais restant traçable.

## Le chiffrement n'a jamais été le problème

C'est le motif du mois entier, en miniature. AES-256 va bien. L'encapsulation par mot de passe va bien. La spec (révision 6) va bien. Ce qui a cassé, c'est la plomberie ennuyeuse entre « la spec dit aléatoire » et « le code a appelé rand() » : un LCG seedé par une horloge, de la mémoire non initialisée, une chaîne que quelqu'un needed pour l'alignement. La même classe de défaillance que la CA dont la clé intermédiaire valait le chiffre 4 et le pool KV dimensionné à 65 % de la fenêtre de contexte : **le primitif fort au bout d'un tuyau faible est un primitif faible**. « AES-256 » sur une liste de fonctionnalités est une promesse sur 2^256, et la seule chose qui la rende vraie, c'est d'où viennent les octets de la clé.

## Quoi faire maintenant

- **Utilisateurs MuPDF** : la 1.28.5 corrige la génération de clés, mais **ne répare pas les fichiers existants** : chaque PDF AES-256 écrit par un MuPDF antérieur a encore aujourd'hui une des 512 clés. Si ces documents comptent, traite-les comme non chiffrés et réémet-les : nouveau fichier, logiciel à jour. `pymupdf` embarque un MuPDF vulnérable sur beaucoup de versions, donc checke ce que ton pipeline embarque (`pymupdf.mupdf_version_tuple`).
- **Foxit / dérivés PDFium** : mets à jour, puis suppose que les PDF écrits par les versions affectées sont récupérables par timestamp et réémet ce qui compte.
- **Tout le monde** : la prochaine fois qu'un vendor dit « AES-256 de grade militaire », demande d'où viennent les octets de la clé. Cette question, répondue honnêtement, c'est tout le génie logiciel cryptographique.

**TL;DR** : les PDF « AES-256 » protégés par mot de passe produits par MuPDF < 1.28.5 ont 9 bits d'entropie de clé : 512 candidates, 7 ms pour les générer, récupération en moins d'une seconde avec des outils publics. Foxit hashait un timestamp et la chaîne « there » ; PDFium a porté ce code depuis 2014. J'en ai créé un, verrouillé, puis déchiffré sans mot de passe dans mon lab en moins d'une seconde, avec chaque commande ci-dessus reproductible.

Sources : [V12 : The case of the 9 bit AES key](https://v12.sh/blog/the-case-of-the-9bit-aes-key) · [PoC decryptors (v12-security/pocs)](https://github.com/v12-security/pocs) · correctif MuPDF dans la 1.28.5
