# Brief — écrire la banque de questions du quiz de positionnement

Vous écrivez des questions pour un quiz sur téléphone, destiné à des élèves de CAP et de Bac Pro froid et
climatisation, dont beaucoup lisent difficilement le français. Le quiz n'est pas noté : il dit à quel
niveau l'élève se situe et quelles compétences il maîtrise.

## 1. Le fichier à produire

Un fichier JSON par niveau : `banque/niveau-N.json`, un tableau d'objets :

```json
{
  "id": "N1-001",
  "niveau": 1,
  "theme": "Les organes",
  "q": "Quel organe fait chuter la pression du fluide ?",
  "r": ["le détendeur", "le compresseur", "le condenseur"],
  "e": "Le détendeur fait passer le fluide de la haute à la basse pression.",
  "mfer": "C2",
  "cap": "C1.1",
  "tax": 1,
  "svg": "detendeur_thermo_ext",
  "source": "Cours-de-theorie/T01, partie 2"
}
```

- `r` : **3 réponses** (4 admises si la source en a 4), **la bonne toujours en premier** ; la page les mélange.
- `e` : l'explication lue après la réponse. **25 mots au plus.** Une phrase, pas de jargon inutile.
- `q` : **20 mots au plus**, une seule idée, pas de double négation, unités écrites (bar, °C, K, kg).
- `tax` : 1 « je sais » (une connaissance), 2 « je comprends » (un lien de cause à effet), 3 « je fais le bon
  geste » (une situation, une décision).
- `mfer` : une compétence du Bac Pro MFER · `cap` : une compétence du CAP IFCA (listes § 3). Une seule chacune.
- `svg` (facultatif) : un identifiant de la palette (§ 4) affiché avec la question — pour les questions du type
  « quel est cet organe ? », « à quoi sert-il ? ». Jamais de symbole redessiné, jamais d'image.
- `source` : le fichier et l'endroit d'où vient la question. **Obligatoire.**
- `d` (facultatif) : `"MFER"` ou `"CAP"` si la question ne vaut que pour une classe.
- Pas de `"toutes les réponses"`, pas de `"aucune"`, pas de piège de formulation.

## 2. Les règles qui ne se négocient pas

1. **Rien d'inventé.** Une valeur, un seuil, une règle, un nom viennent d'une source citée. Si la source ne
   le dit pas, la question ne se pose pas. Les sources sont listées dans `_PLAN-QUIZ-POSITIONNEMENT.md`.
2. **Français simple.** Élèves allophones : mots courants, phrases courtes, un fait par question.
3. **Une bonne réponse, nette.** Les deux autres sont fausses sans ambiguïté, mais plausibles (pas d'absurdité).
4. **Pas de doublon** entre niveaux : chaque fait n'est posé qu'une fois dans toute la banque. Lire les
   fichiers de niveau déjà écrits avant d'ajouter.
5. **Le niveau, c'est la difficulté réelle** : N1 bases (nommer, situer, rôle) · N2 mesurer et agir (lire un
   manomètre, calculer une surchauffe, manifold, azote, vide, charge) · N3 électricité et régulation
   (contacteur, relais, pressostats, pump-down, schéma, habilitation B1V) · N4 habilitation fluide (F-Gas,
   PRP, catégories 2025, CERFA, étanchéité, récupération, sécurité des fluides) · N5 expert (diagnostic,
   régulation électronique, calculs, chiffrage, rendre compte, réglementation avancée).
6. **Quelques faits du dossier à respecter** : la surchauffe attendue est de 5 à 8 K et le sous-refroidissement
   de 4 à 7 K ; le CO₂ est en catégorie B (pas D) et l'ammoniac en C ; la catégorie I devient A1 au
   01/01/2027 ; le R290 est A3 ; le PRP d'un mélange est celui de la règle « le plus élevé » telle que la
   source la donne ; une bouteille d'azote se branche toujours par un détendeur et jamais d'oxygène.
7. **Contrôle avant de rendre** : `PYTHONIOENCODING=utf-8 python construire-banque.py --controle banque/niveau-N.json`
   doit dire « 0 défaut ». Corriger et relancer tant que ce n'est pas le cas.

## 3. Les codes

**Bac Pro MFER** : C1 analyser les conditions de l'opération et son contexte · C2 analyser et exploiter les
données techniques · C3 choisir les matériels, équipements et outillage · C4 organiser et sécuriser son
intervention · C5 réceptionner les approvisionnements · C6 réaliser une installation en adoptant une attitude
écoresponsable · C7 mettre en service · C8 contrôler, régler et paramétrer · C9 maintenance préventive ·
C10 maintenance corrective · C11 consigner et transmettre · C12 communiquer, rendre compte · C13 conseiller
le client.

**CAP IFCA** : C1.1 compléter, transmettre · C1.2 communiquer avec les acteurs · C1.3 rendre compte ·
C2.1 organiser des informations · C2.2 contrôler les éléments nécessaires · C2.3 préparer les conditions
d'intervention · C2.4 sécuriser l'intervention · C3.1 organiser le poste · C3.2 identifier les réseaux
d'alimentation · C3.3 implanter, manutentionner, fixer · C3.4 façonner, raccorder, assembler, isoler les
circuits · C3.5 soudage acier, PER · C3.6 câbler, repérer, connecter · C3.7 contrôler la mise en œuvre ·
C3.8 trier, valoriser les déchets · C3.9 vérifier l'étanchéité avant mise en service · C4.1 tirer au vide ·
C4.2 manipuler le fluide et les huiles · C4.3 contrôler l'étanchéité d'un circuit chargé · C4.4 intervenir
sur un circuit hydraulique ou aéraulique · C4.5 mesurer, comparer des grandeurs · C4.6 paramétrer, régler
les consignes · C4.7 raccorder les équipements de charge, de mesure et de contrôle.

## 4. Les symboles disponibles (`svg`)

Frigorifiques : compresseur_general, compresseur_piston, compresseur_scroll, echangeur_a_air,
condenseur_evaporatif, echangeur_a_plaques, detendeur_thermo_ext, detendeur_thermo_int,
detendeur_electronique, tube_capillaire, bouteille_liquide, filtre_deshydrateur, voyant_liquide,
separateur_huile, distributeur_liquide, vanne_isolement, vanne_securite, electrovanne_frigo,
clapet_anti_retour, ventilateur_axial, ventilateur_centrifuge, resistance_evaporation, manometres,
pressostat, pressostat_bp, pressostat_hp, pressostat_nf, sonde_temperature, thermostat, thermostat_froid.
Électriques : source_3p_n, source_phase_l, source_neutre_n, terre, sectionneur_3_fusibles, sectionneur_3p,
disjoncteur_3p, disjoncteur_1p, disjoncteur_magneto_therm_3p, disjoncteur_moteur_gv2, relais_thermique,
contact_gv_no, contact_gv_nf, fusible_3p, bp_no_marche, bp_nf_arret, arret_urgence, contact_no_13_14,
contact_nf_11_12, contact_puissance_3p_no, bobine_contacteur, bobine_tempo_travail, moteur_triphase,
resistance_chauffante, voyant_lumineux, voyant_rouge, voyant_vert.

## 5. Volumes attendus

N0 : 12 (choisies dans le test d'accueil, telles quelles) · N1 : 30 · N2 : 30 · N3 : 30 · N4 : 35 · N5 : 25.
Numérotation continue par niveau : `N1-001`, `N1-002`…

## 6. Ce que vous rendez

Le ou les fichiers JSON, la sortie du contrôle, et dix lignes : sources réellement lues (chemins), ce qui a
été laissé de côté et pourquoi, les faits sur lesquels deux sources se contredisaient.
