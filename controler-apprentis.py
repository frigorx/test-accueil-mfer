# -*- coding: utf-8 -*-
"""
CONTRÔLER LA BANQUE « ACCUEIL SÉCURITÉ APPRENANT »
==================================================
Même exigence que construire-banque.py, mais sur apprentis/questions.json : forme, longueurs,
codes de compétence des deux CAP, doublons, et le biais de longueur de la bonne réponse.

USAGE   PYTHONIOENCODING=utf-8 python controler-apprentis.py
"""
import io, json, os, re, sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
ICI = os.path.dirname(os.path.abspath(__file__))
FICHIER = os.path.join(ICI, 'apprentis', 'questions.json')

# Arrêté du 15 avril 2019 (CAP MPI) et arrêté du 29 août 2022 (CAP Étancheur).
MPI = {'C1.1', 'C1.2', 'C2.1', 'C2.2', 'C2.3'} | {'C3.%d' % i for i in range(1, 17)}
ETANCH = {'C1.1', 'C1.2', 'C2.1', 'C2.2', 'C2.3'} | {'C3.%d' % i for i in range(1, 15)} | {'C4.1', 'C4.2', 'C4.3'}
# Le TP TECVC est un titre de bureau d'études : son REAC ne code aucune compétence de sécurité.
# Aucune question ne porte donc de code CVC — c'est un constat, pas un oubli.
BLOCS = ["Les règles du lycée valent aussi pour moi", "Mon comportement en entreprise",
         "Mes équipements de protection", "Le travail en hauteur",
         "Ce que j'engage : ma responsabilité", "S'il arrive un accident"]
CHAMPS = {'id', 'b', 'n', 'q', 'r', 'e', 'mpi', 'etanch', 'source'}


def mots(t):
    return len(re.findall(r"[\wÀ-ÿ'’-]+", t or ''))


def controler(qs):
    defauts, ids, textes = [], set(), set()
    for i, q in enumerate(qs):
        ou = '#%d (%s)' % (i + 1, q.get('id', '?'))
        inconnus = set(q) - CHAMPS
        if inconnus:
            defauts.append('%s : champs inconnus %s' % (ou, sorted(inconnus)))
        for k in CHAMPS:
            if k not in q:
                defauts.append('%s : champ manquant « %s »' % (ou, k))
        if q.get('id') in ids:
            defauts.append('%s : identifiant en double' % ou)
        ids.add(q.get('id'))
        if q.get('b') not in range(len(BLOCS)):
            defauts.append('%s : bloc hors 0-%d' % (ou, len(BLOCS) - 1))
        if q.get('n') not in (1, 2, 3):
            defauts.append('%s : n doit valoir 1, 2 ou 3' % ou)
        if mots(q.get('q')) > 20:
            defauts.append('%s : question de %d mots (20 au plus)' % (ou, mots(q.get('q'))))
        if mots(q.get('e')) > 25:
            defauts.append('%s : explication de %d mots (25 au plus)' % (ou, mots(q.get('e'))))
        r = q.get('r')
        if not isinstance(r, list) or not 3 <= len(r) <= 4 or any(not isinstance(x, str) or not x.strip() for x in r):
            defauts.append('%s : il faut 3 ou 4 réponses non vides' % ou)
        else:
            if len({x.strip().lower() for x in r}) != len(r):
                defauts.append('%s : deux réponses identiques' % ou)
            for x in r:
                if mots(x) > 12:
                    defauts.append('%s : réponse de %d mots (12 au plus) : « %s »' % (ou, mots(x), x[:40]))
                if re.search(r'toutes les r[ée]ponses|aucune de|aucune r[ée]ponse', x, re.I):
                    defauts.append('%s : réponse « toutes / aucune » interdite' % ou)
            # Même seuil que construire-banque.py : cocher la plus longue sans lire ne doit
            # rien rapporter. Une mauvaise réponse se rédige aussi soigneusement que la bonne.
            bonne, fausses = len(r[0]), [len(x) for x in r[1:]]
            if bonne > max(fausses) * 1.25 and bonne - max(fausses) > 8:
                defauts.append('%s : la bonne réponse est la plus longue (%d contre %d) — étoffer les fausses ou resserrer la bonne'
                               % (ou, bonne, max(fausses)))
            if bonne * 1.25 < min(fausses) and min(fausses) - bonne > 8:
                defauts.append('%s : la bonne réponse est nettement la plus courte (%d contre %d) — même biais, à l\'envers'
                               % (ou, bonne, min(fausses)))
        if q.get('mpi') not in MPI:
            defauts.append('%s : code CAP MPI inconnu « %s »' % (ou, q.get('mpi')))
        if q.get('etanch') not in ETANCH:
            defauts.append('%s : code CAP Étancheur inconnu « %s »' % (ou, q.get('etanch')))
        if not (q.get('source') or '').strip():
            defauts.append('%s : source vide' % ou)
        t = (q.get('q') or '').strip().lower()
        if t in textes:
            defauts.append('%s : question déjà posée : « %s »' % (ou, t[:60]))
        textes.add(t)
    return defauts


def main():
    if not os.path.exists(FICHIER):
        print('apprentis/questions.json : absent')
        return 1
    try:
        qs = json.loads(io.open(FICHIER, encoding='utf-8').read())
    except Exception as e:
        print('apprentis/questions.json : JSON illisible (%s)' % e)
        return 1
    defauts = controler(qs)
    # Le seuil par question (ci-dessus) ne voit pas le biais d'ensemble : quarante bonnes réponses
    # plus longues de trois caractères chacune passent une par une, et pourtant « cocher la plus
    # longue » rend la banque devinable. Avec trois réponses, le hasard donne 33 %.
    if qs:
        devinables = sum(1 for q in qs if isinstance(q.get('r'), list) and len(q['r']) > 1
                         and len(q['r'][0]) > max(len(x) for x in q['r'][1:]))
        part = 100 * devinables / len(qs)
        if part > 45:
            defauts.append('ENSEMBLE : la bonne réponse est strictement la plus longue dans %d cas sur %d (%d %%) — '
                           'le hasard en donnerait 33 %%. Étoffer les mauvaises réponses.' % (devinables, len(qs), round(part)))
    print('apprentis/questions.json : %d question(s), %d défaut(s)' % (len(qs), len(defauts)))
    for x in defauts:
        print('  -', x)
    if defauts:
        return 1
    par_bloc = Counter(q['b'] for q in qs)
    for b, nom in enumerate(BLOCS):
        print('  bloc %d · %-42s %2d question(s)' % (b, nom, par_bloc.get(b, 0)))
    print('  par n      :', dict(sorted(Counter(q['n'] for q in qs).items())))
    print('  CAP MPI    :', dict(sorted(Counter(q['mpi'] for q in qs).items())))
    print('  Étancheur  :', dict(sorted(Counter(q['etanch'] for q in qs).items())))
    ecarts = [len(q['r'][0]) - max(len(x) for x in q['r'][1:]) for q in qs]
    devinables = sum(1 for q in qs if len(q['r'][0]) > max(len(x) for x in q['r'][1:]))
    print('  biais de longueur : bonne réponse strictement la plus longue dans %d cas sur %d (%d %%, hasard 33 %%) · écart moyen %+.1f caractère(s)'
          % (devinables, len(qs), round(100 * devinables / len(qs)), sum(ecarts) / len(ecarts)))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
