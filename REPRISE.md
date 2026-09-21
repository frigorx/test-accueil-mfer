# Reprise — tests sur téléphone : test d'accueil, positionnement, « Test de rentrée »

**Dépôt** : `C:\git\test-accueil-mfer` · **public** sur GitHub (`frigorx/test-accueil-mfer`), pages en ligne :
https://frigorx.github.io/test-accueil-mfer/ (test d'accueil) et `…/positionnement.html` (positionnement).
**Ce fichier est le point d'entrée.** Mode d'emploi : `README.md` · plan, décisions et restes du positionnement :
`_PLAN-QUIZ-POSITIONNEMENT.md` · les modes de récupération des notes : `PROCEDURE-COLLECTE.md`.
**Dernière mise à jour : 18/09/2026, 11 h 20 — voir « État au 18/09 » juste dessous, puis le reste.**

## État au 18/09/2026 — l'échec du matin est EXPLIQUÉ (nom et mot de passe du Wi-Fi faux) ; reste à le prouver sur un téléphone

**Ce qui existe et marche (vérifié depuis le PC et depuis le téléphone de Franck le 17/09 au soir, chez lui) :**
- Un raccourci Bureau **« Séance sur téléphone »** (`Test-de-rentree.cmd`) lance le serveur (port 8765) et ouvre le poste de commande `http://127.0.0.1:8765/prof` (127.0.0.1 et non localhost : un vieux service worker « inerWeb Édu » traîne sur `localhost:8765` dans les navigateurs ; `/sw.js` sert un coupe-circuit).
- Le poste de commande porte un **formulaire** (Wi-Fi, mot de passe, numéro WhatsApp, lien du groupe, code de surveillance, liste de la classe collée) qui écrit `reglages.json` (ignoré par git). Réglé au 18/09 : Wi-Fi `inerweb.fr`, 26 élèves, groupe WhatsApp, code.
- L'accueil `/` des téléphones = menu : test d'accueil, positionnement (noté, barème dégressif), **`manometres.html`** (10 questions, cadrans à aiguille, notée), **`jeux/schema-frigo/`** (symboles normalisés, 2 niveaux), groupe WhatsApp. `jeux/` est ignoré par git (contient aussi une copie de la station ÉlectroRézo, retirée de l'accueil : marque inerWeb dans un outil du lycée).
- Pages du professeur (PC seul) : `/projeter` (3 QR : Wi-Fi, adresse, groupe), `/surveillance` (aussi sur téléphone avec le code : rouge après 60 s de silence, coupures comptées), `/bilan` + `/bilan.csv` (note du jour : le meilleur total vaut 20 ; alertes ; questions de règles fausses), `/resultats` (« qui a fait quoi »).
- **`questions-au-tableau.html`** : les questions projetées une à une au tableau, réponse révélée par Entrée, feuille de correction. **C'est ce qui a sauvé la séance du 18/09.** Son nom ne doit pas commencer par `/projeter`, `/prof`, `/qr`, `/bilan`, `/resultats`, `/surveillance`, `/groupe`, `/cartographie` (routes du serveur).
- Banque du positionnement : 196 questions (`banque/niveau-x-cuivre-et-bornes.json` ajouté : cuivre, cintrage, repérage des bornes, symboles).
- HAL Claw lit tout cela (incrément 303 : section « Séance sur téléphone » dans la fiche de séance du Mur, bouton d'activation, bilan ; bloc « Sur son téléphone » dans la fiche élève).

**Ce qui a échoué le 18/09 à 8 h — cause trouvée le même jour à 11 h : la borne n'était pas en panne.**
Les téléphones ne voyaient aucun réseau `inerweb.fr` parce que **ce réseau n'existe pas**. La borne
(GL-SFT1200, panneau v4.3.28) émettait normalement, en 2,4 GHz **et** en 5 GHz, SSID visible, puissance Max :

- nom réel : **`inerWeb-Classe`** (2,4 GHz) et `inerWeb-Classe-5G` — **majuscules comprises**, un SSID y est sensible ;
- mot de passe réel : celui d'**usine** de GL.iNet, 8 caractères, pas `azertyuiop`. Jamais écrit ici (dépôt public) :
  il est dans `reglages.json`, et lisible dans le panneau, Wireless → icône œil du champ Wi-Fi Password.

`reglages.json` a été corrigé sur les deux points, donc le QR Wi-Fi projeté est juste désormais. Écartés au
passage, avec preuve : le serveur écoute sur `0.0.0.0:8765` et répond HTTP 200 sur `192.168.8.184:8765` ; le
pare-feu Windows porte déjà une règle entrante « Python » activée, profil **Public**, TCP, tous ports ; la borne
n'a pas d'Internet (« No cable detected in WAN port »), sans importance pour la séance elle-même.

**Piège d'outillage à retenir : le scan Wi-Fi du PC ment.** `netsh wlan show networks` ne rend qu'un réseau à la
fois, au hasard, surtout quand la carte est déjà associée. C'est lui qui a fait croire le matin que « le routeur
n'émet rien ». Il faut le lancer **en boucle** (20 passes espacées de 2,5 s, en accumulant les noms) pour obtenir
la liste complète : c'est ainsi que les vrais SSID ont été relevés. Un téléphone est un bien meilleur scanner.

**Ce qui n'est toujours PAS prouvé :** aucun téléphone n'a encore ouvert `http://192.168.8.184:8765/`. Le Pixel
de Franck refuse de quitter le Wi-Fi de sa box ZTE — qui a Internet — pour un réseau qui n'en a pas ; la liste
des clients de la borne (`192.168.8.1` → Clients) est restée à **un seul appareil, le PC, par câble**. Un
téléphone d'élève, qui ne connaît pas cette box, n'a pas ce conflit.

**À faire la prochaine fois, À L'ÉCOLE, borne allumée et câble branché :**
1. Lancer « Séance sur téléphone » et vérifier que le PC reprend bien `192.168.8.184`. Si l'Ethernet est en
   `169.254.x.x`, la borne n'est pas branchée ou pas allumée : rien d'autre ne sert tant que ce n'est pas réglé.
2. **Un téléphone qui ne connaît pas la box ZTE** : scanner le QR Wi-Fi de `/projeter`, puis le QR d'adresse.
   Le menu des activités doit s'ouvrir. Contrôle côté borne : `192.168.8.1` → Clients, le téléphone doit y figurer.
3. Sur le Pixel de Franck seulement : **oublier `ZTE_E878AE`** avant d'essayer, sinon il ne basculera pas.
4. Puis cinq téléphones, puis la classe.
5. Confort, seulement une fois la chaîne prouvée : borne en **répéteur** sur la box (les téléphones ont alors
   Internet et ne décrochent plus — demande de saisir le mot de passe de la box) ; **portail captif** pour que le
   menu s'ouvre seul après le seul QR Wi-Fi ; remplacer le mot de passe d'usine, et refaire le QR derrière.
6. Ensuite la suite côté HAL Claw : `C:\git\HAL-Claw\CHANTIER-SEANCE-TELEPHONE-2026-09-18.md`.

**Commits** : le travail des 17 et 18/09 est commité localement, rien n'est poussé (dépôt public : feu vert de Franck avant tout push). Le dossier de classe : `C:\git\progression-1re-mfer\_carte-commune\chantier-vendredi-18-09.md`.

## Avant d'écrire

```bash
git log --oneline -5
git status
```

Le dépôt est **public** : jamais de nom d'élève, de numéro de téléphone ni de mot de passe dedans.
`reglages.json` (numéro, Wi-Fi) et `resultats/` (les résultats reçus) sont ignorés par git : c'est voulu.

## Où en est le chantier (fait les 10 et 11 septembre 2026)

- **Test d'accueil** (`index.html`) : 41 questions, noté sur 20, compétences Bac Pro MFER et CAP IFCA,
  test individuel, sorties de la page pénalisées (un point par sortie, arrêt à la cinquième). La **source**
  est dans le dossier 1re MFER (`00-dossier/Test-numerique-accueil-securite-et-regles.html`) : on la modifie
  là, on la recopie ici, on pousse.
- **Positionnement** (`positionnement.html`) : six niveaux adaptatifs (N0 règles → N5 expert), quatre classes
  (CAP IFCA, 1re et Terminale MFER, 2de TNE en codes CC), non noté, carte des compétences 0-4, banque de
  **172 questions** (`banque/niveau-N.json` → `python construire-banque.py` → `banque.json`, 0 défaut),
  symboles de la palette du dossier, chaque question cite sa source.
- **« Test de rentrée »** : raccourci du Bureau → `Test-de-rentree.cmd` → `serveur-test-accueil.py`
  (Python seul) + **poste de commande** `http://localhost:8765/prof` : projeter (`/projeter-en-ligne` : QR codes
  des tests en ligne ; `/projeter` : Wi-Fi du PC et adresse locale), suivre (`/resultats`, `/cartographie`,
  deux CSV), vérifier, régler. Les pages du professeur ne s'ouvrent que sur le PC (403 ailleurs).
- **Le numéro WhatsApp** est dans `reglages.json` (hors dépôt) et voyage dans les liens (`?wa=`), jamais
  dans les pages. Le lanceur repose lui-même le raccourci sur le Bureau et installe le module `qrcode`.
- **Téléphones** (question de Franck, 11/09 : « et les iPhone ? ») : rien de récent dans le code (pas de
  syntaxe qui manquerait aux vieux iOS), viewport posé, champs à 18 px (pas de zoom forcé), symboles en ligne
  (Safari refuse les `use` externes), copie par `prompt` quand le presse-papiers est refusé (http local),
  WhatsApp et courriel par lien. **Piège trouvé** : l'écran qui s'éteint tout seul compte comme une sortie →
  garde d'écran (Wake Lock, https ; iPhone dès iOS 16.4) + consigne « verrouillage automatique sur Jamais »
  au départ et sur les pages à projeter. Le serveur du PC n'autorise plus aucun cache. Ce qui n'a pas pu être
  prouvé depuis le PC : la garde d'écran effective sur un téléphone (à voir le jour J).
- **Deux modes, une seule remontée automatique** (retour de Franck, 11/09 : « la remontée des notes n'aurait
  pas pu se faire toute seule ? … ça m'a demandé WhatsApp Business ») : quand les téléphones ouvrent la page
  **servie par le PC** (son Wi-Fi ou le Wi-Fi du lycée), le résultat part tout seul dans `resultats/` à la fin,
  rien à envoyer, pas de bouton WhatsApp. La page **en ligne** (GitHub) ne peut rien envoyer au PC (https vers
  http, bloqué par les navigateurs) : capture d'écran, WhatsApp ou courriel seulement, et WhatsApp est un
  canal faible (application absente, ou version Business qui réclame un choix). Le poste de commande propose
  donc le mode « téléphones sur ce PC » en premier, en vert ; les tests en ligne sont le secours.
- **Vérifié** : parcours CAP, MFER et TNE rejoués par script sur la vraie banque ; serveur (résultats, CSV,
  cartographie, suivi « En ce moment ») ; refus des pages du professeur depuis le réseau ; relancement quand
  le serveur tourne déjà ; pages publiées (GitHub Pages construit).

## Par quoi commencer la prochaine fois

1. **Le jour J** : un clic sur « Test de rentrée », projeter, suivre. Après la séance : `resultats/` et la
   cartographie ; noter dans ce fichier ce qui a coincé (Wi-Fi, téléphones, questions mal comprises).
2. **Les restes** : les quatre contradictions relevées par les rédacteurs (`_PLAN-QUIZ-POSITIONNEMENT.md`,
   § Résultat) à trancher ; sur l'autre poste, recréer `reglages.json` (`whatsapp`, `ssid`, `motdepasse`) et
   lancer une fois `Test-de-rentree.cmd` ; pour la classe entière, un routeur Wi-Fi à soi ou le Wi-Fi du lycée
   (le point d'accès Windows accepte huit appareils) ; l'ancien test d'accueil de Franck à fusionner s'il
   l'envoie ; pas de bon à tirer → rien n'est intégré au RAG de l'usine.
3. **Le dossier 1re MFER** (`C:\git\progression-1re-mfer`, `REPRISE.md` § 0) tient le carnet de bord de
   la classe ; ce dépôt-ci ne tient que l'outil.
