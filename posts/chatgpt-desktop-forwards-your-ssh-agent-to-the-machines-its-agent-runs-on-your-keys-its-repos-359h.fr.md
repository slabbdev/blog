---
titre: "ChatGPT Desktop transfère ton agent SSH vers les machines où son agent tourne : tes clés, ses repos"
date: 2026-11-09
themes: securite, agents
resume: "Le codex app-server dans ChatGPT Desktop embarque un flag --forward-ssh-agent : ton agent SSH local est partagé dans l'environnement d'exécution de l'agent via un socket stable, donc les processus de l'agent peuvent signer en ton nom et pousser sur tes repos GitHub privés. Ce que le source montre, et le durcissement en deux commandes."
source: https://dev.to/slabb/chatgpt-desktop-forwards-your-ssh-agent-to-the-machines-its-agent-runs-on-your-keys-its-repos-359h
image: https://media2.dev.to/dynamic/image/width=1000,height=420,fit=cover,gravity=auto,format=auto/https%3A%2F%2Fdev-to-uploads.s3.us-east-2.amazonaws.com%2Fuploads%2Farticles%2Fqknhk0s5z6tvkpsxscx6.png
image_alt: "ChatGPT Desktop transfère ton agent SSH vers les machines de son agent : tes clés, ses repos"
---

> Le drop HN d'hier matin, une ligne : *« L'agent qui tourne sur une machine distante peut s'authentifier avec tes identifiants SSH locaux. Ça veut dire qu'il peut pusher sur tes repos privés GitHub, par exemple. »* La preuve liée n'est pas un coup de gueule, c'est l'ingénierie d'OpenAI elle-même : [PR #28131 sur openai/codex](https://github.com/openai/codex/pull/28131), titrée *« [codex] Refresh SSH agent for app-server proxy »*, dont les commentaires de review discutent tranquillement de la ligne d'environnement du daemon `SSH_AUTH_SOCK=~/.codex/app-server-control/forwarded-ssh-agent.sock`, plus une issue compagne sur des clients desktop qui s'écrasent mutuellement *l'agent SSH partagé*. Traduction : **l'infrastructure de l'agent embarque ton agent SSH par défaut.** Les processus que l'agent génère peuvent signer des challenges avec tes clés, silencieusement, parce que c'est précisément à ça que sert la fonctionnalité. Ce post : ce que le source montre vraiment, pourquoi ça compte plus que la fuite quotidienne habituelle, et le durcissement en deux commandes qui rend la signature silencieuse impossible.

## Ce que le source montre

Trois artefacts, tous publics, tous des repos d'OpenAI :

1. **Le flag** : l'intégration codex app-server (ce que ChatGPT Desktop utilise pour lancer les sessions Codex) accepte `--forward-ssh-agent`. Son but est dans le nom : prendre l'agent SSH local de l'utilisateur et le rendre disponible dans l'environnement d'exécution de l'agent.
2. **Le socket stable** : le daemon est lancé avec `SSH_AUTH_SOCK=~/.codex/app-server-control/forwarded-ssh-agent.sock`, donc tout ce que l'app-server génère, shells, outils, commandes d'agent, hérite d'un chemin fonctionnel vers tes clés. Le fil de review du PR, ce sont des ingénieurs qui corrigent soigneusement des edge cases de refresh du socket (un symlink périmé après une nouvelle session SSH, un client desktop qui écrase le lien partagé d'un autre), et ça te dit que ce n'est pas un prototype : c'est maintenu, partagé, et conçu ainsi.
3. **L'issue compagne** (#59694) : « Remote SSH : one desktop client overwrites the shared SSH agent used by [d'autres sessions] » confirme que plusieurs sessions clients partagent un même agent transféré.

Pour être précis sur les claims, parce que le sujet le mérite : c'est une **fonctionnalité, documentée dans le code, dont la conséquence est un transfert de capacité**. Personne n'a montré de malware l'exploitant. Le cadrage HN est le bon : *l'agent qui tourne à l'autre bout* peut s'authentifier comme toi, partout où tes clés sont acceptées : GitHub (push sur les repos privés), les serveurs de ton `~/.ssh/config`, tout ce que ton socket d'agent peut signer. La question de sécurité n'est pas « y a-t-il un bug », c'est « l'utilisateur a-t-il compris qu'ouvrir l'app donne à l'environnement de l'agent le pouvoir de signer en son nom, et peut-il voir chaque usage ? ».

## Pourquoi celle-là coupe plus profond que la fuite habituelle

Le mois nous a servi une séquence d'incidents de vie privée des agents, chacun sur des *données* qui sortent : les transcripts envoyés au modèle, une adresse email dans un User-Agent, Postman qui édite les configs des agents rivaux. Les fuites de données sont graves ; **les fuites de capacité crédentielle sont un autre genre**. Un email dans un header fait de toi une cible de scam. Un agent SSH vivant dans le sandbox de l'agent fait du sandbox *toi* : tes pushes GitHub, tes logins serveur, ton accès deploy, sans mot de passe, sans prompt 2FA, sans trace au-delà des logs d'auth. Et le rayon d'explosion se compose en silence : les sandboxes d'agents exécutent des commandes choisies par le modèle. Une instruction injectée par prompt qui dit « pousse cette branche sur le repo privé de l'utilisateur » n'a besoin d'exfiltrer rien du tout ; elle a besoin que l'environnement contienne déjà ton identité. Désormais, il la contient, par design.

La vieille sagesse SSH était « jamais `ForwardAgent yes` vers un hôte dont tu n'es pas sûr à 100 % ». Le nouveau monde emballe exactement cette décision dans les defaults d'une app desktop, pointée vers un environnement d'exécution qui fait tourner du code généré. Le principe n'a pas changé ; la visibilité de la décision, si.

## L'audit et le durcissement : deux commandes chacun

**Audit** (toute machine ; je les ai lancées sur la mienne ce soir : aucun artefact codex, agent actif avec zéro identité, la baseline propre exacte) :

```bash
# 1. Un socket de transfert d'agent existe-t-il pour ton outillage IA ?
ls -la ~/.codex/app-server-control/ 2>/dev/null || echo "no codex agent socket"

# 2. Qu'est-ce qui pourrait être signé en ton nom là, maintenant,
#    par n'importe quoi qui partage ton agent ?
ssh-add -l        # "The agent has no identities." = rien à abuser (ma sortie ce soir)
                  # une liste d'empreintes = celles-ci peuvent signer, en silence, par processus

# 3. Bonus : qui est ton socket d'agent, et est-il par-session ou système ?
echo "$SSH_AUTH_SOCK"
```

**Durcissement**, par ordre d'efficacité :

```bash
# 1. Rendre chaque usage de ta clé un acte explicite : charger avec confirmation par usage
ssh-add -c ~/.ssh/id_ed25519
# désormais, CHAQUE demande de signature (y compris depuis un sandbox d'agent)
# fait pop un dialog de confirmation natif. La signature silencieuse devient impossible.

# 2. Mieux : des clés qui exigent une présence, pas juste une confirmation.
# Sur macOS, génère des clés dans la Secure Enclave (touch requis) :
ssh-keygen -t ed25519-sk   # ou utilise le YubiKey que tu possèdes déjà
# une clé liée au matériel ne peut pas être « partagée » ; l'agent transfère un socket,
# mais chaque signature exige le tap physique.

# 3. Affamer l'environnement de l'agent : lance les apps desktop IA SANS ton agent
launchctl setenv SSH_AUTH_SOCK ""   # (les approches par session varient)
# ou simplement : ne garde pas de clés chargées (ssh-add -D) pendant les sessions d'agent.
```

L'option 1 est la sleeper : `ssh-add -c` a des décennies, marche avec les clés que tu as déjà, et convertit toute cette classe de problème en un dialog que tu approuves ou que tu tues. Si une popup de confirmation apparaît pour une signature que tu n'as pas demandée, tu viens d'attraper ton agent (ou quelque chose en lui) en train d'essayer d'être toi, en flagrant délit, avec la preuve à l'écran.

Et côté produit, la demande est simple et vieille : les fonctionnalités d'agent qui utilisent des capacités d'identité devraient demander à chaque usage, pas à l'installation. Apple a eu besoin des prompts Touch ID pour rendre l'accès au trousseau macOS digne de confiance ; une app desktop IA qui détient une capacité SSH vivante devrait rencontrer la même barre.

## Le grand livre du mois, dernière ligne

Transcripts, emails dans le User-Agent, éditions de configs dans les outils rivaux, et maintenant le transfert de capacité de clés : chaque histoire a déplacé la même frontière d'un pas, de *ce que l'agent lit* vers *ce que l'agent peut faire*. Le fil conducteur de cette série, c'est que la surface sortante de l'agent est la surface sortante de l'utilisateur. Le forwarding d'agent SSH, c'est cette phrase rendue littérale : la surface inclut désormais tes opérations de clé privée. Traite l'environnement de l'agent comme un jump host que tu ne contrôles pas entièrement : clés minimales, confirmation à l'usage, lié au matériel là où ça compte. Et quand l'app desktop demande pourquoi le push a échoué, la bonne réponse est : parce que tu aurais dû demander.

**TL;DR** : l'intégration Codex de ChatGPT Desktop transfère ton agent SSH dans l'environnement d'exécution de l'agent (`--forward-ssh-agent`, socket stable à `~/.codex/app-server-control/forwarded-ssh-agent.sock`, partagé entre sessions selon le PR et les issues d'OpenAI). C'est une capacité conçue, pas un bug : les processus côté agent peuvent signer en ton nom, y compris des pushes sur des repos privés, en silence. Audite avec `ssh-add -l` et un check de répertoire ; durcis avec `ssh-add -c` (confirmation par usage) ou des clés matérielles `ed25519-sk`, et ne fais pas tourner de sessions d'agent avec des clés chargées que tu ne confierais pas à un jump host.

Sources : [HN : ChatGPT Desktop forwards your SSH agent](https://news.ycombinator.com/item?id=50422628) · [openai/codex PR #28131 : Refresh SSH agent for app-server proxy](https://github.com/openai/codex/pull/28131) (chemin du socket et design dans les commentaires de review) · [openai/codex issue #59694 : agent SSH partagé entre clients desktop](https://github.com/openai/codex/issues/59694)
