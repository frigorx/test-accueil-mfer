# Les trois QCM « Accueil sécurité apprenant »

> Cadré le 22/09/2026, écrit et découpé en **trois QCM** le 22/09 au soir.
> À tester le vendredi 25/09.

## Trois QCM, un par formation

L'apprenti clique sur **son** bouton à l'accueil des téléphones et entre directement dans son QCM.
Il ne choisit rien à l'intérieur de la page : il n'a qu'un seul parcours.

| Formation | Lien | Questions |
|---|---|---|
| CAP Métiers du plâtre et de l'isolation | `/apprentis/?f=mpi` | 36 |
| CAP Étancheur du bâtiment | `/apprentis/?f=etancheur` | 36 |
| Titre pro Technicien d'études CVC | `/apprentis/?f=cvc` | 36 |

Sans formation dans l'adresse, `/apprentis/` montre les trois portes — filet de sécurité si un
apprenti arrive par l'adresse nue.

## Les fichiers

| Fichier | Ce que c'est |
|---|---|
| `apprentis/commun.json` | **28 questions** communes aux trois : règles du lycée, entreprise, EPI, hauteur, responsabilité, accident |
| `apprentis/mpi.json` | 8 questions métier : poussières et silice, plaques, cutter, plateforme, laine, carter, tri du plâtre |
| `apprentis/etancheur.json` | 8 questions métier : permis de feu, extincteur, bouteilles à 10 m, accès, bitume, bord de terrasse |
| `apprentis/cvc.json` | 8 questions métier : accueil chantier, EPI de visiteur, terrasse, coffret ouvert, engin, écran, plans du client |
| `apprentis/index.html` | Le moteur des trois QCM |
| `controler-apprentis.py` | Le contrôle des quatre fichiers **et** des trois QCM assemblés |

Le tronc commun est écrit **une seule fois** : une correction s'y fait à un seul endroit et vaut pour
les trois QCM. C'est la seule chose qui soit mise en commun — chaque apprenti, lui, ne voit que le sien.

### Les six thèmes

0. Les règles du lycée valent aussi pour moi (6) · 1. En entreprise, avec mon tuteur (5) ·
2. Mes équipements de protection (4) · 3. Le travail en hauteur (5) ·
4. **Les risques de mon métier** (8, propre à la formation) · 5. Ma responsabilité et l'accident (8).

## Le contrôle

`PYTHONIOENCODING=utf-8 python controler-apprentis.py` → **0 défaut**, et pour chacun des trois QCM :

| QCM | Bonne réponse la plus longue | Bonne réponse la plus courte |
|---|---|---|
| MPI | 25 % | 17 % |
| Étancheur | 31 % | 6 % |
| CVC | 28 % | 14 % |

Le hasard donne 33 %. **Aucune stratégie de longueur ne paie plus que de répondre au hasard** :
c'était le défaut relevé par les élèves le 22/09, il est fermé.

Parcours vérifiés au navigateur le 22/09 pour les trois QCM : départ direct, questions mélangées,
explication, résultat, compétences codées (MPI et Étancheur), code de validation, engagement.

## Ce qui a changé après la remarque sur la logique des questions

Les questions d'un accueil sécurité racontent un moment réel. Celles qui supposaient un état
impossible ont été retirées ou réécrites :

- **Supprimé** : « Pour entrer à l'atelier, il me faut ma tenue et mes chaussures ». On entre à
  l'atelier **pour** se changer — le vestiaire y est. On n'y arrive pas déjà habillé.
- **Supprimé** : « Ma caisse à outils, à l'arrivée ». Même raison : à l'arrivée, on n'a pas encore
  sa caisse, et on n'est pas encore en tenue.
- **Ajouté à la place** : l'évacuation incendie, vraie en salle comme à l'atelier, et qui est de la
  sécurité d'établissement au sens strict.
- Chaque question du tronc commun **situe son moment** : « Je sais que je vais arriver en retard »,
  « L'échafaudage était déjà monté hier. Ce matin », « Je me coupe un doigt sur le chantier ».

### 🔴 Le même défaut est resté dans le test d'accueil des élèves

`index.html` porte encore les deux questions ci-dessus, bloc « Les règles de la classe » :
« Pour entrer à l'atelier, il me faut… » et « Ma caisse à outils, à l'arrivée… ». Elles supposent un
élève déjà en tenue, sa caisse à la main, avant d'être entré. **Non corrigées** : ce test tourne déjà
avec les classes, la correction se décide. Proposition : « Une fois en tenue, ma caisse à outils… » et
« J'arrive à l'atelier. Avant de travailler, je passe au vestiaire quand le professeur le dit ».

## Les points ouverts

1. **Le QCM CVC ne porte aucun code de compétence.** Le REAC du titre (arrêté du 15/12/2022) code
   dix compétences de bureau d'études — plans, calculs, études — et aucune de sécurité. La page le
   dit à l'apprenti : son résultat se lit par thème et par niveau. Le contrôle n'en réclame pas.
2. **La banque du positionnement porte encore le biais de longueur.** Sur ses 196 questions, la
   bonne réponse est strictement la plus longue dans **133 cas (68 %)**. Les écarts sont petits, donc
   chaque question passe le contrôle une par une — c'est l'ensemble qui trahit. Le contrôle
   d'ensemble existe maintenant dans `controler-apprentis.py` ; le porter dans
   `construire-banque.py` demande ensuite de rééquilibrer les 196 questions.
3. **Un fait écarté faute de source vérifiée** : la durée maximale de travail d'un apprenti mineur
   (8 h par jour, 35 h par semaine, dérogation possible dans le bâtiment). La vérification en ligne
   n'a pas confirmé l'article — la question n'est pas posée.
4. **Le bilan du professeur ne sépare pas les apprentis des élèves.** Les résultats partent sur la
   même route `/resultat`, avec `type: 'apprenti'` dans le suivi.
5. **La liste des noms** (`choisir-son-nom.js`) prend la classe réglée dans le poste de commande.
   Sans liste correspondant au groupe d'apprentis, la saisie reste libre.

## D'où viennent les questions

- **Règles du lycée** : règlement intérieur, consignes d'évacuation.
- **Entreprise, EPI** : Code du travail, art. R4321-4 et R4323-95 (l'employeur fournit gratuitement,
  entretient, remplace), R4228-20 et R4228-21 (alcool), L4121-2 (protection collective d'abord),
  R4153-40 (encadrement du jeune).
- **Hauteur** — rien n'a été réécrit : QCM existant `C:\git\qcm-travail-hauteur` (questions 10, 13, 17),
  référentiel R408 du RAG (item 3.4 vérification journalière, « protection collective et harnais »),
  articles D4153-30 et D4153-31 pour les moins de 18 ans, dérogation R4153-38.
- **Plâtre et isolation** : INRS (silice cristalline), Prévention BTP (ponçage avant peinture),
  Code du travail R4541-1 et suivants (manutention), R4322-1 (équipements maintenus conformes),
  filière REP PMCB pour le tri du plâtre.
- **Étanchéité** : INRS ED 6030 (permis de feu), Prévention BTP « Réaliser les travaux d'étanchéité
  sur toits-terrasses en toute sécurité » — extincteur poudre ABC par poste chaud, 10 m entre
  bouteilles et matériaux inflammables, accès dégagés, gants à manchettes, bitume nettoyé à la crème
  lavante et jamais au solvant.
- **CVC** : Code du travail R4511-1 et suivants (entreprise extérieure), R4542-3 et R4542-4 (travail
  sur écran), R4534-1 et suivants (chantiers), NF C 18-510 pour le coffret ouvert.
- **Responsabilité** : Code civil art. 1240 et 1242 ; Code des assurances art. L113-1 et L124-1.
- **Accident** : 24 h pour informer l'employeur, 48 h pour sa déclaration à la CPAM (dimanches et
  jours fériés non comptés), feuille d'accident S6201, et un accident au CFA est un accident du
  travail — l'apprenti est couvert dès le premier jour (service-public.gouv.fr, ameli.fr).

## Le rappel qui vaut pour tout ce dispositif

Une trace horodatée — résultat, code de validation, case d'engagement — **établit que l'information
a été reçue, et quand**. Elle ne vaut pas signature. Même avertissement que pour
`resultats/engagements.jsonl` du test d'accueil.
