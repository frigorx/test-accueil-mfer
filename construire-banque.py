# -*- coding: utf-8 -*-
"""
CONSTRUIRE LA BANQUE DU QUIZ DE POSITIONNEMENT
==============================================
Contrôle chaque fichier banque/niveau-N.json (forme, longueurs, codes, symboles, doublons) puis fusionne
tout en banque.json, avec des statistiques par niveau, par compétence et par symbole.

USAGE   python construire-banque.py                          contrôle tout et écrit banque.json
        python construire-banque.py --controle banque/niveau-2.json   contrôle un fichier, n'écrit rien
"""
import glob, io, json, os, re, sys

sys.stdout.reconfigure(encoding='utf-8')
ICI = os.path.dirname(os.path.abspath(__file__))
MFER = {'C%d' % i for i in range(1, 14)}
CAP = {'C1.1', 'C1.2', 'C1.3', 'C2.1', 'C2.2', 'C2.3', 'C2.4', 'C3.1', 'C3.2', 'C3.3', 'C3.4', 'C3.5', 'C3.6', 'C3.7',
       'C3.8', 'C3.9', 'C4.1', 'C4.2', 'C4.3', 'C4.4', 'C4.5', 'C4.6', 'C4.7'}
CHAMPS = {'id', 'niveau', 'theme', 'q', 'r', 'e', 'mfer', 'cap', 'tax', 'source', 'svg', 'd'}


def symboles():
    p = os.path.join(ICI, 'symboles.svg')
    if not os.path.exists(p):
        return set()
    return set(re.findall(r'id="([a-z_0-9-]+)"', io.open(p, encoding='utf-8').read()))


def mots(t):
    return len(re.findall(r"[\wÀ-ÿ'’-]+", t or ''))


def controler(chemin, deja=None):
    """Rend (questions, défauts). `deja` : questions des autres fichiers, pour les doublons."""
    defauts, qs = [], []
    try:
        qs = json.loads(io.open(chemin, encoding='utf-8').read())
    except Exception as e:
        return [], ['%s : JSON illisible (%s)' % (chemin, e)]
    if not isinstance(qs, list):
        return [], ['%s : le fichier doit être un tableau' % chemin]
    ids, textes = set(), {(q.get('q') or '').strip().lower() for q in (deja or [])}
    sym = symboles()
    for i, q in enumerate(qs):
        ou = '%s #%d (%s)' % (os.path.basename(chemin), i + 1, q.get('id', '?'))
        inconnus = set(q) - CHAMPS
        if inconnus:
            defauts.append('%s : champs inconnus %s' % (ou, sorted(inconnus)))
        for k in ('id', 'niveau', 'theme', 'q', 'r', 'e', 'mfer', 'cap', 'tax', 'source'):
            if k not in q:
                defauts.append('%s : champ manquant « %s »' % (ou, k))
        if q.get('id') in ids:
            defauts.append('%s : identifiant en double' % ou)
        ids.add(q.get('id'))
        if not isinstance(q.get('niveau'), int) or not 0 <= q['niveau'] <= 5:
            defauts.append('%s : niveau hors 0-5' % ou)
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
        if q.get('mfer') not in MFER:
            defauts.append('%s : code MFER inconnu « %s »' % (ou, q.get('mfer')))
        if q.get('cap') not in CAP:
            defauts.append('%s : code CAP inconnu « %s »' % (ou, q.get('cap')))
        if q.get('tax') not in (1, 2, 3):
            defauts.append('%s : tax doit valoir 1, 2 ou 3' % ou)
        if q.get('svg') and sym and q['svg'] not in sym:
            defauts.append('%s : symbole inconnu « %s »' % (ou, q['svg']))
        if q.get('d') not in (None, 'MFER', 'CAP'):
            defauts.append('%s : d doit valoir MFER ou CAP' % ou)
        if not (q.get('source') or '').strip():
            defauts.append('%s : source vide' % ou)
        t = (q.get('q') or '').strip().lower()
        if t in textes:
            defauts.append('%s : question déjà posée ailleurs : « %s »' % (ou, t[:60]))
        textes.add(t)
    return qs, defauts


def poser_symboles():
    """Colle la palette (symboles.svg) dans positionnement.html, entre les balises SYMBOLES ; idempotent."""
    page = os.path.join(ICI, 'positionnement.html')
    sprite = os.path.join(ICI, 'symboles.svg')
    if not (os.path.exists(page) and os.path.exists(sprite)):
        print('symboles : page ou palette absente')
        return
    svg = io.open(sprite, encoding='utf-8').read()
    m = re.search(r'<svg[\s\S]*</svg>', svg)
    if not m:
        print('symboles : palette illisible')
        return
    bloc = m.group(0)
    if 'display:none' not in bloc[:400]:
        bloc = bloc.replace('<svg', '<svg style="display:none" aria-hidden="true"', 1)
    html = io.open(page, encoding='utf-8').read()
    deb, fin = '<!-- SYMBOLES:debut', '<!-- SYMBOLES:fin -->'
    i, j = html.find(deb), html.find(fin)
    if i < 0 or j < 0:
        print('symboles : balises absentes de la page')
        return
    i2 = html.find('-->', i) + 3
    html = html[:i2] + '\n' + bloc + '\n' + html[j:]
    io.open(page, 'w', encoding='utf-8', newline='\n').write(html)
    print('symboles : %d posés dans positionnement.html' % len(re.findall(r'<g id="', bloc)))


def main():
    if '--symboles' in sys.argv:
        poser_symboles()
        return 0
    if '--controle' in sys.argv:
        fichiers = [a for a in sys.argv[1:] if a.endswith('.json')]
        autres = []
        for f in sorted(glob.glob(os.path.join(ICI, 'banque', 'niveau-*.json'))):
            if os.path.abspath(f) not in {os.path.abspath(x) for x in fichiers}:
                try:
                    autres += json.loads(io.open(f, encoding='utf-8').read())
                except Exception:
                    pass
        total = 0
        for f in fichiers:
            qs, d = controler(f, autres)
            total += len(d)
            print('%s : %d question(s), %d défaut(s)' % (os.path.basename(f), len(qs), len(d)))
            for x in d:
                print('  -', x)
        print('%d défaut(s)' % total)
        return 1 if total else 0

    tout, defauts = [], []
    for f in sorted(glob.glob(os.path.join(ICI, 'banque', 'niveau-*.json'))):
        qs, d = controler(f, tout)
        defauts += d
        tout += qs
        print('%s : %d question(s), %d défaut(s)' % (os.path.basename(f), len(qs), len(d)))
    for x in defauts:
        print('  -', x)
    if defauts:
        print('%d défaut(s) : banque.json NON écrite' % len(defauts))
        return 1
    tout.sort(key=lambda q: (q['niveau'], q['id']))
    io.open(os.path.join(ICI, 'banque.json'), 'w', encoding='utf-8', newline='\n').write(json.dumps(tout, ensure_ascii=False, indent=0))
    from collections import Counter
    poser_symboles()
    print('banque.json : %d questions' % len(tout))
    print('  par niveau :', dict(sorted(Counter(q['niveau'] for q in tout).items())))
    print('  par tax    :', dict(sorted(Counter(q['tax'] for q in tout).items())))
    print('  MFER       :', dict(sorted(Counter(q['mfer'] for q in tout).items(), key=lambda x: int(x[0][1:]))))
    print('  CAP        :', dict(sorted(Counter(q['cap'] for q in tout).items())))
    print('  symboles   :', sum(1 for q in tout if q.get('svg')), '· restreintes :', dict(Counter(q.get('d') for q in tout if q.get('d'))))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
