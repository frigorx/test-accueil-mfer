# Chantier — le profil par famille, puis la mémoire dans le temps

> Cadré le 22/09/2026 au matin, **à faire dans un chat dédié le soir même**. Franck : « on le fait ce
> soir tranquillement dans la nuit, avec un nouveau chat ». Aucune séance derrière : on peut casser,
> mesurer, recommencer. Ce fichier existe pour démarrer à pied d'œuvre, pas pour tout re-découvrir.

## Pourquoi

Le positionnement donne aujourd'hui **un chiffre** : le niveau atteint, et une note sur 20. C'est la bonne
réponse à « où en est cet élève ? ». Ce n'est pas la bonne réponse à **« qu'est-ce qui va le faire échouer à
l'attestation d'aptitude ? »** — parce que l'attestation s'évalue **par domaines** : un candidat excellent en
compresseurs et faible en étanchéité échoue, et sa moyenne ne le sauve pas.

Et parce que chaque passage repart de zéro, un pic atteint retombe au passage suivant : rien ne se construit
sur l'année. Or l'objectif de Franck est justement d'amener ses 1re Bac Pro à l'habilitation en fin de
terminale, et ses CAP à l'échéance qu'ils rencontreront dans le privé.

## Lot 1 — le profil par famille (≈ 40 min, risque faible)

Les **53 thèmes** de `banque.json` se regroupent en **8 familles**. Table établie et **vérifiée le 22/09 :
53 thèmes sur 53 placés, 196 questions réparties**, aucun orphelin.

| Famille | Questions | Thèmes regroupés |
|---|---|---|
| Le circuit frigorifique | 44 | les quatre organes, le cycle, compresseur, condenseur, évaporateur, détendeur, ligne liquide, surchauffe et sous-refroidissement, régulation du froid (deux orthographes), pump-down |
| Électricité et habilitation | 37 | circuit de puissance, circuit de commande, repérage des bornes, symboles électriques, habilitation électrique, zones électriques, contacts NO et NF, schéma électrique, VAT |
| Réglementation et environnement | 31 | catégories d'attestation, PRP et équivalent CO2, réglementation F-Gas, réglementation avancée, CERFA et registre, classes de sécurité NF EN 378, récupération et bouteilles, manipulation et stockage |
| Sécurité et prévention | 24 | règles de la classe, règlement du lycée, sécurité à l'atelier, gestes qui sauvent, gestes de secours, risques et EPI, les EPI, EPI électriques, consignation |
| Mesures et diagnostic | 19 | pression et température, multimètre, raisonnement de diagnostic, reconnaître sur une machine, plaque signalétique, calcul de mise en service |
| Tuyauterie et brasage | 19 | cuivre et cintrage, brasage fort, azote et épreuve d'étanchéité |
| Intervention et étanchéité | 13 | tirage au vide, charger un circuit, mise en service, seuils de contrôle d'étanchéité |
| Communication et gestion | 9 | chiffrer une intervention, rendre compte et conseiller, ordre de travail |

⚠️ **Deux pièges relevés en établissant la table** : le thème s'écrit `PRP et équivalent CO2` (chiffre 2, pas
l'indice ₂), et `La régulation du froid` / `Régulation du froid` coexistent — deux orthographes du même thème,
à garder toutes les deux dans la table tant que la banque n'est pas nettoyée.

**À faire :** poser la table dans `construire-banque.py` (elle devient un champ `famille` sur chaque question),
puis afficher le profil — un tableau de plus sur l'écran de fin de `positionnement.html`, à côté de la carte des
compétences, et la même chose dans `/bilan` côté professeur.

**Critère de réussite :** sur un parcours simulé, le tableau des familles sort juste (somme = nombre de questions
répondues), et le bilan du professeur l'affiche élève par élève.

**Décision déjà prise, à ne pas remettre en cause :** un profil faible sur une famille **ne bloque rien**.
On affiche les sommets atteints, on ne ferme aucune porte. Un élève de CAP bloqué décroche ; le déblocage est
une récompense visible, jamais une serrure.

## Lot 2 — la mémoire dans le temps (≈ 50 min, risque moyen)

Aujourd'hui `preparer()` tire au hasard (graine = nom + classe), identique à chaque passage. Il faut qu'une
question ratée revienne vite et souvent, et qu'une question sue s'espace.

**V1 réaliste pour une soirée :** au démarrage, la page demande au serveur ce que l'élève avait raté
(`GET /historique?nom=…`, le serveur lit `resultats/test-accueil.jsonl` et renvoie les `id` ratés) ; `preparer()`
place ces questions en tête du tirage de leur niveau. Rien de plus.

**Ce qui n'est PAS promis pour ce soir :** la pondération fine (espacement progressif d'une question sue,
montée automatique du niveau sur l'année). C'est un vrai modèle de répétition espacée, pas une heure de travail.

**Critère de réussite :** deux passages simulés du même élève ; au second, les questions ratées au premier
reviennent en priorité.

**Point de vigilance :** `preparer()` est le cœur du test. Commiter le lot 1 **avant** d'y toucher, pour que
l'outil reste utilisable si le lot 2 dérape.

## Ce qui existe déjà — ne rien réécrire

**Banque du positionnement** (`C:\git\test-accueil-mfer`) : 196 questions, champs `id, niveau, theme, q, r, e,
mfer, cap, tax, source, svg`. Six niveaux (12 / 30 / 42 / 52 / 35 / 25), un code de compétence MFER **et** un code
CAP sur chacune, taxonomie (102 / 70 / 24). Sert à **situer un élève dans son cursus**.

**Banque de l'habilitation** (`C:\git\inerweb-habilitation\contenus\banque-entrainement.json`) : **266 questions**
rangées en **14 chapitres du référentiel officiel de l'attestation** (législation et thermodynamique 46,
compresseurs 28, récupération 27, détendeurs 25, hydrocarbures A1/A2 21, évaporateurs 20, réglementations 19,
condenseurs 16, CO₂/R-744 16, contrôles d'étanchéité 15, technologies de substitution 15, mise en service 8,
tuyauterie 7). **Les 266 pointent vers leur chapitre de remédiation**, 251 vers des ressources. Plus 89 questions
d'examen dans `questions-habilitation.json`. Sert à **entraîner à un examen**.

🔴 **Ne pas fusionner ces deux banques.** Buts différents, granularités différentes : les mélanger affaiblirait
les deux. Un pont entre elles, oui ; une seule banque, non.

## Fait le 22/09 au matin, déjà en place

- **Niveau de départ par classe** (`const DEPART`, `positionnement.html`) : TNE 0, CAP 0, 1re MFER 1,
  Terminale MFER 2. La frise **barre** les niveaux non demandés à la classe. Les niveaux non abordés sont
  exclus du calcul de la note — `terminer()` fait `if (!repondu) return;`, donc la note reste juste.
  ⚠️ Conséquence assumée : **les notes ne sont plus comparables d'une classe à l'autre**.
- **Pas de plafond**, et c'est délibéré : le test monte par paliers et chaque niveau se mérite à 50 % de
  réussite. Personne ne reçoit une question au-dessus de ce qu'il a validé — le plafond était une fausse
  bonne idée, écartée après vérification du code.
- **Défaut corrigé** : `construire-banque.py` cherchait la première balise `<svg>` de `symboles.svg`, or la
  première occurrence est dans le texte du commentaire d'en-tête. Le mode d'emploi était recopié dans la page
  et **s'affichait devant l'élève**. Les commentaires sont retirés avant la recherche.
