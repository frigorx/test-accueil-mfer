# Chantier — « Accueil sécurité apprenant » (MPI · Étancheur · TP CVC)

> Cadré le 22/09/2026 au soir. **Écrit et vérifié le 22/09/2026 au soir** : 40 questions, page
> `apprentis/`, contrôle à 0 défaut. Ce fichier dit ce qui existe, ce qui a été tranché, et ce qui
> reste à décider par F. Henninot.

## Ce qui existe maintenant

| Fichier | Ce que c'est |
|---|---|
| `apprentis/questions.json` | **40 questions**, six thèmes, codées CAP MPI et CAP Étancheur, chacune avec sa source |
| `apprentis/index.html` | La page de l'apprenti : même charte et même mécanique que le test d'accueil des élèves |
| `controler-apprentis.py` | Le contrôle : forme, longueurs, codes, doublons, **et le biais de longueur** |
| `serveur-test-accueil.py` | Une ligne ajoutée : l'activité n° 5 de l'accueil des téléphones, `/apprentis/` |

`PYTHONIOENCODING=utf-8 python controler-apprentis.py` → **40 questions, 0 défaut.**
Parcours vérifié au navigateur le 22/09 : départ, questions mélangées, explication, résultat,
compétences codées, code de validation, case d'engagement.

### Les six thèmes

| # | Thème | Questions |
|---|---|---|
| 0 | Les règles du lycée valent aussi pour moi | 9 |
| 1 | Mon comportement en entreprise | 7 |
| 2 | Mes équipements de protection | 6 |
| 3 | Le travail en hauteur | 7 |
| 4 | Ce que j'engage : ma responsabilité | 5 |
| 5 | S'il arrive un accident | 6 |

## Ce qui a été tranché (et pourquoi)

- **Une seule banque**, pas trois. Chaque question porte son code MPI *et* son code Étancheur.
  Aucune question n'est propre à une filière : un accueil sécurité est le même pour les trois.
  Le champ `filiere` du cadrage n'a donc pas été créé — il n'aurait rien porté.
- **Le nom retenu** : « Accueil sécurité apprenant ».
- **Le travail en hauteur n'a pas été réécrit** : les sept questions viennent du QCM existant
  (`C:\git\qcm-travail-hauteur`, questions 8, 11, 13, 15, 17, 22, 25), du référentiel R408 du RAG
  (items 2.4, 3.4, écrans « protection collective », « harnais, longe, point d'ancrage ») et des
  articles D4153-30 et D4153-31 pour les moins de 18 ans. Chaque question cite laquelle.
- **Durée 45 minutes**, mêmes règles que le test d'accueil : sorties de page comptées (−1 point,
  arrêt à 5), écran maintenu allumé, code de validation, capture d'écran comme preuve.

## 🔴 Trois points qui appellent une décision

### 1. Le TP CVC n'a pas de code de compétence à porter

Le REAC du titre (arrêté du 15/12/2022) ne code que des compétences de **bureau d'études**
(CP1 à CP10 : plans, calculs, études). Aucune ne porte la sécurité. Les questions ne peuvent donc
pas lui être rattachées sans inventer un code. La page le dit à l'apprenti CVC — son résultat se
lit par thème et par niveau — et le contrôle n'en réclame pas. **À trancher** : garder le TP CVC
dans cette banque, ou lui faire un accueil à part.

### 2. La banque du positionnement porte encore le biais que les élèves ont trouvé

Le contrôle du 22/09 refuse une bonne réponse *nettement* plus longue (plus d'un quart, plus de
8 caractères). Il ne voit pas le biais d'ensemble : **sur les 196 questions du positionnement, la
bonne réponse est strictement la plus longue dans 133 cas, soit 68 %** — le hasard en donnerait 33 %.
Les écarts sont petits (+3,6 caractères en moyenne), donc chaque question passe le contrôle une par
une ; mais cocher la plus longue sans lire rapporte encore 68 %.

`controler-apprentis.py` ajoute ce contrôle d'ensemble (défaut au-delà de 45 %). La banque
apprenant est à **32 %, écart moyen −1,5 caractère**. **À trancher** : porter le même contrôle dans
`construire-banque.py` et rééquilibrer les 196 questions du positionnement (c'est du travail de
réécriture, pas un réglage).

### 3. Un fait écarté faute de source vérifiée

La durée maximale de travail d'un apprenti mineur (8 h par jour, 35 h par semaine, avec dérogation
possible dans le bâtiment) n'a **pas** été posée en question : la vérification en ligne n'a pas
confirmé l'article. À ajouter si la source est retrouvée — le fait est utile à un apprenti.

## D'où viennent les questions

- **Règles du lycée** : règlement intérieur et test d'accueil des élèves (`index.html`), dont les
  questions sont déjà validées en classe. Le doublon avec le test des élèves est voulu : un apprenti
  croit souvent que ces règles ne le concernent pas.
- **Entreprise, EPI** : Code du travail, art. R4321-4 et R4323-95 (l'employeur fournit gratuitement,
  entretient, remplace), R4228-20 et R4228-21 (alcool), L4121-2 (protection collective d'abord),
  L4122-1, R4153-40 (encadrement du jeune).
- **Hauteur** : voir plus haut.
- **Responsabilité** : Code civil, art. 1240 et 1242 (« les artisans [répondent] du dommage causé par
  leurs élèves et apprentis pendant le temps qu'ils sont sous leur surveillance ») ; Code des
  assurances, art. L113-1 (la faute intentionnelle n'est pas assurée) et L124-1.
- **Accident** : 24 h pour informer l'employeur, 48 h pour sa déclaration à la CPAM (dimanches et
  jours fériés non comptés), feuille d'accident S6201 (soins sans avance de frais), et un accident
  survenu **au CFA** est un accident du travail — l'apprenti est couvert dès le premier jour
  (service-public.gouv.fr, ameli.fr).

## Ce qui n'est pas fait

- **Le bilan du professeur ne distingue pas encore les apprentis.** Les résultats partent sur la même
  route `/resultat` que ceux des élèves, avec `type: 'apprenti'` dans le suivi. Ils se mélangent au
  bilan du jour. À séparer si la séance d'accueil des apprentis se tient hors d'un cours de classe.
- **La liste des noms** (`choisir-son-nom.js`) prend la classe réglée dans le poste de commande. Pour
  un groupe d'apprentis, il faut y coller leur liste avant la séance, sinon la saisie reste libre.
- Aucun essai sur un téléphone réel : même réserve que pour le reste du dépôt (voir `REPRISE.md`).

## Le rappel qui vaut pour tout ce dispositif

Une trace horodatée — résultat, code de validation, case d'engagement — **établit que l'information
a été reçue, et quand**. Elle ne vaut pas signature. C'est le même avertissement que pour
`resultats/engagements.jsonl` du test d'accueil.
