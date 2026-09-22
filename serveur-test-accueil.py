# -*- coding: utf-8 -*-
"""
SERVEUR LOCAL DU TEST D'ACCUEIL — dans l'esprit de SchoolRoom, sans rien installer
==================================================================================
Le PC du professeur sert la page du test aux téléphones de la classe (même réseau Wi-Fi, ou point
d'accès mobile du PC) et reçoit les résultats. Rien ne sort du PC, aucun forfait n'est nécessaire.

USAGE      python serveur-test-accueil.py            (port 8765)
           python serveur-test-accueil.py 8080

CE QUE VOIENT LES ÉLÈVES   http://ADRESSE-DU-PC:8765/          (l'adresse s'affiche au lancement)
CE QUE VOIT LE PROFESSEUR  http://localhost:8765/resultats     (tableau vivant, rafraîchi toutes les 10 s)
                           http://localhost:8765/resultats.csv (à ouvrir dans un tableur)

Les résultats s'écrivent dans resultats/test-accueil.jsonl (une ligne par élève, rien n'est jamais
effacé) et resultats/test-accueil.csv (refait à chaque réception).

Pare-feu : au premier lancement, Windows demande d'autoriser Python sur le réseau — autoriser,
sinon les téléphones ne voient pas le PC. Python seul suffit (bibliothèque standard).
"""
import csv, html, io, json, os, re, socket, sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ICI = os.path.dirname(os.path.abspath(__file__))
DOSSIER = os.path.join(ICI, 'resultats')
JSONL = os.path.join(DOSSIER, 'test-accueil.jsonl')
CSV = os.path.join(DOSSIER, 'test-accueil.csv')
# Les engagements sont une TRACE, pas une donnée de travail : fichier à part, on n'y ajoute
# que des lignes, jamais de filtrage ni de réécriture, et le CSV ne le touche pas.
ENGAGEMENTS = os.path.join(DOSSIER, 'engagements.jsonl')
PORT = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8765
COLONNES = ['recu', 'type', 'nom', 'diplome', 'classe', 'niveau', 'niveau_nom', 'note', 'justes', 'total', 'sorties', 'arret', 'repondu',
            'minutes', 'code', 'competences', 'niveaux', 'tax', 'blocs', 'reponses', 'ip']


def lire_resultats(toutes_les_classes=False):
    """Les résultats de la CLASSE DU JOUR (bilan, « qui a fait quoi », cartographie, CSV passent tous par ici).

    Le fichier garde tout, pour toujours : on ne filtre qu'à la lecture. Deux classes peuvent donc passer
    le même jour sans se mélanger, et une classe de l'an dernier se retrouve en la rechoisissant.
    Tant qu'aucune classe n'est nommée dans le poste de commande, on montre tout, comme avant."""
    lignes = []
    if os.path.exists(JSONL):
        with io.open(JSONL, encoding='utf-8') as f:
            for l in f:
                l = l.strip()
                if l:
                    try:
                        lignes.append(json.loads(l))
                    except ValueError:
                        pass
    if toutes_les_classes:
        return lignes
    active = str(reglages().get('nom_classe') or '').strip()
    if not active:
        return lignes
    return [l for l in lignes if str(l.get('seance') or '').strip() == active]


def ecrire_csv(lignes):
    with io.open(CSV, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=COLONNES, delimiter=';', extrasaction='ignore')
        w.writeheader()
        for l in lignes:
            w.writerow({k: l.get(k, '') for k in COLONNES})


SUIVI = {}   # qui est connecté en ce moment : clé = nom normalisé (cle_nom) → dernier signe de vie, coupures, activités vues
SILENCE_ROUGE = 60   # secondes sans signe de vie avant le rouge (Franck, 17/09/2026)
ACTIVITES_NOMS = {'accueil': "Test d'accueil", 'positionnement': "Où j'en suis", 'manometres': 'Manomètres', 'jeu-schema': 'Jeu du schéma'}


def noter_signe_de_vie(d, fini=False):
    """Un signe de vie (toutes les 20 s depuis les pages) ou un résultat reçu : on garde la dernière heure, le premier contact,
    les coupures de plus de SILENCE_ROUGE secondes et les activités vues. Clé : le nom normalisé, pour suivre l'élève d'une activité à l'autre."""
    import time
    maintenant = time.time()
    k = cle_nom(d.get('nom')) or str(d.get('nom'))
    prev = SUIVI.get(k) or {}
    d = dict(d)
    d['_t'] = maintenant
    d['_premier'] = prev.get('_premier', maintenant)
    d['_coupures'] = list(prev.get('_coupures', []))
    if prev and maintenant - prev.get('_t', maintenant) > SILENCE_ROUGE and not prev.get('fini'):
        d['_coupures'].append([prev['_t'], maintenant])
    d['_activites'] = sorted(set(prev.get('_activites', []) + ([d.get('type')] if d.get('type') else [])))
    if fini:
        d['fini'] = True
    SUIVI[k] = d


def page_surveillance():
    """La page du téléphone du professeur (et du PC) : une carte par élève, rouge après SILENCE_ROUGE s de silence, gris quand il a fini,
    les jamais vus de la liste de la classe en bas. Rafraîchie toutes les 10 s."""
    import time
    maintenant = time.time()
    classe = [n for n in (reglages().get('classe') or []) if str(n).strip()]
    recus = {}
    for l in lire_resultats():
        recus.setdefault(cle_nom(l.get('nom')), set()).add(l.get('type') or 'accueil')
    cartes = []
    for k, v in SUIVI.items():
        silence = int(maintenant - v.get('_t', maintenant))
        coupures = v.get('_coupures', [])
        perdu = int(sum(b - a for a, b in coupures) / 60)
        if v.get('fini'):
            etat, ordre, titre = 'fini', 2, 'a terminé %s' % ACTIVITES_NOMS.get(v.get('type'), v.get('type', ''))
        elif silence > SILENCE_ROUGE:
            etat, ordre, titre = 'rouge', 0, 'HORS LIGNE depuis %d min %02d s' % (silence // 60, silence % 60)
        else:
            etat, ordre, titre = 'vert', 1, '%s · question %s / %s' % (ACTIVITES_NOMS.get(v.get('type'), v.get('type', '')), v.get('question', '?'), v.get('total', '?'))
        detail = []
        if coupures:
            detail.append('%d coupure(s), %d min perdue(s)' % (len(coupures), perdu))
        if v.get('sorties'):
            detail.append('%s sortie(s) de la page' % v.get('sorties'))
        detail.append('vu depuis %d min' % int((maintenant - v.get('_premier', maintenant)) / 60))
        faits = ' '.join('✓ ' + ACTIVITES_NOMS.get(t, t) for t in sorted(recus.get(k, [])))
        cartes.append((ordre, silence if etat == 'rouge' else 0, v.get('nom', '?'),
                       '<div class="c %s"><b>%s</b><span class="t">%s</span><span class="d">%s</span>%s</div>'
                       % (etat, html.escape(str(v.get('nom', '?'))), html.escape(titre), html.escape(' · '.join(detail)),
                          ('<span class="f">%s</span>' % html.escape(faits)) if faits else '')))
    cartes.sort(key=lambda c: (c[0], -c[1], str(c[2]).lower()))
    vus = {k for k in SUIVI}
    jamais = [n for n in classe if cle_nom(n) not in vus]
    n_rouge = sum(1 for c in cartes if c[0] == 0); n_vert = sum(1 for c in cartes if c[0] == 1); n_fini = sum(1 for c in cartes if c[0] == 2)
    return ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta http-equiv="refresh" content="10">'
            '<meta name="robots" content="noindex, nofollow"><title>Surveillance de la classe</title>'
            '<style>*{box-sizing:border-box}body{margin:0;background:#eef1f5;color:#22303f;font-family:Calibri,Segoe UI,Arial,sans-serif;font-size:17px;line-height:1.35}'
            '.page{max-width:640px;margin:0 auto;padding:10px 12px 40px}h1{font-size:20px;color:#1b3a63;margin:6px 0 2px;font-family:Trebuchet MS,sans-serif}'
            '.etat{color:#5d6b7c;font-size:14px;margin:0 0 10px}.c{background:#fff;border-left:8px solid #0e7a5f;border-radius:10px;padding:10px 12px;margin:8px 0;display:flex;flex-direction:column;gap:2px;box-shadow:0 1px 6px rgba(27,58,99,.10)}'
            '.c b{font-size:19px}.c .t{font-weight:bold;color:#0e7a5f}.c .d,.c .f{font-size:14px;color:#5d6b7c}.c .f{color:#1b3a63}'
            '.rouge{border-left-color:#b3261e;background:#fdf3f3}.rouge .t{color:#b3261e;font-size:18px}.fini{border-left-color:#9aa5b1;background:#f5f6f8;color:#5d6b7c}.fini .t{color:#5d6b7c}'
            '.jamais{background:#fff;border-radius:10px;padding:10px 12px;margin:14px 0 0;font-size:15px}.jamais b{color:#1b3a63}a{color:#1b3a63}</style>'
            '<div class="page"><h1>Surveillance de la classe</h1>'
            '<p class="etat">%d en ligne · <b style="color:#b3261e">%d hors ligne</b> · %d terminé(s) · %d jamais vu(s) · rouge après %d s de silence · page rafraîchie toutes les 10 s</p>%s%s'
            '<p class="etat" style="margin-top:16px"><a href="/">Ouvrir les activités comme un élève</a> · <a href="/resultats">résultats (PC)</a></p></div>'
            % (n_vert, n_rouge, n_fini, len(jamais), SILENCE_ROUGE,
               ''.join(c[3] for c in cartes) or '<p class="etat">Personne n\'a encore ouvert une activité.</p>',
               ('<div class="jamais"><b>Jamais connectés (%d)</b> : %s</div>' % (len(jamais), html.escape(', '.join(jamais)))) if jamais else ''))


def bloc_suivi():
    import time
    maintenant = time.time()
    vivants = [(k, v) for k, v in SUIVI.items() if maintenant - v.get('_t', 0) < 90]
    if not vivants:
        return '<p><b>En ce moment :</b> personne de connecté.</p>'
    tr = []
    for k, v in sorted(vivants, key=lambda x: x[1].get('nom', '')):
        depuis = int(maintenant - v.get('_t', 0))
        alerte = ' style="background:#fdf3f3"' if (v.get('sorties') or 0) >= 3 else ''
        niveau = v.get('niveau', '')
        niveau = ('N%s' % niveau) if isinstance(niveau, int) else html.escape(str(niveau))
        tr.append('<tr%s><td><b>%s</b></td><td>%s</td><td>%s · question %s / %s</td><td>%s</td><td>%s min</td><td>%s</td><td>il y a %d s</td></tr>' % (
            alerte, html.escape(str(v.get('nom', ''))), html.escape(str(v.get('classe', '')))[:18], niveau, v.get('question', ''), v.get('total', ''),
            v.get('sorties', 0), v.get('minutes', ''), 'terminé' if v.get('fini') else 'en cours', depuis))
    return ('<h2 style="font-size:17px;color:#1b3a63">En ce moment — %d connecté(s)</h2>'
            '<table><tr><th>Nom</th><th>Classe</th><th>Où il en est</th><th>Sorties</th><th>Durée</th><th>État</th><th>Vu</th></tr>%s</table>' % (len(vivants), ''.join(tr)))


def cle_nom(nom):
    """« Léa DUPONT », « dupont lea » → même clé : minuscules, sans accents, mots triés."""
    import unicodedata
    t = unicodedata.normalize('NFD', str(nom or '')).encode('ascii', 'ignore').decode('ascii').lower()
    return ' '.join(sorted(re.findall(r'[a-z]+', t)))


def tableau_classe(lignes):
    """La classe de reglages.json (un nom par ligne) croisée avec les résultats reçus : une ligne par élève, une colonne par activité."""
    classe = [n for n in (reglages().get('classe') or []) if str(n).strip()]
    if not classe:
        return ('<p class="etat">Pour voir <b>qui a fait quoi</b>, coller la liste de la classe dans le poste de commande (<a href="/prof">réglages</a>).</p>')
    ACT = [('accueil', "Test d'accueil"), ('positionnement', "Où j'en suis"), ('manometres', 'Manomètres'), ('jeu-schema', 'Jeu du schéma')]
    par_eleve, inconnus = {}, {}
    cles = {cle_nom(n): n for n in classe}
    for l in lignes:
        k = cle_nom(l.get('nom'))
        t = l.get('type') or 'accueil'
        cible = par_eleve.setdefault(cles[k], {}) if k in cles else inconnus.setdefault(l.get('nom', '?'), {})
        if t == 'jeu-schema':
            v = '%s/%s' % (l.get('justes', ''), l.get('total', ''))
        elif t == 'positionnement':
            v = '%s/20 · %s' % (l.get('note', ''), str(l.get('niveau_nom', '')).split(' · ')[0])
        else:
            v = '%s/20' % l.get('note', '')
        cible[t] = v   # le dernier envoi fait foi
    def ligne(nom, d, gris=False):
        cells = ''.join('<td class="%s">%s</td>' % ('fait' if d.get(t) else 'vide', html.escape(d.get(t, '—'))) for t, _ in ACT)
        return '<tr%s><td><b>%s</b></td>%s</tr>' % (' style="color:#777"' if gris else '', html.escape(str(nom)), cells)
    faits = sum(1 for d in par_eleve.values() if d)
    corps = ''.join(ligne(n, par_eleve.get(n, {})) for n in classe)
    corps += ''.join(ligne(n, d, True) for n, d in sorted(inconnus.items()))
    note = ('<p class="etat">%d élève(s) sur %d ont envoyé au moins un résultat.%s</p>'
            % (faits, len(classe), (' En gris : %d nom(s) tapé(s) autrement que dans la liste.' % len(inconnus)) if inconnus else ''))
    return ('<style>.fait{background:#f2faf7;color:#0e7a5f;font-weight:bold}.vide{color:#aaa;text-align:center}</style>'
            '<h1>Qui a fait quoi</h1>%s<table><tr><th>Élève</th>%s</tr>%s</table><br>'
            % (note, ''.join('<th>%s</th>' % t for _, t in ACT), corps))


def banque_questions():
    """id → texte de la question, depuis banque.json (le quiz de positionnement)."""
    try:
        return {q['id']: q['q'] for q in json.loads(io.open(os.path.join(ICI, 'banque.json'), encoding='utf-8').read())}
    except Exception:
        return {}


def nombre(x):
    try:
        return float(str(x).replace(',', '.'))
    except (TypeError, ValueError):
        return None


def bilan(lignes):
    """Une ligne par élève de la liste (puis les noms inconnus) : dernière note par activité, total, note du jour, alertes, règles fausses."""
    classe = [n for n in (reglages().get('classe') or []) if str(n).strip()]
    cles = {cle_nom(n): n for n in classe}
    questions = banque_questions()
    par = {}
    for l in lignes:
        k = cle_nom(l.get('nom'))
        nom = cles.get(k, l.get('nom', '?'))
        par.setdefault(nom, {'connu': k in cles})[l.get('type') or 'accueil'] = l    # le dernier envoi fait foi
    ordre = classe + sorted(n for n in par if n not in cles.values())
    rangs = []
    for nom in ordre:
        d = par.get(nom, {'connu': True})
        a, p, m, j = d.get('accueil'), d.get('positionnement'), d.get('manometres'), d.get('jeu-schema')
        na, np_, nm = (nombre(a.get('note')) if a else None), (nombre(p.get('note')) if p else None), (nombre(m.get('note')) if m else None)
        total = (na or 0) + (np_ or 0) + (nm or 0)
        alertes, regles = [], []
        manque = [t for t, x in (("test d'accueil", a), ("où j'en suis", p), ('manomètres', m)) if not x]
        if len(manque) == 3:
            alertes.append("n'a rien fait")
        elif manque:
            alertes.append('manque : ' + ', '.join(manque))
        for t, x in (("accueil", a), ("positionnement", p)):
            if x and x.get('arret'):
                alertes.append('%s arrêté (5 sorties)' % t)
            elif x and (int(nombre(x.get('sorties')) or 0) >= 3):
                alertes.append('%s : %s sorties de la page' % (t, x.get('sorties')))
        if a:
            for bloc in str(a.get('blocs') or '').split(' · '):
                mm = re.match(r'(.+?) (\d+)/(\d+)$', bloc.strip())
                if mm and int(mm.group(3)) and int(mm.group(2)) / int(mm.group(3)) < 0.5 and mm.group(1) in ("Les règles de la classe", "La sécurité à l'atelier", 'Le règlement du lycée'):
                    alertes.append('règles : %s %s/%s' % (mm.group(1).lower(), mm.group(2), mm.group(3)))
            regles += [e for e in (a.get('erreurs') or []) if not e.startswith(('Les gestes', 'Le projet'))]
        if p:
            niv = nombre(p.get('niveau'))
            if niv is not None and niv < 0:
                alertes.append("règles : niveau 0 « l'atelier et les règles » non validé")
            for bloc in str(p.get('reponses') or '').split(' | '):
                if bloc.startswith('N0:'):
                    for rep in bloc[3:].split():
                        qid, _, val = rep.partition('=')
                        if val not in ('0', '-', '') and qid in questions:
                            regles.append("L'atelier et les règles · " + questions[qid])
        rangs.append({'nom': nom, 'connu': d.get('connu', True), 'accueil': na, 'positionnement': np_, 'niveau': (p or {}).get('niveau_nom', ''), 'manometres': nm,
                      'jeu': ('%s/%s' % (j.get('justes'), j.get('total'))) if j else None, 'total': total, 'alertes': alertes, 'regles': regles})
    maxi = max([r['total'] for r in rangs] + [0])
    for r in rangs:
        r['jour'] = round(20 * r['total'] / maxi * 2) / 2 if maxi else 0
    return rangs, maxi


def page_bilan(lignes):
    rangs, maxi = bilan(lignes)
    connus = [r for r in rangs if r['connu']]
    moy = (sum(r['jour'] for r in connus) / len(connus)) if connus else 0
    n_alerte = sum(1 for r in connus if r['alertes'])
    def n(x):
        return '—' if x is None else ('%g' % x).replace('.', ',')
    def tr(r):
        cls = ' class="alerte"' if r['alertes'] else ''   # rose : une alerte ; les questions de règles fausses restent lisibles sans colorer la ligne
        gris = ' style="color:#777"' if not r['connu'] else ''
        regles = ('<details><summary>%d question(s) de règles fausse(s)</summary><ul>%s</ul></details>'
                  % (len(r['regles']), ''.join('<li>%s</li>' % html.escape(q) for q in r['regles']))) if r['regles'] else ''
        return ('<tr%s%s><td><b>%s</b></td><td>%s</td><td>%s<br><small>%s</small></td><td>%s</td><td>%s</td><td>%s / 60</td><td class="jour">%s</td><td>%s%s</td></tr>'
                % (cls, gris, html.escape(str(r['nom'])), n(r['accueil']), n(r['positionnement']), html.escape(str(r['niveau'] or '')), n(r['manometres']),
                   html.escape(r['jeu'] or '—'), n(r['total']), n(r['jour']), html.escape(' · '.join(r['alertes'])), regles))
    return (CSS_PROF + '<meta http-equiv="refresh" content="30"><title>Bilan du jour</title>'
            '<style>table{border-collapse:collapse;width:100%%;background:#fff}td,th{border:1px solid #d8dee6;padding:6px 8px;text-align:left;vertical-align:top;font-size:15px}'
            'th{background:#f5f8fc;color:#1b3a63}.alerte{background:#fdf3f3}.jour{font-size:20px;font-weight:bold;color:#1b3a63}details{font-size:14px}summary{cursor:pointer;color:#b3261e;font-weight:bold}ul{margin:4px 0 0 16px;padding:0}small{color:#666}</style>'
            '<h1>Bilan du jour</h1><p class="etat"><b>Note du jour</b> : total des trois activités notées (test d\'accueil + où j\'en suis + manomètres, sur 60) ramené sur 20, '
            '<b>le meilleur total de la classe vaut 20</b> (%s / 60 aujourd\'hui) ; une activité non faite vaut zéro. Moyenne de la classe : <b>%s / 20</b> · %d élève(s) en alerte sur %d · '
            '<a href="/bilan.csv">télécharger le tableur</a> · <a href="/prof">poste de commande</a> · page rafraîchie toutes les 30 s.</p>'
            '<table><tr><th>Élève</th><th>Test d\'accueil</th><th>Où j\'en suis</th><th>Manomètres</th><th>Jeu</th><th>Total</th><th>Note du jour</th><th>Alertes · règles à reprendre</th></tr>%s</table>'
            '<p class="pied">En rose : au moins une alerte. En gris : un nom envoyé qui n\'est pas dans la liste de la classe.</p>'
            % (('%g' % maxi).replace('.', ','), ('%.1f' % moy).replace('.', ','), n_alerte, len(connus), ''.join(tr(r) for r in rangs)))


def csv_bilan(lignes):
    rangs, maxi = bilan(lignes)
    out = io.StringIO()
    w = csv.writer(out, delimiter=';')
    w.writerow(['élève', "test d'accueil /20", "où j'en suis /20", 'niveau atteint', 'manomètres /20', 'jeu du schéma', 'total /60', 'note du jour /20', 'alertes', 'questions de règles fausses'])
    fmt = lambda x: '' if x is None else ('%g' % x).replace('.', ',')   # virgule décimale pour Excel en français
    for r in rangs:
        w.writerow([r['nom'], fmt(r['accueil']), fmt(r['positionnement']), r['niveau'], fmt(r['manometres']), r['jeu'] or '', fmt(r['total']), fmt(r['jour']),
                    ' · '.join(r['alertes']), ' | '.join(r['regles'])])
    return out.getvalue()


def page_resultats(lignes):
    page = page_resultats_brut(lignes)
    return page.replace('<h1>', tableau_classe(lignes) + '<h1>', 1)


def page_resultats_brut(lignes):
    lignes = sorted(lignes, key=lambda l: l.get('recu', ''), reverse=True)
    tr = []
    for l in lignes:
        cls = ' style="background:#fdf3f3"' if l.get('arret') else ''
        tr.append('<tr%s><td>%s</td><td><b>%s</b></td><td>%s</td><td style="font-size:20px"><b>%s</b></td><td>%s%s</td><td>%s / %s</td><td><code>%s</code></td><td style="font-size:12px">%s</td></tr>' % (
            cls, html.escape(str(l.get('recu', ''))[11:16]), html.escape(str(l.get('nom', ''))), html.escape(str(l.get('diplome', ''))[:22]),
            html.escape(str(l.get('note', ''))), html.escape(str(l.get('sorties', 0))), ' — arrêté' if l.get('arret') else '',
            html.escape(str(l.get('repondu', ''))), html.escape(str(l.get('total', ''))), html.escape(str(l.get('code', ''))),
            html.escape(str(l.get('competences', '')))))
    return ('<meta charset="utf-8"><meta http-equiv="refresh" content="10"><title>Résultats du test d\'accueil</title>'
            '<style>body{font-family:Calibri,Segoe UI,sans-serif;margin:18px;color:#22303f}table{border-collapse:collapse;width:100%%}'
            'td,th{border:1px solid #d8dee6;padding:5px 8px;text-align:left;vertical-align:top}th{background:#f5f8fc;color:#1b3a63}'
            'h1{color:#1b3a63;font-size:20px}a{color:#1b3a63}</style>'
            '<h1>Résultats — %d reçu(s)</h1>'
            '<p>Rafraîchi toutes les 10 secondes · <a href="/resultats.csv">télécharger le tableau (CSV)</a> · <a href="/cartographie">cartographie des compétences</a> · fichier : %s</p>'
            '%s'
            '<h2 style="font-size:17px;color:#1b3a63">Résultats reçus</h2>'
            '<table><tr><th>Heure</th><th>Nom</th><th>Classe · date</th><th>Note /20</th><th>Sorties</th><th>Répondu</th><th>Code</th><th>Compétences</th></tr>%s</table>'
            % (len(lignes), html.escape(JSONL), bloc_suivi(), ''.join(tr) or '<tr><td colspan="8">Aucun résultat pour l\'instant.</td></tr>'))


ECHELLE = ['non évalué', 'non acquis', 'en cours', 'acquis', 'parfaitement maîtrisé']


def cartographie(lignes):
    """Une ligne par élève (son dernier résultat de positionnement), une colonne par compétence : la note 0-4."""
    derniers = {}
    for l in lignes:
        if l.get('type') == 'positionnement' and isinstance(l.get('carte'), dict):
            derniers[(l.get('nom', ''), l.get('classe', ''))] = l
    codes = sorted({c for l in derniers.values() for c in l['carte']}, key=lambda c: [int(x) if x.isdigit() else x for x in c.replace('C', '').split('.')])
    eleves = sorted(derniers.values(), key=lambda l: (l.get('classe', ''), l.get('nom', '')))
    return codes, eleves


def csv_cartographie(codes, eleves):
    out = io.StringIO()
    w = csv.writer(out, delimiter=';')
    w.writerow(['nom', 'classe', 'date', 'niveau atteint', 'justes', 'total', 'sorties'] + codes + ['moyenne 0-4'])
    for l in eleves:
        vals = [l['carte'].get(c, '') for c in codes]
        nums = [v for v in vals if isinstance(v, int) and v > 0]
        w.writerow([l.get('nom'), l.get('classe'), l.get('quand', ''), l.get('niveau_nom', ''), l.get('justes', ''), l.get('total', ''), l.get('sorties', '')]
                   + vals + [round(sum(nums) / len(nums), 2) if nums else ''])
    return out.getvalue()


def page_cartographie(codes, eleves):
    couleurs = {0: '#eef1f5', 1: '#f8d7d3', 2: '#fde3c9', 3: '#d5efe6', 4: '#cfe0f5'}
    tr = []
    for l in eleves:
        cells = ''.join('<td style="background:%s;text-align:center" title="%s">%s</td>' % (couleurs.get(l['carte'].get(c, 0), '#fff'), ECHELLE[l['carte'].get(c, 0)], l['carte'].get(c, '·')) for c in codes)
        tr.append('<tr><td><b>%s</b><br><span style="font-size:11px;color:#5d6b7c">%s · %s</span></td><td>%s</td>%s</tr>' % (
            html.escape(str(l.get('nom', ''))), html.escape(str(l.get('classe', ''))), html.escape(str(l.get('quand', ''))), html.escape(str(l.get('niveau_nom', ''))), cells))
    th = ''.join('<th style="writing-mode:vertical-rl;transform:rotate(180deg);padding:6px 2px">%s</th>' % html.escape(c) for c in codes)
    # colonne : part d'élèves à « acquis » ou mieux, pour lire les points faibles de la classe
    bas = []
    for c in codes:
        vals = [l['carte'].get(c, 0) for l in eleves if l['carte'].get(c, 0) > 0]
        bas.append('<td style="text-align:center;font-size:12px">%s</td>' % ('%d %%' % round(100 * sum(1 for v in vals if v >= 3) / len(vals)) if vals else '·'))
    return ('<meta charset="utf-8"><meta http-equiv="refresh" content="20"><title>Cartographie de la classe</title>'
            '<style>body{font-family:Calibri,Segoe UI,sans-serif;margin:18px;color:#22303f}table{border-collapse:collapse}'
            'td,th{border:1px solid #d8dee6;padding:4px 6px;font-size:13px;vertical-align:middle}th{background:#f5f8fc;color:#1b3a63}'
            'h1{color:#1b3a63;font-size:20px}a{color:#1b3a63}.leg span{display:inline-block;padding:2px 8px;margin-right:6px;border-radius:4px;font-size:12px}</style>'
            '<h1>Cartographie — %d élève(s), %d compétence(s)</h1>'
            '<p class="leg"><span style="background:#f8d7d3">1 non acquis</span><span style="background:#fde3c9">2 en cours</span>'
            '<span style="background:#d5efe6">3 acquis</span><span style="background:#cfe0f5">4 parfaitement maîtrisé</span> · '
            '<a href="/cartographie.csv">télécharger le CSV</a> · <a href="/resultats">tous les résultats</a></p>'
            '<table><tr><th>Élève</th><th>Niveau atteint</th>%s</tr>%s<tr><td colspan="2"><b>Part de la classe à « acquis » ou mieux</b></td>%s</tr></table>'
            % (len(eleves), len(codes), th, ''.join(tr) or '<tr><td colspan="99">Aucun positionnement reçu pour l\'instant.</td></tr>', ''.join(bas)))


def adresse_eleves(chemin=''):
    ips = adresses()
    return 'http://%s:%d/%s' % (ips[0] if ips else 'localhost', PORT, chemin)


def reglages():
    """reglages.json à côté du serveur (jamais publié) : {"ssid": "...", "motdepasse": "...", "adresse": "http://192.168.137.1:8765/",
    "whatsapp": "33612345678"} — tout facultatif. Le numéro voyage dans les liens en ligne (?wa=), jamais dans les pages."""
    p = os.path.join(ICI, 'reglages.json')
    try:
        return json.loads(io.open(p, encoding='utf-8').read()) if os.path.exists(p) else {}
    except ValueError:
        return {}


# Ce qui appartient à UNE classe et change avec elle : sa liste d'élèves, son groupe WhatsApp
# (chaque classe a le sien), le nom affiché de ce groupe, et le fait de le montrer ou non.
# Le reste (Wi-Fi, numéro du professeur, code de surveillance) est commun à toutes les classes.
CHAMPS_CLASSE = ('classe', 'groupe_whatsapp', 'nom_groupe', 'afficher_whatsapp')


def ecrire_reglages(r):
    io.open(os.path.join(ICI, 'reglages.json'), 'w', encoding='utf-8').write(json.dumps(r, ensure_ascii=False, indent=1))


def archiver_classe(r, nom):
    """Range les réglages de la classe `nom` dans r['classes'], sans rien perdre.

    Les clés de premier niveau restent celles de la CLASSE ACTIVE : tout le reste du serveur
    continue de lire reglages()['classe'] ou ['groupe_whatsapp'] sans savoir qu'il y a des archives."""
    nom = (nom or '').strip()
    if not nom:
        return r
    r.setdefault('classes', {})[nom] = dict((k, r.get(k)) for k in CHAMPS_CLASSE)
    return r


def charger_classe(r, nom):
    """Remonte les réglages archivés de `nom` au premier niveau ; classe inconnue = classe neuve, vide."""
    arch = (r.get('classes') or {}).get((nom or '').strip()) or {}
    for k in CHAMPS_CLASSE:
        r[k] = arch.get(k) if k in arch else ([] if k == 'classe' else ('' if k != 'afficher_whatsapp' else True))
    r['nom_classe'] = (nom or '').strip()
    return r


def classes_connues(r=None):
    """Les noms de classe déjà enregistrés, la classe active comprise, par ordre alphabétique."""
    r = r if r is not None else reglages()
    noms = set((r.get('classes') or {}).keys())
    if (r.get('nom_classe') or '').strip():
        noms.add(r['nom_classe'].strip())
    return sorted(noms, key=lambda s: s.lower())


def qr_png(texte=None):
    """Un QR code (PNG) si le module qrcode est installé (pip install qrcode[pil]) ; sinon None."""
    try:
        import qrcode
    except ImportError:
        return None
    buf = io.BytesIO()
    qrcode.make(texte or adresse_eleves(), box_size=12, border=2).save(buf, format='PNG')
    return buf.getvalue()


def qr_wifi():
    """Le QR « rejoindre le Wi-Fi » (lu par l'appareil photo des téléphones), si le SSID est réglé."""
    r = reglages()
    if not r.get('ssid'):
        return None
    mdp = r.get('motdepasse', '')
    return qr_png('WIFI:T:%s;S:%s;P:%s;;' % ('WPA' if mdp else 'nopass', r['ssid'], mdp))


def qr_groupe():
    """Le QR du groupe WhatsApp de la classe (lien d'invitation dans reglages.json, jamais publié)."""
    lien = reglages().get('groupe_whatsapp')
    return qr_png(lien) if lien else None


ACTIVITES = [
    ('/index.html', "1. Test d'accueil", 'sécurité et règles de la classe · 41 questions · noté sur 20', '#1b3a63'),
    ('/positionnement.html', "2. Où j'en suis", 'froid, climatisation, habilitations · six niveaux · noté, barème dégressif', '#c9451a'),
    ('/manometres.html', '3. Lire un manomètre', 'pression, fluide, température · 10 questions · noté sur 20', '#0e7a5f'),
    ('/jeux/schema-frigo/', '4. Jeu : compléter le schéma frigorifique', 'je pose chaque organe à sa place', '#5d6b7c'),
    ('/apprentis/', '5. Accueil sécurité apprenant', 'apprentis MPI, Étancheur, TP CVC · règles, EPI, hauteur, accident · 40 questions', '#7a4b8f'),
]


def page_accueil():
    """L'accueil des téléphones : les activités dans l'ordre, un bouton chacune, le groupe WhatsApp si réglé."""
    r = reglages()
    boutons = list(ACTIVITES)
    # Le groupe est celui de la classe active, et le professeur décide de le montrer ou non
    # (réglages d'avant cette version : pas de clé, donc affiché comme avant).
    if r.get('groupe_whatsapp') and r.get('afficher_whatsapp', True):
        nom_g = (r.get('nom_groupe') or '').strip()
        boutons.append(('/groupe', 'Rejoindre ' + ('le groupe ' + nom_g if nom_g else 'le groupe WhatsApp de la classe'),
                        'ouvre WhatsApp · une seule fois', '#128c7e'))
    boutons.append(('/aide', 'Un problème ?', "mon écran s'éteint, j'ai perdu la page, mon téléphone dit qu'il n'y a pas Internet", '#5d6b7c'))
    b = ''.join('<a class="b" href="%s" style="background:%s"><b>%s</b><span>%s</span></a>' % (h, c, html.escape(t), html.escape(d))
                for h, t, d, c in boutons)
    return ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><meta name="robots" content="noindex, nofollow">'
            '<title>Les activités du jour</title>'
            '<style>*{box-sizing:border-box}body{margin:0;background:#eef1f5;color:#22303f;font-family:Calibri,Segoe UI,Arial,sans-serif;font-size:18px;line-height:1.4}'
            '.page{max-width:640px;margin:0 auto;padding:0 14px 40px}header{background:#1b3a63;color:#fff;border-radius:0 0 10px 10px;padding:12px 16px;margin:0 -14px 14px}'
            'header .lycee{font-family:Trebuchet MS,sans-serif;font-weight:bold;letter-spacing:.06em;font-size:13px;opacity:.9}header h1{margin:2px 0 0;font-family:Trebuchet MS,sans-serif;font-size:19px}'
            '.b{display:flex;flex-direction:column;gap:3px;color:#fff;text-decoration:none;border-radius:12px;padding:16px 18px;margin:10px 0;min-height:64px;box-shadow:0 2px 12px rgba(27,58,99,.12)}'
            '.b b{font-size:20px;font-family:Trebuchet MS,sans-serif}.b span{font-size:15px;opacity:.92}p{margin:6px 0 10px}footer{font-size:12px;color:#5d6b7c;text-align:center;margin-top:20px}</style>'
            '<div class="page"><header><div class="lycee">LPP JACQUES RAYNAUD</div><h1>Les activités du jour, dans l\'ordre</h1></header>'
            '<p>Je fais les activités <b>dans l\'ordre</b>. À la fin de chaque test, mon résultat part tout seul vers le PC du professeur.</p>%s'
            '<footer>LPP Jacques Raynaud — Campus ÉQUATIO · F. Henninot · P. Warton · © F. Henninot 2026</footer></div>' % b)


def lire_engagements(toutes_les_classes=False):
    lignes = []
    if os.path.exists(ENGAGEMENTS):
        with io.open(ENGAGEMENTS, encoding='utf-8') as f:
            for l in f:
                l = l.strip()
                if l:
                    try:
                        lignes.append(json.loads(l))
                    except ValueError:
                        pass
    if toutes_les_classes:
        return lignes
    active = str(reglages().get('nom_classe') or '').strip()
    return lignes if not active else [l for l in lignes if str(l.get('seance') or '').strip() == active]


def page_engagements():
    """Qui s'est engagé à respecter les règles, et qui ne l'a pas fait. Page du professeur.

    Ce n'est pas une signature : c'est une trace horodatée, à lire avec le test lui-même,
    qui prouve, lui, que l'élève a répondu aux questions de sécurité."""
    r = reglages()
    active = (r.get('nom_classe') or '').strip()
    classe = [n for n in (r.get('classe') or []) if str(n).strip()]
    signes = {}
    for l in lire_engagements():
        signes[cle_nom(l.get('nom'))] = l
    lignes = ''
    for l in sorted(lire_engagements(), key=lambda x: str(x.get('quand') or '')):
        q = str(l.get('quand') or '')
        lisible_q = (q[8:10] + '/' + q[5:7] + '/' + q[0:4] + ' à ' + q[11:16].replace(':', ' h ')) if len(q) >= 16 else q
        lignes += ('<tr><td>%s</td><td>%s</td><td>%s</td></tr>'
                   % (html.escape(str(l.get('nom') or '')), lisible_q, html.escape(str(l.get('note') or ''))))
    manquants = [n for n in classe if cle_nom(n) not in signes]
    bloc_manquants = ''
    if classe:
        bloc_manquants = ('<h2>N\'ont pas coché (%d)</h2>' % len(manquants)
                          + ('<p class="etat">Personne : toute la classe s\'est engagée.</p>' if not manquants else
                             '<p class="etat">À reprendre avec eux. Ne pas cocher n\'est pas une faute : c\'est une information.</p>'
                             '<ul class="manque">' + ''.join('<li>%s</li>' % html.escape(n) for n in manquants) + '</ul>'))
    autres = len(lire_engagements(True)) - len(lire_engagements())
    return (CSS_PROF + '<style>table{border-collapse:collapse;margin:8px 0}td,th{border:1px solid #d8dee6;padding:6px 12px;font-size:16px;text-align:left}'
            'th{background:#eef3f9;color:#1b3a63}.manque{font-size:17px;line-height:1.6}'
            '.avert{background:#fff6e6;border-left:6px solid #c9821a;border-radius:8px;padding:10px 14px;max-width:760px;font-size:15px}</style>'
            '<title>Engagements sur les règles</title><h1>Engagements sur les règles</h1>'
            '<p class="etat">%s%s · fichier <code>%s</code>, jamais modifié ni purgé%s</p>'
            '<p class="avert"><b>Ce n\'est pas une signature.</b> C\'est une trace horodatée, à lire avec le test lui-même : '
            'ce sont les réponses aux questions de sécurité qui établissent que l\'élève a été informé. '
            'Le règlement intérieur, lui, est signé au dossier d\'inscription, par l\'élève et son responsable légal.</p>'
            '<h2>Ont coché (%d)</h2>%s%s'
            '<p class="pied"><a href="/prof">← Retour au poste de commande</a></p>'
            % (('Classe <b>%s</b>' % html.escape(active)) if active else 'Toutes classes',
               (' · %d élève(s) dans la liste' % len(classe)) if classe else '',
               html.escape(ENGAGEMENTS),
               (' · %d engagement(s) gardé(s) pour les autres classes' % autres) if autres else '',
               len(lire_engagements()),
               ('<table><tr><th>Élève</th><th>Quand</th><th>Note du test</th></tr>' + lignes + '</table>') if lignes else
               '<p class="etat">Aucun engagement enregistré pour cette classe.</p>',
               bloc_manquants))


def page_aide():
    """La même aide que sur le tableau, mais sur le téléphone de l'élève (celui qui est encore connecté).

    Ne remplace pas la page projetée : un élève vraiment déconnecté ne peut plus ouvrir cette page-ci,
    c'est le QR resté au tableau qui le rattrape."""
    cas = [("Mon écran s'éteint tout seul",
            "Un écran éteint compte comme une sortie de la page, et les sorties sont comptées. "
            "<b>Android</b> : Réglages &rarr; Affichage &rarr; Délai de mise en veille &rarr; le plus long. "
            "<b>iPhone</b> : Réglages &rarr; Luminosité et affichage &rarr; Verrouillage auto &rarr; <b>Jamais</b>."),
           ("Mon téléphone dit qu'il n'y a pas Internet",
            "C'est normal et ça n'empêche rien : le Wi-Fi de la classe sert à joindre le PC du professeur, "
            "pas à aller sur Internet. Je réponds <b>oui, rester connecté</b> et je continue."),
           ("J'ai perdu la page, j'ai fermé par erreur",
            "Je regarde le tableau : je rescanne le <b>QR n&deg;&nbsp;2</b>. Les codes y restent affichés "
            "pendant toute la séance. Ce que j'avais déjà validé n'est pas perdu."),
           ("Je n'arrive pas à me connecter au Wi-Fi",
            "Je rescanne le <b>QR n&deg;&nbsp;1</b> au tableau. Si ça ne marche toujours pas, je choisis le "
            "réseau à la main dans les réglages Wi-Fi et je tape le mot de passe écrit sous le QR code."),
           ("Je ne sais plus où j'en étais",
            "Je reviens à l'accueil et je reprends l'activité : elle me remet où j'en étais.")]
    blocs = ''.join('<div class="cas"><h2>' + html.escape(q) + '</h2><p>' + rep + '</p></div>' for q, rep in cas)
    return ('<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'
            '<meta name="robots" content="noindex, nofollow"><title>Un problème ?</title>'
            '<style>*{box-sizing:border-box}body{margin:0;background:#eef1f5;color:#22303f;'
            'font-family:Calibri,Segoe UI,Arial,sans-serif;font-size:18px;line-height:1.45}'
            '.page{max-width:640px;margin:0 auto;padding:0 14px 40px}'
            'header{background:#1b3a63;color:#fff;border-radius:0 0 10px 10px;padding:12px 16px;margin:0 -14px 14px}'
            'header h1{margin:0;font-family:Trebuchet MS,sans-serif;font-size:20px}'
            '.cas{background:#fff;border-radius:12px;padding:12px 16px;margin:10px 0;box-shadow:0 2px 12px rgba(27,58,99,.10)}'
            '.cas h2{font-family:Trebuchet MS,sans-serif;font-size:18px;color:#1b3a63;margin:0 0 6px}'
            '.cas p{margin:0}'
            '.retour{display:block;text-align:center;background:#1b3a63;color:#fff;text-decoration:none;'
            'border-radius:12px;padding:14px;margin:16px 0 0;font-size:19px}</style>'
            '<div class="page"><header><h1>Un problème ?</h1></header>' + blocs +
            '<a class="retour" href="/">Revenir aux activités</a></div>')


def page_projeter():
    """La page à projeter au tableau : TOUT sur un seul écran, sans jamais défiler.

    On ne fait pas défiler une projection pendant que la classe scanne, et l'élève en retard
    doit retrouver l'étape 1 quand les autres sont à la 3 : rien ne bouge, rien ne disparaît.
    Les hauteurs sont en vh pour que l'ensemble tienne quel que soit le vidéoprojecteur.
    La liste des activités n'est pas ici : l'élève l'a sous les yeux sur son téléphone."""
    r = reglages()
    url = r.get('adresse') or adresse_eleves()
    qr_ok = qr_png(url) is not None

    # Garde-fou : sans la borne branchée, l'adresse devinée est celle d'une autre carte du PC
    # (Hyper-V, Tailscale…) et aucun téléphone ne l'atteindra. On le dit avant de projeter.
    alerte_borne = ''
    if not r.get('adresse') and '192.168.8.' not in url:
        alerte_borne = ('<p class="alerte-borne">&#9940; <b>La borne Wi-Fi n\'est pas détectée.</b> '
                        'L\'adresse ci-dessous (<b>' + html.escape(url) + '</b>) est celle d\'une autre carte '
                        'réseau de ce PC : <b>les téléphones ne l\'atteindront pas.</b> Brancher le câble, '
                        'attendre dix secondes, recharger.</p>')

    if r.get('ssid'):
        bloc_wifi = ('<div class="col"><div class="num">1</div><h2>Je rejoins le Wi-Fi</h2>'
                     + ('<img src="/qr-wifi.png" alt="QR du Wi-Fi">' if qr_ok else '')
                     + '<div class="nom">' + html.escape(r['ssid']) + '</div>'
                     + '<p class="secours">sinon, à la main &mdash; mot de passe <b>'
                     + html.escape(r.get('motdepasse', '') or '(aucun)') + '</b></p></div>')
    else:
        bloc_wifi = ('<div class="col"><div class="num">1</div><h2>Je rejoins le Wi-Fi</h2>'
                     '<p class="secours">Nom et mot de passe non réglés : les écrire dans le poste de '
                     'commande (<code>/prof</code>).</p></div>')

    image_adresse = ('<img src="/qr.png" alt="QR de l\'adresse">' if qr_ok else
                     '<p class="secours">Pas de QR : lancer une fois <code>pip install qrcode[pil]</code>.</p>')
    bloc_adresse = ('<div class="col"><div class="num">2</div><h2>J\'ouvre la page</h2>' + image_adresse
                    + '<p class="secours">sinon, je tape <b>' + html.escape(url) + '</b></p></div>')

    # Le groupe ne prend une colonne que s'il est réglé ET montré : sinon la place va aux deux autres.
    bloc_groupe = ''
    if r.get('groupe_whatsapp') and qr_ok and r.get('afficher_whatsapp', True):
        nom_g = (r.get('nom_groupe') or '').strip()
        bloc_groupe = ('<div class="col"><div class="num">3</div><h2>' + (html.escape(nom_g) if nom_g else 'Le groupe de la classe')
                       + '</h2><img src="/qr-groupe.png" alt="QR du groupe WhatsApp">'
                       + '<p class="secours">je le scanne avec WhatsApp</p></div>')

    android = ('<div class="bande"><h3>&#128241; Android <span>Samsung, Pixel, Xiaomi, Oppo&hellip;</span></h3><ol>'
               '<li><b>Appareil photo</b> &rarr; QR n&deg;&nbsp;1 &rarr; <b>Se connecter au réseau</b></li>'
               '<li>&laquo;&nbsp;Pas d\'accès à Internet&nbsp;&raquo; &rarr; <b>OUI, rester connecté</b> (c\'est normal)</li>'
               '<li><b>Appareil photo</b> &rarr; QR n&deg;&nbsp;2 &rarr; je touche le lien</li>'
               '</ol></div>')
    iphone = ('<div class="bande"><h3>&#127823; iPhone</h3><ol>'
              '<li><b>Appareil photo</b> &rarr; QR n&deg;&nbsp;1 &rarr; bandeau <b>Rejoindre le réseau</b></li>'
              '<li>&laquo;&nbsp;Sécurité faible&nbsp;&raquo; &rarr; sans importance, je continue</li>'
              '<li><b>Appareil photo</b> &rarr; QR n&deg;&nbsp;2 &rarr; je touche le bandeau</li>'
              '</ol></div>')

    pied = ('<div class="pied">'
            '<span class="p-alerte">&#9888;&#65039; <b>Mon écran ne doit pas s\'éteindre</b> &mdash; '
            '<b>Android</b> : Réglages &rsaquo; Affichage &rsaquo; Mise en veille &rsaquo; le plus long. '
            '<b>iPhone</b> : Réglages &rsaquo; Luminosité &rsaquo; Verrouillage auto &rsaquo; <b>Jamais</b>.</span>'
            '<span class="p-secours">&#128260; <b>Perdu&nbsp;?</b> je rescanne le QR n&deg;&nbsp;1 puis le n&deg;&nbsp;2 &mdash; '
            'ils restent affichés toute la séance.</span></div>')

    return (CSS_PROJETER + '<title>Se connecter au test</title>'
            '<div class="ecran">'
            '<h1>Séance sur téléphone &mdash; ce que je fais, dans l\'ordre</h1>'
            + alerte_borne
            + '<div class="cols">' + bloc_wifi + bloc_adresse + bloc_groupe + '</div>'
            + '<div class="bandes">' + android + iphone + '</div>'
            + pied + '</div>')


PUBLIC = 'https://frigorx.github.io/test-accueil-mfer/'
PAGES_PROF = ('/prof', '/projeter', '/resultats', '/cartographie', '/qr', '/bilan', '/engagements')   # ne s'ouvrent que sur le PC du professeur
CSS_PROJETER = ('<meta charset="utf-8"><meta http-equiv="refresh" content="60">'
                '<style>*{box-sizing:border-box}'
                'html,body{height:100%;margin:0;overflow:hidden}'
                'body{font-family:Calibri,Segoe UI,sans-serif;background:#1b3a63;color:#fff;text-align:center}'
                '.ecran{height:100%;display:flex;flex-direction:column;gap:1.1vh;padding:1.4vh 1.2vw}'
                'h1{font-size:2.6vh;margin:0;flex:0 0 auto}'
                'h2{font-size:2.5vh;margin:0 0 .4vh}'
                'h3{font-size:2.2vh;margin:0 0 .6vh;color:#ffd9a8}h3 span{font-weight:normal;font-size:1.7vh;opacity:.8}'
                'code{font-family:Consolas,monospace}b{color:#fff}'
                '.cols{flex:1 1 auto;display:flex;gap:1.2vw;justify-content:center;min-height:0}'
                '.col{flex:1 1 0;max-width:34vw;background:rgba(255,255,255,.07);border-radius:1.4vh;'
                'padding:1.6vh 1vw .9vh;position:relative;display:flex;flex-direction:column;align-items:center;min-height:0}'
                '.num{position:absolute;top:-1.6vh;left:50%;transform:translateX(-50%);width:3.4vh;height:3.4vh;'
                'line-height:3.4vh;border-radius:50%;background:#ffd9a8;color:#1b3a63;font-size:2.1vh;font-weight:bold}'
                '.nom{font-size:2.6vh;font-weight:bold;background:#fff;color:#1b3a63;display:inline-block;'
                'padding:.5vh 1.4vh;border-radius:1vh;margin:.6vh 0 .3vh;word-break:break-all}'
                'img{flex:1 1 auto;min-height:0;width:auto;max-width:100%;object-fit:contain;'
                'margin:.5vh auto;border-radius:.8vh;background:#fff;padding:.5vh}'
                '.secours{font-size:1.7vh;opacity:.85;margin:.3vh 0 0;line-height:1.3}'
                '.bandes{flex:0 0 auto;display:flex;gap:1.2vw;justify-content:center}'
                '.bande{flex:1 1 0;max-width:42vw;background:rgba(255,255,255,.07);border-radius:1.4vh;padding:1vh 1.2vw}'
                '.bande ol{text-align:left;font-size:1.85vh;line-height:1.35;margin:0;padding-left:2.2vh}'
                '.bande li{margin-bottom:.3vh}'
                '.alerte-borne{flex:0 0 auto;font-size:2vh;line-height:1.35;background:#a11b1b;'
                'border:.3vh solid #ffd9a8;border-radius:1vh;padding:.8vh 1.2vw;margin:0}'
                '.pied{flex:0 0 auto;display:flex;gap:1.2vw;justify-content:center;font-size:1.7vh;line-height:1.3}'
                '.p-alerte{flex:1 1 0;background:#8a3b12;border-radius:1vh;padding:.7vh 1vw;text-align:left}'
                '.p-secours{flex:0 1 32vw;background:rgba(255,255,255,.1);border-radius:1vh;padding:.7vh 1vw;text-align:left}'
                '</style>')
CSS_PROF = ('<meta charset="utf-8"><style>body{font-family:Calibri,Segoe UI,sans-serif;margin:0;padding:18px 26px;color:#22303f;background:#f5f8fc}'
            'h1{color:#1b3a63;font-size:28px;margin:0 0 4px}h2{color:#1b3a63;font-size:20px;margin:22px 0 8px}.etat{font-size:16px;color:#555;margin:0}'
            '.grille{display:flex;flex-wrap:wrap;gap:12px}.b{flex:1;min-width:240px;max-width:420px;color:#fff;text-decoration:none;border-radius:12px;padding:14px 16px;display:flex;flex-direction:column;gap:4px}'
            '.b b{font-size:20px}.b span{font-size:14px;opacity:.9}.mono{font-family:Consolas,monospace;font-size:15px;line-height:1.7}'
            'code{font-family:Consolas,monospace;background:#e8eef6;padding:1px 4px;border-radius:3px}.pied{color:#777;font-size:14px;margin-top:26px}a{color:#1b3a63}</style>')


def lisible(wa):
    """33649243008 → 06 49 24 30 08 (numéro français) ; sinon +numéro."""
    n = '0' + wa[2:] if wa.startswith('33') and len(wa) == 11 else '+' + wa
    return ' '.join(n[i:i + 2] for i in range(0, len(n), 2)) if n.startswith('0') else n


def liens_publics():
    """Les deux tests en ligne ; le numéro WhatsApp du professeur voyage dans le lien (?wa=), jamais dans les pages."""
    wa = str(reglages().get('whatsapp') or '')
    q = '?wa=' + wa if wa.isdigit() else ''
    return [("Test d'accueil", 'sécurité, règlement, règles de la classe · noté sur 20 · 1 h', PUBLIC + q),
            ('Positionnement', 'six niveaux, non noté · le niveau atteint et mes compétences', PUBLIC + 'positionnement.html' + q)]


def qr_data(texte):
    """Le QR code en donnée incorporable (data:), ou '' sans le module qrcode."""
    import base64
    png = qr_png(texte)
    return 'data:image/png;base64,' + base64.b64encode(png).decode('ascii') if png else ''


def page_projeter_en_ligne():
    """À projeter quand les élèves ont Internet (4G ou Wi-Fi du lycée) : les deux QR codes des tests en ligne."""
    wa = str(reglages().get('whatsapp') or '')
    cols = ''
    for titre, sous, url in liens_publics():
        img = qr_data(url)
        cols += ('<div class="col"><h2>%s</h2><p class="pas" style="font-size:18px">%s</p>%s<div class="adr" style="font-size:22px">%s</div></div>'
                 % (html.escape(titre), html.escape(sous),
                    '<img src="%s" alt="QR code">' % img if img else '<p class="pas">(pas de QR code : module qrcode absent)</p>',
                    html.escape(url.replace('https://', '').split('?')[0])))
    num = ('WhatsApp du professeur : <b>%s</b>' % html.escape(lisible(wa))) if wa.isdigit() else "Numéro WhatsApp non réglé (reglages.json) : la capture d'écran suffit."
    return (CSS_PROJETER + '<title>Les tests en ligne</title>'
            '<h1>Pour faire le test sur mon téléphone (4G ou Wi-Fi)</h1><div class="cols">%s</div>'
            '<ol class="pas" style="text-align:left;display:inline-block;margin:14px auto 0"><li>Je scanne le QR code, ou je tape l\'adresse.</li>'
            '<li>Mon téléphone ne s\'éteint pas tout seul : verrouillage automatique sur « Jamais ».</li>'
            '<li>Mon nom, ma classe, « Commencer ».</li><li>Je réponds. <b>Je ne quitte pas la page</b> : chaque sortie est comptée.</li>'
            '<li>À la fin : capture d\'écran du cadre, puis « Envoyer par WhatsApp au professeur ».</li></ol>'
            '<p class="pas">%s</p>' % (cols, num))


def url_surveillance():
    """L'adresse de la page de surveillance pour le téléphone du professeur, avec son code ; vide sans code."""
    code = str(reglages().get('code_prof') or '')
    return adresse_eleves('surveillance?code=' + code) if code else ''


def page_prof(ok=False):
    """Le poste de commande du professeur (sur son PC seulement) : je règle, je projette, je suis la classe."""
    import time
    r = reglages()
    vivants = sum(1 for d in SUIVI.values() if time.time() - d.get('_t', 0) < 90)
    ip = (adresses() or ['localhost'])[0]

    def bouton(href, titre, sous, couleur='#1b3a63'):
        return ('<a class="b" href="%s" target="_blank" style="background:%s"><b>%s</b><span>%s</span></a>'
                % (href, couleur, html.escape(titre), html.escape(sous)))
    def champ(nom, titre, aide, valeur, large=False):
        return ('<label class="ch"><b>%s</b><span>%s</span>%s</label>'
                % (html.escape(titre), html.escape(aide),
                   ('<textarea name="%s" rows="8" placeholder="un élève par ligne">%s</textarea>' % (nom, html.escape(valeur))) if large else
                   ('<input name="%s" value="%s" autocomplete="off">' % (nom, html.escape(valeur)))))
    classe = r.get('classe') or []
    active = (r.get('nom_classe') or '').strip()
    autres_classes = len(lire_resultats(True)) - len(lire_resultats())
    etat = ('%d résultat(s) reçu(s)%s · %d téléphone(s) connecté(s) en ce moment · %d élève(s) dans la liste'
            % (len(lire_resultats()),
               (' pour <b>%s</b>' % html.escape(active)) if active else '',
               vivants, len(classe))
            + ((' · %d résultat(s) gardé(s) pour les autres classes' % autres_classes) if autres_classes else ''))

    # Mes classes : un bouton chacune, jamais un menu déroulant. Changer de classe range la
    # précédente (élèves, groupe WhatsApp) et sort celle qu'on demande : rien n'est perdu.
    autres = [n for n in classes_connues(r) if n != active]
    bascules = ''.join('<button type="submit" name="basculer" value="%s" class="cl">%s</button>'
                       % (html.escape(n, True), html.escape(n)) for n in autres)
    barre = ('<div class="classes"><b>Classe du jour</b>'
             + ('<span class="cl actif">%s</span>' % html.escape(active) if active else
                '<span class="vide">aucune classe enregistrée pour l\'instant</span>')
             + ('<span class="fleche">changer pour</span>' if bascules else '')
             + bascules
             + ('<button type="submit" name="supprimer" value="%s" class="cl sup" '
                'onclick="return confirm(\'Retirer la classe %s de la liste ? Ses résultats déjà reçus sont gardés.\')"'
                '>Retirer « %s »</button>' % (html.escape(active, True), html.escape(active, True), html.escape(active))
                if active else '')
             + '<span class="aide">Une classe se choisit d\'un clic et ne se retape jamais. '
               'Pour en ajouter une : le champ « Ajouter une classe » juste dessous, une seule fois.</span></div>')

    coche = ('<label class="ch coche"><input type="checkbox" name="afficher_whatsapp" value="1"%s> '
             '<b>Montrer le groupe WhatsApp aux élèves</b>'
             '<span>Décoché, le groupe n\'apparaît ni sur leur accueil ni sur la page projetée. '
             'Le lien reste gardé pour cette classe.</span></label>'
             % (' checked' if r.get('afficher_whatsapp') else ''))

    # Tout passe par des %s (barre et case comprises) : en Python « % » lie plus fort que « + »,
    # et une concaténation mêlée au formatage ne remplacerait que le dernier morceau.
    # Sans liste, les téléphones retombent sur la saisie libre — et c'est par là que sont
    # arrivés « Mini sicario » et « Waayyyli » le 22/09. On le dit avant la séance, pas après.
    alerte_liste = ''
    if not classe:
        alerte_liste = ('<p class="alerte-liste">&#9888;&#65039; <b>Aucune liste d\'élèves pour cette classe.</b> '
                        'Les téléphones laisseront chacun <b>taper</b> son nom, et vous récupérerez des pseudos '
                        'impossibles à rattacher. Collez la liste ci-dessous avant de lancer la séance.</p>')
    form = (alerte_liste + '<form method="post" action="/reglages" class="form">%s%s%s%s%s%s%s%s%s%s'
            '<button type="submit">Enregistrer mes réglages</button>'
            '<p class="etat">Tout reste sur ce PC, dans <code>reglages.json</code>, jamais publié. Adresse des téléphones : <code>%s</code>%s</p></form>'
            % (barre,
               champ('nouvelle_classe', 'Ajouter une classe à la liste',
                     'seulement pour en créer une nouvelle : j\'écris son nom une fois, par exemple 2A CAP IFCA, et elle '
                     'devient un bouton là-haut. Ensuite je la choisis d\'un clic, sans jamais la retaper. '
                     'Laisser vide pour enregistrer la classe en cours.', ''),
               champ('classe', 'La liste de cette classe', 'collée depuis École Directe, un nom par ligne : les résultats se rangent élève par élève. Un élève arrive en cours d\'année ? une ligne de plus.', '\n'.join(classe), True),
               champ('groupe_whatsapp', 'Lien du groupe WhatsApp de CETTE classe', "chaque classe a le sien. Dans le groupe : Inviter via un lien, copier. C'est ce lien qui fabrique le QR code.", r.get('groupe_whatsapp') or ''),
               champ('nom_groupe', 'Nom du groupe, tel que les élèves le verront', 'par exemple MFER 26-27 ; laissé vide, on écrit simplement « le groupe WhatsApp de la classe »', r.get('nom_groupe') or ''),
               coche,
               champ('ssid', 'Nom du Wi-Fi de classe', 'celui du routeur : inerWeb-Classe. Commun à toutes les classes.', r.get('ssid') or ''),
               champ('motdepasse', 'Mot de passe du Wi-Fi', 'il fait le QR code que les téléphones scannent', r.get('motdepasse') or ''),
               champ('whatsapp', 'Mon numéro WhatsApp', 'format 33612345678, pour le bouton « envoyer au professeur » des tests en ligne', str(r.get('whatsapp') or '')),
               champ('code_prof', 'Code pour surveiller depuis mon téléphone', 'quatre chiffres ou plus, à moi seul : la page de surveillance s\'ouvre sur mon téléphone avec ce code', str(r.get('code_prof') or '')),
               html.escape('http://%s:%d/' % (ip, PORT)),
               ' — <b style="color:#0e7a5f">réglages enregistrés ✓</b>' if ok else ''))
    return (CSS_PROF + '<style>.form{background:#fff;border:1px solid #d8dee6;border-radius:12px;padding:16px 18px;max-width:760px}'
            '.ch{display:block;margin:0 0 12px}.ch b{display:block;color:#1b3a63;font-size:16px}.ch span{display:block;color:#666;font-size:13px;margin:0 0 4px}'
            '.ch input,.ch textarea{width:100%%;font:inherit;font-size:16px;padding:8px 10px;border:1.5px solid #c9d3df;border-radius:8px;box-sizing:border-box}'
            '.form button{font:inherit;font-size:17px;font-weight:bold;background:#0e7a5f;color:#fff;border:none;border-radius:10px;padding:12px 20px;cursor:pointer}'
            '.classes{display:flex;flex-wrap:wrap;align-items:center;gap:8px;background:#eef3f9;border-radius:10px;padding:10px 12px;margin:0 0 16px}'
            '.classes>b{color:#1b3a63;font-size:15px;margin-right:4px}'
            '.form button.cl,.cl{font:inherit;font-size:15px;font-weight:normal;background:#fff;color:#1b3a63;'
            'border:1.5px solid #c9d3df;border-radius:20px;padding:6px 14px;cursor:pointer}'
            '.cl.actif{background:#1b3a63;color:#fff;border-color:#1b3a63;font-weight:bold;cursor:default}'
            '.form button.cl.sup{background:#fff;color:#a11b1b;border-color:#e0bcbc}'
            '.classes .vide{color:#777;font-size:14px;font-style:italic}'
            '.classes .fleche{color:#666;font-size:13px;margin:0 2px 0 8px}'
            '.classes .aide{flex-basis:100%%;color:#666;font-size:13px}'
            '.alerte-liste{background:#fdf3f3;border:2px solid #b3261e;border-radius:10px;padding:12px 16px;'
            'max-width:760px;margin:0 0 14px;color:#b3261e;font-size:16px;line-height:1.45}'
            '.ch.coche{background:#f5f8fc;border:1.5px solid #d8dee6;border-radius:8px;padding:10px 12px}'
            '.ch.coche input{width:auto;margin-right:6px}.ch.coche b{display:inline}</style>'
            '<title>Ma séance sur téléphone — poste du professeur</title>'
            '<h1>Ma séance sur téléphone</h1><p class="etat">%s</p>'
            '<h2>1. Je règle (une fois)</h2>%s'
            '<h2>2. Je projette au tableau</h2><div class="grille">%s</div>'
            '<h2>3. Je suis la classe</h2><div class="grille">%s%s%s%s%s%s</div>%s'
            '<h2>4. Si besoin</h2><div class="grille">%s%s%s</div>'
            '<p class="pied">Les élèves scannent le QR, l\'accueil leur donne les activités dans l\'ordre. Pour arrêter : fermer la fenêtre noire. Les résultats restent dans %s.</p>'
            % (etat, form,
               bouton('/projeter', 'Projeter : Wi-Fi, adresse, groupe WhatsApp', 'les trois QR codes au tableau ; les résultats arrivent tout seuls sur ce PC', '#128c7e'),
               bouton('/bilan', 'Bilan du jour : notes et alertes', 'une ligne par élève : les trois notes, la note du jour (le meilleur vaut 20), qui n\'a pas joué le jeu, qui a raté les règles et quelles questions', '#1b3a63'),
               bouton('/surveillance', 'Surveiller la classe', 'qui est en ligne, qui est hors ligne depuis combien de temps (rouge après une minute), qui a fini', '#b3261e'),
               bouton('/resultats', 'Qui a fait quoi, résultats en direct', 'élève par élève, activité par activité, les notes'),
               bouton('/cartographie', 'Cartographie des compétences', 'élèves × compétences, de 1 à 4'),
               bouton('/engagements', 'Engagements sur les règles', "qui a coché « je m'engage à respecter les règles », quand — et qui ne l'a pas fait", '#6b3fa0'),
               bouton('/resultats.csv', 'Tableur des résultats', 'CSV pour Excel', '#555'),
               (('<div class="form" style="margin-top:10px"><b style="color:#1b3a63">La même surveillance sur mon téléphone</b> (connecté au Wi-Fi de classe) : je scanne, ou je tape <code>%s</code><br><img src="/qr-surveillance.png" alt="QR surveillance" style="width:180px;margin-top:6px"></div>' % html.escape(url_surveillance()))
                if url_surveillance() else '<p class="etat">Pour surveiller depuis mon téléphone : remplir le code dans les réglages ci-dessus.</p>'),
               bouton('/', 'Voir ce que voient les élèves', "l'accueil des activités, sur ce PC", '#c8511b'),
               bouton('/projeter-en-ligne', 'Les tests en ligne (sans ce PC)', "QR codes des versions en ligne : l'élève envoie une capture d'écran", '#555'),
               bouton('/cartographie.csv', 'Tableur de la cartographie', 'CSV pour Excel', '#555'),
               html.escape(DOSSIER)))


class Gestionnaire(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ICI, **k)

    def log_message(self, fmt, *args):  # journal court : seulement les résultats reçus
        if args and 'POST /resultat' in args[0]:
            sys.stdout.write('%s %s\n' % (datetime.now().strftime('%H:%M:%S'), args[0]))

    def end_headers(self):   # jamais de cache : les téléphones voient toujours la dernière version des pages
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def repondre(self, code, corps, type_='text/html; charset=utf-8'):
        b = corps.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', type_)
        self.send_header('Content-Length', str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if any(self.path.startswith(p) for p in PAGES_PROF) and self.client_address[0] not in ('127.0.0.1', '::1'):
            self.repondre(403, 'Page du professeur : elle ne s\'ouvre que sur son PC.')
            return
        if self.path.startswith('/prof'):
            self.repondre(200, page_prof('ok=1' in self.path))
            return
        if self.path.startswith('/surveillance'):
            from urllib.parse import urlparse, parse_qs
            code = (parse_qs(urlparse(self.path).query).get('code') or [''])[0]
            attendu = str(reglages().get('code_prof') or '')
            if self.client_address[0] not in ('127.0.0.1', '::1') and not (attendu and code == attendu):
                self.repondre(403, "Page du professeur. Sur le téléphone : l\'adresse avec le code, donnée par le poste de commande.")
                return
            self.repondre(200, page_surveillance())
            return
        if self.path.startswith('/projeter-en-ligne'):
            self.repondre(200, page_projeter_en_ligne())
            return
        if self.path.startswith('/projeter'):
            self.repondre(200, page_projeter())
            return
        if self.path.startswith(('/qr-wifi.png', '/qr.png', '/qr-groupe.png', '/qr-surveillance.png')):
            png = qr_wifi() if 'wifi' in self.path else qr_groupe() if 'groupe' in self.path else qr_png(url_surveillance()) if 'surveillance' in self.path else qr_png(reglages().get('adresse') or None)
            if not png:
                self.repondre(404, 'pas de QR : installer le module qrcode (pip install qrcode[pil])')
                return
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(png)))
            self.end_headers()
            self.wfile.write(png)
            return
        if self.path.startswith('/bilan.csv'):
            b = ('\ufeff' + csv_bilan(lire_resultats())).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="bilan-du-jour.csv"')
            self.send_header('Content-Length', str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        if self.path.startswith('/engagements'):
            self.repondre(200, page_engagements())
            return
        if self.path.startswith('/bilan'):
            self.repondre(200, page_bilan(lire_resultats()))
            return
        if self.path.startswith('/cartographie.csv'):
            codes, eleves = cartographie(lire_resultats())
            b = ('﻿' + csv_cartographie(codes, eleves)).encode('utf-8')
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="cartographie.csv"')
            self.send_header('Content-Length', str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        if self.path.startswith('/cartographie'):
            codes, eleves = cartographie(lire_resultats())
            self.repondre(200, page_cartographie(codes, eleves))
            return
        if self.path.startswith('/resultats.csv'):
            if not os.path.exists(CSV):
                ecrire_csv(lire_resultats())
            with io.open(CSV, 'rb') as f:
                b = f.read()
            self.send_response(200)
            self.send_header('Content-Type', 'text/csv; charset=utf-8')
            self.send_header('Content-Disposition', 'attachment; filename="test-accueil.csv"')
            self.send_header('Content-Length', str(len(b)))
            self.end_headers()
            self.wfile.write(b)
            return
        if self.path.startswith('/resultats'):
            self.repondre(200, page_resultats(lire_resultats()))
            return
        if self.path.split('?')[0] == '/sw.js':
            # Coupe-circuit : un vieux service worker d'inerWeb Édu (scope /, script /sw.js) est encore enregistré sur localhost:8765 dans certains
            # navigateurs et affiche « Pas de réseau — inerWeb Édu ». À sa prochaine vérification il charge ceci, se désinscrit, vide ses caches et recharge la page.
            self.repondre(200, "self.addEventListener('install', () => self.skipWaiting());self.addEventListener('activate', e => e.waitUntil(self.registration.unregister().then(() => caches.keys()).then(ks => Promise.all(ks.map(k => caches.delete(k)))).then(() => self.clients.matchAll({type: 'window'})).then(cs => cs.forEach(c => c.navigate(c.url)))));", 'application/javascript; charset=utf-8')
            return
        if self.path.startswith('/classe.json'):
            # La liste de la classe du jour, pour que l'élève CHOISISSE son nom au lieu de le taper.
            # Servie seulement sur le Wi-Fi de la classe, jamais publiée. Vide = les pages
            # retombent d'elles-mêmes sur la saisie libre (cas de la version en ligne).
            r = reglages()
            self.repondre(200, json.dumps({'classe': (r.get('nom_classe') or '').strip(),
                                           'eleves': [n for n in (r.get('classe') or []) if str(n).strip()]},
                                          ensure_ascii=False), 'application/json')
            return
        if self.path.startswith('/aide'):
            self.repondre(200, page_aide())
            return
        if self.path.startswith('/groupe'):
            lien = reglages().get('groupe_whatsapp')
            if not lien:
                self.repondre(404, "Pas de groupe réglé : écrire groupe_whatsapp dans reglages.json, à côté du serveur.")
                return
            self.send_response(302)
            self.send_header('Location', lien)
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        if self.path.split('?')[0] in ('/', ''):
            self.repondre(200, page_accueil())
            return
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith('/reglages'):
            if self.client_address[0] not in ('127.0.0.1', '::1'):
                self.repondre(403, 'Réglages : seulement sur le PC du professeur.')
                return
            from urllib.parse import parse_qs
            n = int(self.headers.get('Content-Length') or 0)
            form = parse_qs(self.rfile.read(n).decode('utf-8'), keep_blank_values=True)
            r = reglages()
            actuelle = (r.get('nom_classe') or '').strip()
            bascule = (form.get('basculer') or [''])[0].strip()
            supprimer = (form.get('supprimer') or [''])[0].strip()
            if bascule:                                   # bouton « passer à cette classe »
                archiver_classe(r, actuelle)
                charger_classe(r, bascule)
            elif supprimer:                               # bouton « supprimer cette classe »
                (r.setdefault('classes', {})).pop(supprimer, None)
                if supprimer == actuelle:                 # on retombe sur une classe restante, ou sur rien
                    restantes = sorted((r.get('classes') or {}).keys(), key=lambda s: s.lower())
                    charger_classe(r, restantes[0] if restantes else '')
            else:
                # Le nom de la classe active ne se retape JAMAIS : on la choisit par son bouton.
                # Un seul champ crée une classe, et il est vide par défaut — pas de classe fantôme
                # née d'une lettre changée par inadvertance.
                for k in ('ssid', 'motdepasse', 'whatsapp', 'groupe_whatsapp', 'nom_groupe', 'code_prof'):
                    r[k] = (form.get(k) or [''])[0].strip()
                r['whatsapp'] = re.sub(r'\D', '', r['whatsapp'])
                r['afficher_whatsapp'] = bool(form.get('afficher_whatsapp'))
                r['classe'] = [x.strip() for x in (form.get('classe') or [''])[0].splitlines() if x.strip()]
                archiver_classe(r, actuelle)          # ce que le formulaire montrait appartient à la classe en cours
                nouvelle = (form.get('nouvelle_classe') or [''])[0].strip()
                if nouvelle and nouvelle != actuelle:
                    charger_classe(r, nouvelle)       # la nouvelle naît vide : elle n'hérite de rien
                    archiver_classe(r, nouvelle)
            ecrire_reglages(r)
            self.send_response(303)
            self.send_header('Location', '/prof?ok=1')
            self.send_header('Content-Length', '0')
            self.end_headers()
            return
        if self.path.startswith('/suivi'):
            try:
                import time
                n = int(self.headers.get('Content-Length') or 0)
                d = json.loads(self.rfile.read(n).decode('utf-8') or '{}')
                if isinstance(d, dict) and d.get('nom'):
                    noter_signe_de_vie(d)
                self.repondre(200, '{"ok":true}', 'application/json')
            except Exception as e:
                self.repondre(400, json.dumps({'ok': False, 'erreur': str(e)}), 'application/json')
            return
        if self.path.startswith('/engagement'):
            try:
                n = int(self.headers.get('Content-Length') or 0)
                d = json.loads(self.rfile.read(n).decode('utf-8') or '{}')
                if not isinstance(d, dict) or not str(d.get('nom') or '').strip():
                    raise ValueError('engagement sans nom')
                quand = datetime.now()
                ligne = {'nom': str(d.get('nom')).strip(), 'note': d.get('note', ''), 'code': d.get('code', ''),
                         'texte': str(d.get('texte') or '').strip(),
                         'seance': str(reglages().get('nom_classe') or '').strip() or 'sans nom',
                         'quand': quand.isoformat(timespec='seconds'), 'ip': self.client_address[0]}
                os.makedirs(DOSSIER, exist_ok=True)
                with io.open(ENGAGEMENTS, 'a', encoding='utf-8') as f:
                    f.write(json.dumps(ligne, ensure_ascii=False) + '\n')
                self.repondre(200, json.dumps({'ok': True, 'quand': quand.strftime('%d/%m/%Y à %H h %M')},
                                              ensure_ascii=False), 'application/json')
            except Exception as e:
                self.repondre(400, json.dumps({'ok': False, 'erreur': str(e)}), 'application/json')
            return
        if not self.path.startswith('/resultat'):
            self.repondre(404, 'non')
            return
        try:
            n = int(self.headers.get('Content-Length') or 0)
            d = json.loads(self.rfile.read(n).decode('utf-8') or '{}')
            if not isinstance(d, dict) or not d.get('nom'):
                raise ValueError('résultat sans nom')
            d = dict(d)   # tout est gardé (dont la carte des compétences) ; le CSV n'en prend que les colonnes connues
            noter_signe_de_vie({'nom': d.get('nom'), 'classe': d.get('classe'), 'type': d.get('type') or 'accueil', 'sorties': d.get('sorties', 0)}, fini=True)
            d['recu'] = datetime.now().isoformat(timespec='seconds')
            d['ip'] = self.client_address[0]
            # Le poste de commande estampille la séance : c'est lui qui sait quelle classe passe, pas le téléphone.
            # Rien n'est jamais effacé du .jsonl — plusieurs classes cohabitent, et on retrouve chacune plus tard.
            d['seance'] = str(reglages().get('nom_classe') or '').strip() or 'sans nom'
            os.makedirs(DOSSIER, exist_ok=True)
            with io.open(JSONL, 'a', encoding='utf-8') as f:
                f.write(json.dumps(d, ensure_ascii=False) + '\n')
            ecrire_csv(lire_resultats())
            self.repondre(200, '{"ok":true}', 'application/json')
        except Exception as e:
            self.repondre(400, json.dumps({'ok': False, 'erreur': str(e)}), 'application/json')


def adresses():
    ips = []
    try:
        for ip in socket.gethostbyname_ex(socket.gethostname())[2]:
            if not ip.startswith('127.'):
                ips.append(ip)
    except OSError:
        pass
    try:  # l'adresse réellement utilisée pour sortir, si le PC a un réseau
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('10.255.255.255', 1))
        ip = s.getsockname()[0]
        s.close()
        if ip not in ips and not ip.startswith('127.'):
            ips.insert(0, ip)
    except OSError:
        pass
    ips.sort(key=lambda ip: not ip.startswith('192.168.8.'))   # le Wi-Fi de classe (routeur GL.iNet, LAN 192.168.8.x) d'abord
    return ips


if __name__ == '__main__':
    import webbrowser
    os.makedirs(DOSSIER, exist_ok=True)
    ouvrir = sys.argv[sys.argv.index('--ouvrir') + 1] if '--ouvrir' in sys.argv[:-1] else ''   # --ouvrir /prof : ouvre le navigateur
    print('=' * 64)
    print('  TEST DE RENTRÉE — serveur local (fermer la fenêtre pour arrêter)')
    print('=' * 64)
    print('  Poste de commande : http://127.0.0.1:%d/prof   (projeter, suivre, vérifier, régler)' % PORT)
    for ip in adresses() or ['(pas de réseau détecté)']:
        print('  Élèves, mode fermé : http://%s:%d/  et  /positionnement.html' % (ip, PORT))
    print('  À projeter : /projeter-en-ligne (QR des tests en ligne) · /projeter (Wi-Fi du PC et adresse locale)')
    print('  Professeur : /resultats · /cartographie · /resultats.csv · /cartographie.csv')
    print('  Résultats  : %s' % JSONL)
    print('=' * 64)
    try:   # déjà lancé ? (sous Windows, un second serveur se lierait au même port sans erreur)
        socket.create_connection(('127.0.0.1', PORT), timeout=0.5).close()
        deja = True
    except OSError:
        deja = False
    if deja:
        print('  Le serveur tourne déjà (port %d) : j\'ouvre seulement le poste de commande.' % PORT)
        if ouvrir:
            webbrowser.open('http://127.0.0.1:%d%s' % (PORT, ouvrir))   # 127.0.0.1 et non localhost : un ancien service worker (inerWeb Édu) traîne sur localhost:8765 dans le navigateur
        sys.exit(0)
    serveur = ThreadingHTTPServer(('0.0.0.0', PORT), Gestionnaire)
    if ouvrir:
        webbrowser.open('http://127.0.0.1:%d%s' % (PORT, ouvrir))   # 127.0.0.1 et non localhost : un ancien service worker (inerWeb Édu) traîne sur localhost:8765 dans le navigateur
    serveur.serve_forever()
