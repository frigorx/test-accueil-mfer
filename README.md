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

## Le mode « SchoolRoom » : le PC du professeur fait tout

```
python serveur-test-accueil.py
```

1. **Le PC crée son Wi-Fi** : Paramètres Windows → Réseau et Internet → *Point d'accès mobile* → activer.
   Windows demande que le PC soit lui-même relié à un réseau (câble ou Wi-Fi du lycée) pour activer le
   point d'accès. Le PC prend alors l'adresse **192.168.137.1**.
2. **Projeter** `http://localhost:8765/projeter` : l'adresse en très gros (et le QR code si le module
   `qrcode` est installé : `pip install qrcode[pil]`, une fois). Les élèves se connectent au Wi-Fi du
   professeur, ouvrent l'adresse, tapent leur nom, choisissent leur classe.
3. **Suivre** `http://localhost:8765/resultats` : qui est connecté, à quel niveau, à quelle question,
   combien de sorties de la page (rouge à partir de trois), et les résultats reçus au fur et à mesure.
4. **Cartographier** `http://localhost:8765/cartographie` : élèves × compétences, colorée de 1 (non acquis)
   à 4 (parfaitement maîtrisé), part de la classe à « acquis » par compétence ; `cartographie.csv` pour le
   tableur. Tout reste dans `resultats/` sur le PC.

Rien ne sort du PC : les téléphones n'ont pas besoin d'Internet ni de forfait.

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

Voir aussi `PROCEDURE-COLLECTE.md` (les modes de récupération) et `_PLAN-QUIZ-POSITIONNEMENT.md`.
