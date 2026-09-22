# -*- coding: utf-8 -*-
"""
CONTRÔLER LES TROIS QCM « ACCUEIL SÉCURITÉ APPRENANT »
======================================================
Trois QCM distincts — MPI, Étancheur, CVC — assemblés chacun à partir du tronc commun
(apprentis/commun.json) et de son fichier métier (mpi.json, etancheur.json, cvc.json).

Même exigence que construire-banque.py : forme, longueurs, codes de compétence, doublons,
biais de longueur de la bonne réponse — et, en plus, la mesure d'ensemble de ce biais.

USAGE   PYTHONIOENCODING=utf-8 python controler-apprentis.py
"""
import io, json, os, re, sys
from collections import Counter

sys.stdout.reconfigure(encoding='utf-8')
ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.join(ICI, 'apprentis')

# Arrêté du 15 avril 2019 (CAP MPI) et arrêté du 29 août 2022 (CAP Étancheur).
MPI = {'C1.1', 'C1.2', 'C2.1', 'C2.2', 'C2.3'} | {'C3.%d' % i for i in range(1, 17)}
ETANCH = {'C1.1', 'C1.2', 'C2.1', 'C2.2', 'C2.3'} | {'C3.%d' % i for i in range(1, 15)} | {'C4.1', 'C4.2', 'C4.3'}
# Le TP TECVC est un titre de bureau d'études : son REAC (CP1 à CP10) ne code aucune compétence
# de sécurité. Le QCM CVC ne porte donc pas de code — c'est un constat de référentiel, pas un oubli.

BLOCS = ["Les règles du lycée valent aussi pour moi", "En entreprise, avec mon tuteur",
         "Mes équipements de protection", "Le travail en hauteur",
         "Les risques de mon métier", "Ma responsabilité et l'accident"]
BLOC_METIER = 4

# fichier → (codes exigés, blocs permis)
FICHIERS = {
    'commun.json':    (('mpi', 'etanch'), {0, 1, 2, 3, 5}),
    'mpi.json':       (('mpi',),          {BLOC_METIER}),
    'etancheur.json': (('etanch',),       {BLOC_METIER}),
    'cvc.json':       ((),                {BLOC_METIER}),
}
QCM = {'mpi': 'mpi.json', 'etancheur': 'etancheur.json', 'cvc': 'cvc.json'}
CODES = {'mpi': MPI, 'etanch': ETANCH}
BASE = {'id', 'b', 'n', 'q', 'r', 'e', 'source'}


def mots(t):
    return len(re.findall(r"[\wÀ-ÿ'’-]+", t or ''))


def lire(nom):
    chemin = os.path.join(DOSSIER, nom)
    if not os.path.exists(chemin):
        return None, ['%s : absent' % nom]
    try:
        qs = json.loads(io.open(chemin, encoding='utf-8').read())
    except Exception as e:
        return None, ['%s : JSON illisible (%s)' % (nom, e)]
    if not isinstance(qs, list):
        return None, ['%s : le fichier doit être un tableau' % nom]
    return qs, []


def controler(nom, qs):
    exiges, blocs = FICHIERS[nom]
    champs = BASE | set(exiges)
    defauts, ids = [], set()
    for i, q in enumerate(qs):
        ou = '%s #%d (%s)' % (nom, i + 1, q.get('id', '?'))
        inconnus = set(q) - champs
        if inconnus:
            defauts.append('%s : champs inconnus %s (ce fichier n\'en porte pas)' % (ou, sorted(inconnus)))
        for k in champs:
            if k not in q:
                defauts.append('%s : champ manquant « %s »' % (ou, k))
        if q.get('id') in ids:
            defauts.append('%s : identifiant en double' % ou)
        ids.add(q.get('id'))
        if q.get('b') not in blocs:
            defauts.append('%s : bloc %s hors des blocs de ce fichier %s' % (ou, q.get('b'), sorted(blocs)))
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
            # Même seuil que construire-banque.py : cocher la plus longue sans lire ne doit rien
            # rapporter. Une mauvaise réponse se rédige aussi soigneusement que la bonne.
            bonne, fausses = len(r[0]), [len(x) for x in r[1:]]
            if bonne > max(fausses) * 1.25 and bonne - max(fausses) > 8:
                defauts.append('%s : la bonne réponse est la plus longue (%d contre %d) — étoffer les fausses ou resserrer la bonne'
                               % (ou, bonne, max(fausses)))
            if bonne * 1.25 < min(fausses) and min(fausses) - bonne > 8:
                defauts.append('%s : la bonne réponse est nettement la plus courte (%d contre %d) — même biais, à l\'envers'
                               % (ou, bonne, min(fausses)))
        for champ in exiges:
            if q.get(champ) not in CODES[champ]:
                defauts.append('%s : code %s inconnu « %s »' % (ou, champ, q.get(champ)))
        if not (q.get('source') or '').strip():
            defauts.append('%s : source vide' % ou)
    return defauts


def devinables(qs):
    """Combien de fois la bonne réponse est STRICTEMENT la plus longue. Le hasard donne 1/3."""
    return sum(1 for q in qs if isinstance(q.get('r'), list) and len(q['r']) > 1
               and len(q['r'][0]) > max(len(x) for x in q['r'][1:]))


def main():
    defauts, banques = [], {}
    for nom in FICHIERS:
        qs, d = lire(nom)
        defauts += d
        if qs is None:
            continue
        banques[nom] = qs
        defauts += controler(nom, qs)
        print('%-16s %2d question(s)' % (nom, len(qs)))
    if len(banques) != len(FICHIERS):
        for x in defauts:
            print('  -', x)
        return 1

    print()
    for qcm, metier in QCM.items():
        qs = banques['commun.json'] + banques[metier]
        textes = Counter((q.get('q') or '').strip().lower() for q in qs)
        for t, n in textes.items():
            if n > 1:
                defauts.append('QCM %s : question posée %d fois — « %s »' % (qcm, n, t[:60]))
        ids = Counter(q.get('id') for q in qs)
        for i, n in ids.items():
            if n > 1:
                defauts.append('QCM %s : identifiant « %s » en double' % (qcm, i))
        # Le seuil par question ne voit pas le biais d'ensemble : trente bonnes réponses plus
        # longues de trois caractères chacune passent une par une, et rendent pourtant le QCM
        # devinable sans le lire. Avec trois réponses, le hasard donne 33 %.
        dev = devinables(qs)
        part = 100 * dev / len(qs)
        if part > 45:
            defauts.append('QCM %s : la bonne réponse est strictement la plus longue dans %d cas sur %d (%d %%) — '
                           'le hasard en donnerait 33 %%. Étoffer les mauvaises réponses.' % (qcm, dev, len(qs), round(part)))
        ecarts = [len(q['r'][0]) - max(len(x) for x in q['r'][1:]) for q in qs]
        print('QCM %-10s %2d questions · par bloc %s · niveaux %s' % (
            qcm, len(qs), dict(sorted(Counter(q['b'] for q in qs).items())), dict(sorted(Counter(q['n'] for q in qs).items()))))
        print('%-15s bonne réponse la plus longue : %d/%d (%d %%, hasard 33 %%) · écart moyen %+.1f caractère(s)'
              % ('', dev, len(qs), round(part), sum(ecarts) / len(ecarts)))
        champ = {'mpi': 'mpi', 'etancheur': 'etanch'}.get(qcm)
        if champ:
            print('%-15s compétences : %s' % ('', dict(sorted(Counter(q[champ] for q in qs).items()))))
        else:
            print('%-15s compétences : aucune — le REAC du titre CVC ne code pas la sécurité' % '')

    print()
    if defauts:
        print('%d défaut(s) :' % len(defauts))
        for x in defauts:
            print('  -', x)
        return 1
    print('0 défaut.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
