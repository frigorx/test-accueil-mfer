# Chantier — « inerWeb QCM », station d'inerweb.fr (07/10/2026, chat 5 des finitions)

**Critère de réussite** : `inerweb.fr/qcm/` ouvre un accueil et trois activités qui marchent sur téléphone,
sans aucune trace de l'établissement, sans nom demandé, sans rien envoyer ; Franck l'a vue (lien direct)
et a donné son feu vert AVANT tout push.

**Décisions** : marque inerWeb (Franck, 07/10). Version « révision libre » (décision du 21/09) : pas de nom,
pas de sorties pénalisées, pas de note /20, résultat par compétences, rien ne remonte. L'outil de classe
n'est PAS modifié : `en-ligne/livrer.mjs` en tire une copie nettoyée ; chaque remplacement doit trouver sa
cible, sinon rien n'est écrit.

**Périmètre** : `positionnement.html`, `manometres.html`, `jeux/schema-frigo/`. Hors périmètre (scolaires) :
test d'accueil `index.html`, `apprentis/`, `jeux/r134a/`, `questions-au-tableau.html`.

## Étapes
- [x] 1. `en-ligne/` : accueil de la station, `revision.css` (masquages + filigrane R9), `filigrane.svg`, `livrer.mjs`
- [x] 2. `jeux/schema-frigo/` sous git (exception au `.gitignore`)
- [x] 3. Livrer dans un worktree du site (`C:\git\_wt-qcm`), `animations.mjs` + `retour-accueil.mjs` sur `qcm/` seulement
- [x] 4. Essai navigateur (ordinateur + téléphone), mesure : aucune requête vers le PC, aucun nom, filigrane
- [x] 5. Montrer à Franck (lien direct) ; trancher : carte sur l'accueil, indexation
- [x] 6. Feu vert → catalogue des stations + RAG HAL, `git fetch` + règle 4, push, contrôle en ligne
- [x] 7. fin-de-chantier, ligne du § 4 de FINITIONS-INERWEB.md
