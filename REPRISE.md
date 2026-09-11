# Reprise — tests sur téléphone : test d'accueil, positionnement, « Test de rentrée »

**Dépôt** : `C:\git\test-accueil-mfer` · **public** sur GitHub (`frigorx/test-accueil-mfer`), pages en ligne :
https://frigorx.github.io/test-accueil-mfer/ (test d'accueil) et `…/positionnement.html` (positionnement).
**Ce fichier est le point d'entrée.** Mode d'emploi : `README.md` · plan, décisions et restes du positionnement :
`_PLAN-QUIZ-POSITIONNEMENT.md` · les modes de récupération des notes : `PROCEDURE-COLLECTE.md`.
**Dernière mise à jour : 11/09/2026.**

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
