# Plan — le grand quiz de positionnement (ouvert le 10/09/2026 au soir)

**Ce que Franck a demandé (dicté)** : « ce super méga quiz, niveau CAP, niveau Bac Pro, avec possibilité de
récupérer les notes par email ou WhatsApp, avec les compétences de non acquis à parfaitement maîtrisé.
Habilitation fluide, la totale. On part du niveau 0 au niveau maxi. Un niveau qui correspond à la 2nde TNE,
un niveau CAP 2 à peu près pareil, et un niveau Terminale Bac Pro où on envoie du lourd, habilitation
fluide. Le test d'intégration. Ça permet aussi une cartographie des élèves : exporter un CSV complet pour
faire la cartographie des points forts, points faibles, attention aux attendus. »

## Interprétations retenues

- **Un positionnement, pas une note** : on monte les niveaux tant que l'élève tient (au moins la moitié de
  bonnes réponses au niveau), on s'arrête sinon. Le résultat dit **le niveau atteint** et la carte des
  compétences ; la note sur 20 est calculée mais secondaire.
- **Six niveaux** : N0 accueil et sécurité (le test d'accueil, réduit) · N1 les bases (2nde TNE, CAP 1re
  année, entrée en 1re MFER) · N2 mesurer et agir (CAP 2e année, 1re MFER) · N3 électricité et régulation ·
  N4 habilitation fluide (Terminale, attestation A1) · N5 expert (sortie de Terminale, entrée BTS).
- **Quatre classes au départ** : CAP IFCA, 1re Bac Pro MFER, Terminale Bac Pro MFER, 2de TNE (« j'ai oublié
  la TNE »). Les compétences sont celles du référentiel de la classe (CAP IFCA C1.1 → C4.7 ; Bac Pro MFER
  C1 → C13 ; 2de TNE : compétences communes CC obtenues par correspondance depuis les codes Bac Pro),
  chaque question portant un code pour chacun des deux référentiels.
- **Échelle des compétences** : moins de 40 % de justes = non acquis · 40 à 64 % = en cours · 65 à 84 % =
  acquis · 85 % et plus = parfaitement maîtrisé · aucune question = non évalué.
- **Rien d'inventé** : toute question vient d'une source de Franck ou du dossier, et la cite.
- **Français simple** (élèves allophones) : une idée par phrase, réponses courtes, explication courte, le
  bouton de lecture à voix haute.
- **Récupération** : capture d'écran (cadre unique), envoi WhatsApp (`wa.me`) et courriel une fois le
  numéro et l'adresse renseignés, serveur local sur le PC (`serveur-test-accueil.py`, tableau vivant,
  CSV, **cartographie élèves × compétences**).
- Les symboles viennent de la palette du dossier (`symboles.svg`, copie de `symboles-mfer.svg`), jamais
  redessinés.

Réglage : Fable en cadrage, moteur et vérification ; trois rédacteurs Sonnet (effort moyen) pour la banque.

## Sources, par niveau

| Niveau | Sources (lues, pas seulement titrées) |
|---|---|
| N0 | `progression-1re-mfer/00-dossier/Test-numerique-accueil-securite-et-regles.html` (41 questions, en prendre 12) |
| N1 | `Interros/Interros-P1-01-a-05-{ELEVE,PROFESSEUR}.html`, `Interros/Evaluation-P1-*`, `Interros/Interro-01-grand-format-*-PROFESSEUR.html`, `Cours-de-theorie/T01`, `T02`, `T07` |
| N2 | `Interros/Interros-P3-08-a-13-*`, `Interros/Evaluation-P3-*`, `T03`, `T04`, `T05`, `T10`, `T14`, `T18`, `T19`, `Interros/Exercice-Vendredi-Lecture-manometre-*`, `Documents/P1/12-tp-r1-mise-en-service/*RESSOURCE*` |
| N3 | `Interros/Interros-P4-14-a-18-*`, `Interros/Evaluation-P4-*`, `T15`, `T16`, `T17`, `T20`, `Documents/P1/14-tp-r3-cabler-le-pump-down/*` |
| N4 | `C:\git\fgas-eval-habilitation\data\questions-habilitation.json` (85 questions taguées), `Interros/Evaluation-P5-attestation-A1-*`, `T13`, `T21`, `3-PROF-PEDAGO\caude tp\quiz-fgas-securite-complet.html` (20 questions) |
| N5 | `Interros/Evaluation-P6-examen-blanc-E2-*`, `Interros/Interros-P5-et-P6-*`, `T06`, `T08`, `T22`, chapitres 09 à 14 de `questions-habilitation.json` |

## Étapes

| # | Étape | État |
|---|---|---|
| 1 | Plan, brief des rédacteurs, schéma de la banque, vérificateur `construire-banque.py` | ✅ |
| 2 | Trois rédacteurs Sonnet : N0+N1+N2 · N3 · N4+N5 → `banque/niveau-N.json` | ✅ 10/09 (0 défaut chacun) |
| 3 | Moteur `positionnement.html` (niveaux adaptatifs, symboles, compétences 0-4, exports) | ✅ |
| 4 | Fusion et contrôle de la banque, `banque.json` | ✅ 172 questions |
| 5 | Serveur local : `/cartographie` et `/cartographie.csv` | ✅ |
| 6 | Essais dans le navigateur (CAP, MFER, arrêt de niveau, exports), publication GitHub Pages | ✅ 10/09 soir |
| 7 | Journal, mémoire, relais | ✅ |

## Résultat (10/09 au soir)

**La banque** : 172 questions — N0 12 · N1 30 · N2 30 · N3 40 · N4 35 · N5 25 ; taxonomie « je sais » 89,
« je comprends » 61, « je fais le bon geste » 22 ; 37 questions portent un symbole de la palette ; aucune
question restreinte à un diplôme. Un élève tire 15 questions par niveau (les 12 du N0) : **87 questions au
plus** pour celui qui va jusqu'au niveau 5, une trentaine pour celui qui s'arrête au niveau 1.

**Les essais** (par script, serveur local) : CAP « tout juste » → N5 atteint, 87/87, dix-sept compétences CAP
à « parfaitement maîtrisé », 19 symboles vus ; MFER qui échoue au N1 → arrêt, niveau atteint N0, 12/27 ;
2de TNE mixte (N4 à moitié juste, N5 faux) → N4 atteint, 65/87, carte en codes CC (CC11 → CC82). Côté PC :
`/resultats` (avec le bloc « En ce moment »), `/resultats.csv`, `/cartographie`, `/cartographie.csv` justes.

**Relevé par les rédacteurs, à trancher par Franck** (aucune question n'a été écrite sur ces points) :
1. `TP-R1-Mise-en-service-RESSOURCE` attribue au cours T05 les fourchettes « surchauffe 5-8 K,
   sous-refroidissement 4-7 K » ; T05 ne donne aucun chiffre et renvoie au constructeur.
2. Température de refoulement : 70 °C dans le corrigé des interros P1 (n° 1), 90 °C dans le cours T02.
3. Identifier les organes sur un schéma : compétence C1 dans l'Évaluation P1, C2 dans l'interro grand format.
4. « Purger le manifold » n'a pas de source au N2 ; la classification A2L/A3 est laissée au N4 (habilitation).
