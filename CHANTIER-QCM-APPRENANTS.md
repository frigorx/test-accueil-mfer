# Chantier — « Accueil sécurité apprenant » (MPI · Étancheur · TP CVC)

> Cadré le 22/09/2026 au soir, à la demande de F. Henninot. **Rien n'est écrit pour l'instant** :
> ce fichier existe pour qu'une session neuve parte de l'existant et non de zéro.

## Ce que c'est

Le même esprit que le test d'accueil des élèves, mais pour des **apprentis**, et avec la partie
métier remplacée par du générique entreprise. Trois filières :

| Filière | Code dans le RAG | Ce que le RAG contient déjà |
|---|---|---|
| CAP Métiers du plâtre et de l'isolation | `CAP_MPI` | sujets d'examen EP1, EP2, EP3 (PDF) |
| CAP Étancheur du bâtiment | `CAP_ETANCH` | **compétences codées** : C1.2 Échanger et rendre compte oralement, C3.4 Utiliser des échafaudages, C3.6 Exécuter les travaux préparatoires, C3.8 Mettre en œuvre une étanchéité |
| Titre professionnel CVC | (voir `C:\git\tp-tecvc`) | dossier de TP existant |

**Interroger le RAG avant d'écrire** : `node C:/git/HAL-v3/scripts/chercher-rag.js "<sujet>"`.
C'est lui qui a fourni tout ce tableau.

## 🔴 Ne pas refaire : le travail en hauteur existe déjà

- **`C:\git\qcm-travail-hauteur`** — QCM autonome (`index.html`, `data.js`, `script.js`), ~27 questions,
  son PDF source `Le-travail-en-hauteur.pdf`, ses illustrations dans `assets/`. Dépôt GitHub `frigorx/qcm-travail-hauteur`.
- **Référentiel R408** dans le RAG : `res/habilitation/referentiel-r408-hauteur/…` (ex. « 4.2 — Utiliser un
  échafaudage de pied en sécurité »).
- Deux TP « Travail en hauteur » (un BAC MFER, un CAP IFCA) et la station **« En hauteur (Législation) »**,
  déjà en ligne sur inerweb.fr.

Le volet hauteur du QCM apprenant **reprend cette matière**, il ne la réécrit pas.

## Le fond commun à écrire

Ce qui remplace la partie « froid, spécifique atelier » du test des élèves :

1. **Les règles de vie du lycée s'appliquent aussi aux apprentis** — demande explicite de F. Henninot,
   « c'est ce qu'un apprenti croit souvent ne pas le concerner ». Plusieurs questions, pas une seule.
2. **Comportement responsable en entreprise** — horaires, tenue, téléphone, alcool, consignes du tuteur.
3. **Le port des EPI** — lesquels, quand, qui les fournit, que faire s'ils manquent.
4. **Le travail en hauteur** — repris de l'existant ci-dessus.
5. **La responsabilité civile de l'apprenti** — ce qu'il engage, ce que couvre l'entreprise, ce que couvre
   l'établissement, à qui il déclare un dommage.
6. **Conduite à tenir en cas d'accident** — déclarer, à qui, dans quel délai, et pourquoi la trace compte.

> **L'objectif n'est pas seulement pédagogique** : F. Henninot le dit clairement, il s'agit aussi de
> **se protéger en cas d'accident** — pouvoir établir que l'apprenti a été informé, et quand. C'est la même
> logique que les engagements du test d'accueil (`resultats/engagements.jsonl`), et le même avertissement
> s'applique : une trace horodatée établit l'information reçue, elle ne vaut pas signature.

## Contraintes de rédaction — non négociables

- 🔴 **La bonne réponse ne doit pas être la plus longue.** Défaut relevé par les élèves le 22/09 : 73 % sur le
  test d'accueil, +17 caractères de moyenne. `construire-banque.py` refuse désormais ces questions.
  Une mauvaise réponse doit être **aussi crédible et aussi longue** que la bonne — c'est meilleur
  pédagogiquement, une fausse plausible en apprend davantage qu'une évidence.
- Question de 20 mots au plus, réponse de 12 mots au plus, explication de 25 mots au plus.
- Trois ou quatre réponses, jamais « toutes les réponses » ni « aucune ».
- Chaque question cite sa source et porte son code de compétence.
- Vocabulaire simple : pas de terme savant, niveau CAP, lecteurs FLE et DYS compris.

## À trancher avant d'écrire

- Une banque commune aux trois filières avec un champ `filiere`, ou trois banques distinctes ? (Le test
  d'accueil des élèves gère déjà deux diplômes dans un seul fichier, via un champ `d` — c'est le précédent.)
- Le nom retenu : **« Accueil sécurité apprenant »**.
