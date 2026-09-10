# Récupérer les notes du test d'accueil

La page est servie par GitHub Pages : https://frigorx.github.io/test-accueil-mfer/

Elle ne peut rien enregistrer par elle-même (pas de serveur). Les résultats partent donc dans
**un formulaire Google à vous**, que la page remplit et envoie toute seule quand l'élève termine :
chaque résultat devient une ligne de la feuille de réponses, dans votre Google Drive.

## 1. Créer le formulaire (cinq minutes, une seule fois)

1. https://forms.google.com → « Formulaire vierge ». Titre : `Test d'accueil MFER — résultats`.
2. Créer **six questions**, toutes de type **« Réponse courte »**, dans cet ordre et avec ces titres :
   `Nom` · `Machine` · `Note` · `Blocs` · `Code` · `Réponses`.
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
- les six `entry.NNN`, dans l'ordre des questions → `COLLECTE.champs.nom`, `machine`, `note`,
  `blocs`, `code`, `reponses`.

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
| Réponses | `numéro:choix` pour les 40 questions (0 = juste), pour analyser les erreurs |

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
