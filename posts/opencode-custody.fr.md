---
titre: "OpenCode a perdu les clés qui vivaient dans son cloud. Celles sur le disque allaient bien."
date: 2026-10-19
themes: securite, agents
resume: "Une intrusion dans la console en ligne d'OpenCode a exposé 1,4 % des clés API stockées — des factures à cinq chiffres à 3h du matin, Anthropic et Google qui bloquent les clés, OpenAI qui rembourse. Les utilisateurs du CLI ont dormi. L'incident n'a pas eu besoin du mobile de distillation contesté pour prouver la règle d'architecture : le grade de custody de votre clé, c'est la politique de rétention de l'endroit où vous l'avez posée."
---

> Les clés d'API sont des cartes bancaires sans plafond. Cette semaine, quelqu'un a forcé le bureau de celui qui détient le plafond — et la partie intéressante n'est pas de savoir qui. La partie intéressante, c'est que l'intrusion a trié les utilisateurs en deux groupes selon l'architecture, et qu'un groupe a dormi pendant ce temps.

Mi-octobre, des attaquants sont entrés dans la **console en ligne d'OpenCode**, un agent de programmation open source positionné comme alternative à Claude Code ou Cursor. Certains développeurs y stockaient leurs clés d'API des fournisseurs IA — un espace de travail pratique où la plateforme garde vos identifiants et proxifie vos appels. Les clés ont fuité. [Le papier d'Actu.ai](https://www.actu.ai/opencode-piratage-cles-api-factures-ia-proteger-ses-cles-80037.html) et les déclarations d'OpenCode sur X reconstituent l'incident : **1,4 % des utilisateurs de la console** touchés, alertes de dépense à 3h du matin, factures de plusieurs centaines à plus de **1 000 $** chez OpenAI, Anthropic et Google.

La machinerie de réponse a fonctionné comme prévu. Anthropic et Google ont **bloqué les clés exposées** ; OpenAI a rétabli l'accès et **remboursé les crédits consommés** ; OpenCode rembourse les frais non autorisés. Le cofondateur Dax Raad rapporte des tentatives d'intrusion continues pendant 48 heures.

## La fracture qui compte plus que la brèche

Voilà ce que je mettrais sur une slide. L'incident a divisé les utilisateurs d'OpenCode en deux populations, et la ligne de partage n'était ni la chance, ni le niveau de patch, ni la force du mot de passe :

- **Les clés stockées dans la console cloud** — la politique de rétention de la plateforme devenait *le* grade de custody de votre clé. 1,4 % de cette population a été détroussée.
- **Les clés restées sur la machine** — le CLI et l'app locale n'envoient jamais les clés sur les serveurs d'OpenCode. Zéro membre de cette population a été exposé. Pas « moins exposé ». Structurellement inatteignable par cette attaque.

La déclaration d'OpenCode elle-même est la preuve : l'app et le CLI sont intacts *parce que les clés utilisées par ces outils ne transitent jamais par leurs serveurs*. Le vendeur a publié la règle d'architecture en même temps que la brèche de l'architecture qui l'a brisée.

## Et l'histoire de distillation, alors ?

Le mobile revendiqué est une « attaque de distillation à grande échelle » — brûler des clés volées à volume industriel pour entraîner un modèle concurrent sur les sorties d'un modèle frontier, depuis des régions où les modèles américains sont restreints. C'est une histoire séduisante, et [des observateurs sont ouvertement sceptiques](https://www.actu.ai/opencode-piratage-cles-api-factures-ia-proteger-ses-cles-80037.html) : pour eux, c'est une intrusion classique, et la distillation comme finalité n'est pas démontrée. OpenCode n'a pas dit comment les attaquants sont entrés, ni comment les clés étaient stockées.

Je vais proposer quelque chose qui sonne froid : **le mobile ne change rien à la conclusion d'ingénierie.** Que les voleurs veuillent des données d'entraînement ou juste de l'inférence gratuite, la condition exploitable était identique — des clés détenues en custody par une console web tierce. Votre défense ne doit pas dépendre d'un récit que le vendeur n'a pas pu confirmer non plus. Les faits d'abord : le stockage de clés côté serveur a fui, le stockage côté machine non. L'histoire, c'est le post-mortem de quelqu'un d'autre.

## Exécutez chez vous : l'audit de custody

Vous ne pouvez pas auditer OpenCode. Vous pouvez vous auditer vous-même, en un pipeline — la question n'est pas « mes clés sont-elles en sécurité » mais « **où vivent-elles physiquement, et qui contrôle ce stockage** ». Comptez les endroits où vos clés se trouvent réellement :

```sh
# 1. des clés qui traînent dans les configs shell et les dotfiles (on compte, on n'imprime pas)
grep -rlE "sk-ant-[a-zA-Z0-9_-]{20,}|sk-[a-zA-Z0-9]{20,}|AIza[0-9A-Za-z_-]{35}" \
  ~/.zshrc ~/.bashrc ~/.profile ~/.config 2>/dev/null

# 2. des clés dupliquées dans les .env de projets (chaque copie est une surface de rétention)
find ~ -maxdepth 4 -name ".env" -not -path "*/node_modules/*" 2>/dev/null \
  -exec grep -lE "sk-ant-|sk-[a-zA-Z0-9]{20,}|AIza" {} \;

# 3. des clés commises dans l'historique git — la surface de rétention qui vous survit
git log --all --full-history -p -- . 2>/dev/null | grep -cE "sk-ant-[a-zA-Z0-9_-]{20,}"
```

Règle un : le résultat d'un audit est un *comptage et un emplacement*, jamais la clé elle-même. Règle deux : chaque emplacement en sortie est une surface de rétention que vous contrôlez (votre disque, chiffré au repos, votre keychain) ou ne contrôlez pas (la console web de quelqu'un, le cache CI de quelqu'un, l'historique git de quelqu'un). Règle trois, venue de l'incident : **les clés qui ne vivent que sur votre machine ne peuvent pas fuir dans une brèche de console** — ce n'est pas une bonne pratique, c'est une propriété d'architecture.

Puis fermez la boucle de manière ennuyeuse : des clés par projet au lieu d'une clé unique (une fuite est contenue), des plafonds de dépense durs chez le fournisseur (l'alerte de 3h du matin devient un rejet de 3h du matin), et la rotation au moindre doute — la rotation bat la suppression, parce qu'une clé supprimée dans le dump d'exfiltration de quelqu'un reste valide jusqu'à révocation.

## Le grade de custody, appliqué au key material

Mon dernier post de cette série portait sur l'industrie des CA découvrant qu'un témoin doit vivre quelque part que l'attaquant ne peut pas atteindre — cinq perspectives, deux RIR, un quorum. Le même `min()` traverse cette brèche. Votre clé d'API a un grade d'authoring (vous l'avez tapée, vous contrôlez les octets) et un grade de custody (l'endroit où vous l'avez *stockée*, et la politique de rétention de celui qui garde ce stockage). Stockez-la dans une console web et votre grade de custody, c'est la discipline de patch de cette console, sa réponse à incident et le vetting de ses employés — rien de tout cela n'apparaît dans votre modèle de menace avant que 1,4 % de la base utilisateurs ne reçoive un e-mail.

Nous avons livré la réponse sur notre propre stack la même semaine, parce que la règle n'est pas neuve même quand l'actualité l'est : les clés vivent dans le keychain de l'OS, liées à l'origine qu'elles appellent, et l'agent qui les utilise ne doit jamais les lire — [`navette creds set`](https://github.com/slabbdev/navette) enregistre un mot de passe que vous tapez une fois, le range dans le Keychain, et l'agent ne reçoit qu'un `{logged_in: true}`. Et si vous voulez *savoir* ce que votre agent émet au lieu de lui faire confiance, c'est le rôle d'un proxy de logging devant le client — [un fichier, pas de clé API, capture verbatim](https://dev.to/slabb/i-put-a-logging-proxy-in-front-of-an-llm-client-heres-what-it-emitted-5dii).

Les utilisateurs du CLI OpenCode avaient raison par architecture. Ayez raison par architecture.

---

*Sources : [Actu.ai — Piratage d'OpenCode](https://www.actu.ai/opencode-piratage-cles-api-factures-ia-proteger-ses-cles-80037.html) (20 oct. 2026), déclarations OpenCode sur X (Dax Raad). Le cadre custody suit [ce fil de commentaires](https://dev.to/fluffydesk/comment/3hmoi) et [le post five-witnesses](https://dev.to/slabb/five-witnesses-and-two-rirs-the-cas-just-discovered-custody-4aie).*
