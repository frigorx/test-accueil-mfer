# Tests sur téléphone — 1re MFER, CAP IFCA, 2de TNE, Terminale MFER

Deux pages, un serveur, rien à installer.

| Page | À quoi elle sert | En ligne | Sur le PC du professeur |
|---|---|---|---|
| `index.html` | **Test d'accueil** : sécurité, règlement, règles de la classe, 41 questions, 1 h, noté sur 20 avec compétences | https://frigorx.github.io/test-accueil-mfer/ | `http://ADRESSE:8765/` |
| `positionnement.html` | **Positionnement** : six niveaux adaptatifs, du niveau 0 (règles) au niveau 5 (expert), habilitations fluide et électrique comprises ; non noté ; carte des compétences | https://frigorx.github.io/test-accueil-mfer/positionnement.html | `http://ADRESSE:8765/positionnement.html` |

La source des deux pages est dans le dossier 1re MFER pour le test d'accueil
(`C:\git\progression-1re-mfer\00-dossier\Test-numerique-accueil-securite-et-regles.html`, recopié ici en
`index.html`) et ici pour le positionnement. La banque de questions du positionnement est `banque.json`,
construite depuis `banque/niveau-N.json` par `python construire-banque.py` (qui pose aussi la palette de
symboles dans la page).

## « Test de rentrée » : un clic sur le Bureau

Le raccourci **Test de rentrée** du Bureau (icône bleue à coche) lance `Test-de-rentree.cmd` : le serveur
démarre sur le PC et le **poste de commande** `http://localhost:8765/prof` s'ouvre dans le navigateur.
Le lancer une deuxième fois rouvre seulement le poste de commande. Sur un autre poste, exécuter une fois
`Test-de-rentree.cmd` : il pose lui-même le raccourci sur le Bureau. Les pages du professeur (`/prof`,
`/projeter…`, `/resultats…`, `/cartographie…`) ne s'ouvrent que sur le PC : un téléphone reçoit « 403 ».

Le poste de commande, en cinq blocs :

1. **Projeter au tableau** — soit `/projeter-en-ligne` : les deux QR codes des tests en ligne (les élèves
   ont Internet, 4G ou Wi-Fi du lycée ; résultats par WhatsApp et capture d'écran) ; soit `/projeter` :
   le Wi-Fi du PC et l'adresse locale (mode fermé, tout arrive sur ce PC).
2. **Suivre** — `/resultats` : qui est connecté, à quel niveau, à quelle question, combien de sorties de la
   page (rouge à partir de trois), et les résultats reçus au fur et à mesure ; `/cartographie` : élèves ×
   compétences, colorée de 1 (non acquis) à 4 (parfaitement maîtrisé), part de la classe à « acquis » par
   compétence ; les deux CSV pour le tableur. Tout reste dans `resultats/` sur le PC.
3. **Vérifier moi-même** — ouvrir les deux tests sur le PC comme un élève.
4. **Les liens en ligne** — à copier, avec le numéro WhatsApp dans le lien.
5. **Réglages** — `reglages.json` à côté du serveur, jamais publié : `whatsapp` (numéro au format
   international, sans + ni espaces), `ssid` et `motdepasse` du Wi-Fi du PC pour le mode fermé, `adresse`
   si celle détectée n'est pas la bonne.

**Le mode fermé** : Paramètres Windows → Réseau et Internet → *Point d'accès mobile* → activer (Windows
demande que le PC soit lui-même relié à un réseau, câble ou Wi-Fi du lycée). Le PC prend l'adresse
**192.168.137.1**. Les téléphones n'ont alors besoin ni d'Internet ni de forfait, et rien ne sort du PC.

**Deux limites à connaître.** Le point d'accès mobile de Windows accepte **huit appareils au plus** : pour une
classe entière, soit deux vagues, soit le Wi-Fi du lycée (le PC et les téléphones sur le même réseau, à
condition que ce réseau laisse les appareils se parler), soit un petit routeur Wi-Fi à soi, relié à rien,
auquel le PC et les téléphones se connectent : c'est le montage le plus sûr. Et au premier lancement,
Windows demande d'autoriser Python sur le réseau : autoriser, sinon les téléphones ne voient pas le PC.

## Ce que voit l'élève à la fin

Un cadre à capturer en photo d'écran (nom, classe, date et heure, niveau atteint ou note, compétences, code de
validation), et selon les réglages du bloc `COLLECTE` en tête de la page : un bouton WhatsApp
(`wa.me`, numéro du professeur au format international), un bouton courriel, le bouton « copier ».

**Le numéro du professeur ne s'écrit pas dans la page publique** : il se passe dans le lien donné aux élèves,
`…/positionnement.html?wa=33612345678` (pareil pour `index.html`), et la page le lit. La page à projeter en
classe, avec les deux QR codes portant ce lien, est dans `a-projeter/` (non versionné, refait par
`python faire-la-page-a-projeter.py NUMERO`).

## Les sorties de la page

Chaque sortie (autre application, écran verrouillé, page fermée) est comptée. Test d'accueil : un point en
moins par sortie, arrêt à la cinquième. Positionnement : comptées et affichées, arrêt à la cinquième.

**Un écran qui s'éteint tout seul compte comme une sortie.** Les deux pages demandent donc au téléphone de
garder l'écran allumé pendant le test (Wake Lock : Android, et iPhone à partir d'iOS 16.4, en https donc sur
les pages en ligne ; pas en mode fermé, qui est en http). Partout où cela ne marche pas, la consigne est
écrite au départ et sur les pages à projeter : verrouillage automatique sur « Jamais ». Le serveur du PC
n'autorise aucun cache : après une modification, les téléphones voient tout de suite la nouvelle page.

Voir aussi `PROCEDURE-COLLECTE.md` (les modes de récupération) et `_PLAN-QUIZ-POSITIONNEMENT.md`.
