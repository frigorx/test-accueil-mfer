# Récupérer les notes du test d'accueil

**Mode retenu le 10/09/2026 (F. Henninot) : la capture d'écran.** L'écran de résultat tient dans un
cadre orange fait pour être capturé : nom, machine, classe, date et heure, note sur 20, compétences,
niveaux, code de validation. L'élève l'envoie au professeur, qui note en direct. Le code protège
contre une capture retouchée : il dépend du nom, de la machine et des réponses. Les deux canaux
ci-dessous restent disponibles si un jour on veut automatiser.

La page est servie par GitHub Pages : https://frigorx.github.io/test-accueil-mfer/

Elle ne peut rien enregistrer par elle-même (pas de serveur). Les résultats partent donc dans
**un formulaire Google à vous**, que la page remplit et envoie toute seule quand l'élève termine :
chaque résultat devient une ligne de la feuille de réponses, dans votre Google Drive.

## Sans Internet : le serveur local sur le PC du professeur (esprit SchoolRoom)

`python serveur-test-accueil.py` dans ce dossier (Python seul, rien à installer). Le PC sert la page
aux téléphones du même réseau Wi-Fi (ou du point d'accès mobile du PC) et **reçoit les résultats** :

- élèves : `http://ADRESSE-DU-PC:8765/` (l'adresse s'affiche au lancement ; les élèves la tapent) ;
- professeur : `http://localhost:8765/resultats` (tableau vivant : heure, nom, classe, note, sorties,
  répondu, code, compétences) et `http://localhost:8765/resultats.csv` pour le tableur ;
- fichiers : `resultats/test-accueil.jsonl` (jamais effacé) et `resultats/test-accueil.csv`.

La page détecte qu'elle est servie par le PC et y envoie le résultat toute seule ; la capture d'écran
reste demandée par sécurité. Au premier lancement, Windows demande d'autoriser Python sur le réseau :
autoriser. Aucun forfait, rien ne sort du PC.

**Les sorties de la page** (dans la page, quel que soit le mode) : chaque fois que l'élève quitte la
page (autre application, écran verrouillé, page fermée ou rechargée), il perd un point ; à la
cinquième sortie le test s'arrête, l'écran l'envoie voir le professeur puis la vie scolaire. Le
compte est gardé sur le téléphone et apparaît dans le résultat.

## 1. Créer le formulaire (cinq minutes, une seule fois)

1. https://forms.google.com → « Formulaire vierge ». Titre : `Test d'accueil MFER — résultats`.
2. Créer **huit questions**, toutes de type **« Réponse courte »**, dans cet ordre et avec ces titres :
   `Nom` · `Machine` · `Note` · `Blocs` · `Code` · `Réponses` · `Diplome` · `Competences`.
   Aucune n'est obligatoire. Pas de connexion requise : dans « Paramètres » → « Réponses »,
   laisser **« Limiter à 1 réponse » décoché** et **ne pas** cocher « Collecter les adresses e-mail ».
3. En haut à droite, les trois points → **« Obtenir le lien pré-rempli »**. Écrire `a` dans chaque
   champ, cliquer « Obtenir le lien », puis « Copier le lien ».
4. Envoyer ce lien à Claude (ou le coller dans `index.html`, bloc `COLLECTE`, voir ci-dessous).
5. Onglet « Réponses » → icône Sheets → **« Créer une feuille de calcul »** : c'est là que les
   notes arrivent, une ligne par élève, avec la date.

## 2. Brancher la page

Le lien pré-rempli ressemble à :
`https://docs.google.com/forms/d/e/1FAIpQLSd…/viewform?usp=pp_url&entry.111=a&entry.222=a&…`

- la partie entre `/d/e/` et `/viewform` est l'identifiant du formulaire → `COLLECTE.formulaire` ;
- les huit `entry.NNN`, dans l'ordre des questions → `COLLECTE.champs.nom`, `machine`, `note`,
  `blocs`, `code`, `reponses`, `diplome`, `competences`.

Dans `index.html`, bloc `const COLLECTE = {…}`, puis `git commit` et `git push` : la page en ligne
se met à jour en une minute.

## 3. Ce que reçoit la feuille

| Colonne | Contenu |
|---|---|
| Horodatage | posé par Google |
| Nom | ce que l'élève a tapé |
| Machine | son équipe |
| Note | sur 20 |
| Blocs | justes par bloc, ex. `Les règles de la classe 6/9 · …` |
| Code | le code de validation, le même que sur son écran : il prouve que la ligne vient bien de la page |
| Réponses | la durée passée, puis `numéro:choix` pour les 41 questions (0 = juste), pour analyser les erreurs et repérer qui n'a pas travaillé |
| Diplome | `1re Bac Pro MFER` ou `2e année CAP IFCA` (choisi par l'élève au départ) |
| Competences | par compétence du référentiel choisi : justes / total et « acquis · en cours · à revoir » ; puis les trois niveaux « Je sais · Je comprends · Je fais le bon geste » |

## Second canal : le courriel

Dans le même bloc `COLLECTE`, `courriel: 'adresse@…'` fait apparaître sur l'écran de résultat un bouton
« Envoyer par courriel au professeur » : le téléphone ouvre sa messagerie avec le résultat déjà écrit
(nom, machine, note, blocs, code, réponses), l'élève n'a qu'à envoyer. Utile si le formulaire n'est pas
encore branché, ou pour les élèves sans réseau au moment du test. Mettre une adresse professionnelle,
pas une adresse personnelle : la page est publique.

## Sans formulaire branché

La page fonctionne quand même : l'élève montre son écran de résultat, recopie son code, ou
« Copier mon résultat » et le colle dans un message. Le code ne se devine pas (il dépend du nom,
de la machine et des réponses).
