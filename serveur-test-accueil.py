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
PORT = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 8765
COLONNES = ['recu', 'type', 'nom', 'diplome', 'classe', 'niveau', 'niveau_nom', 'note', 'justes', 'total', 'sorties', 'arret', 'repondu',
            'minutes', 'code', 'competences', 'niveaux', 'tax', 'blocs', 'reponses', 'ip']


def lire_resultats():
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
    return lignes


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
]


def page_accueil():
    """L'accueil des téléphones : les activités dans l'ordre, un bouton chacune, le groupe WhatsApp si réglé."""
    r = reglages()
    boutons = list(ACTIVITES)
    if r.get('groupe_whatsapp'):
        boutons.append(('/groupe', 'Rejoindre le groupe WhatsApp de la classe', 'ouvre WhatsApp · une seule fois', '#128c7e'))
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


def page_projeter():
    """La page à projeter au tableau : le Wi-Fi à rejoindre (QR), puis l'adresse en très gros (QR)."""
    r = reglages()
    url = r.get('adresse') or adresse_eleves()
    qr_ok = qr_png(url) is not None
    wifi = ''
    if r.get('ssid'):
        wifi = ('<div class="col"><h2>1. Le Wi-Fi</h2><div class="adr" style="font-size:36px">%s</div>%s<p class="pas">mot de passe : <b>%s</b></p></div>'
                % (html.escape(r['ssid']), '<img src="/qr-wifi.png" alt="QR Wi-Fi">' if qr_ok else '', html.escape(r.get('motdepasse', '') or '(aucun)')))
    else:
        wifi = '<div class="col"><h2>1. Le Wi-Fi</h2><p class="pas">Je me connecte au Wi-Fi du professeur.</p><p style="font-size:14px;opacity:.7">Pour afficher le nom, le mot de passe et leur QR code : écrire <code>reglages.json</code> à côté du serveur.</p></div>'
    adresse = ('<div class="col"><h2>2. L\'adresse</h2><div class="adr">%s</div>%s<p class="pas">l\'accueil me donne les activités dans l\'ordre. À la fin de chaque test, mon résultat part tout seul vers le PC du professeur.</p></div>'
               % (html.escape(url), '<img src="/qr.png" alt="QR adresse">' if qr_ok else
                  '<p style="font-size:18px;color:#ffd0bd">Pas de QR code : lancer une fois <code>pip install qrcode[pil]</code> (Test-de-rentree.cmd le fait s\'il y a Internet).</p>'))
    groupe = ''
    if r.get('groupe_whatsapp'):
        groupe = ('<div class="col"><h2>3. Le groupe WhatsApp de la classe</h2>%s<p class="pas">Je le scanne avec WhatsApp (appareil photo, ou « Scanner le code ») et je rejoins le groupe.</p></div>'
                  % ('<img src="/qr-groupe.png" alt="QR groupe WhatsApp">' if qr_ok else ''))
    return (CSS_PROJETER + '<title>Se connecter au test</title>'
            '<h1>Pour faire le test sur mon téléphone</h1><div class="cols">%s%s%s</div>'
            '<p class="pas">Mon téléphone ne s\'éteint pas tout seul : verrouillage automatique sur « Jamais ». Un écran éteint compte comme une sortie.</p>'
            '<p style="font-size:16px;opacity:.85">L\'accueil donne les activités dans l\'ordre : test d\'accueil, où j\'en suis, manomètres, jeux &nbsp;·&nbsp; Le professeur suit tout sur http://localhost:%d/resultats</p>'
            '<p style="font-size:14px;opacity:.7">Si l\'adresse ne répond pas, essayer : %s (point d\'accès mobile de Windows : 192.168.137.1 en général)</p>'
            % (wifi, adresse, groupe, PORT, html.escape(' · '.join('http://%s:%d/' % (ip, PORT) for ip in adresses()) or '—')))


PUBLIC = 'https://frigorx.github.io/test-accueil-mfer/'
PAGES_PROF = ('/prof', '/projeter', '/resultats', '/cartographie', '/qr', '/bilan')   # ne s'ouvrent que sur le PC du professeur
CSS_PROJETER = ('<meta charset="utf-8"><meta http-equiv="refresh" content="60">'
                '<style>body{font-family:Calibri,Segoe UI,sans-serif;margin:0;background:#1b3a63;color:#fff;text-align:center;padding:18px}'
                'h1{font-size:30px;margin:6px 0 14px}h2{font-size:24px;margin:4px 0 8px}code{font-family:Consolas,monospace}'
                '.cols{display:flex;gap:24px;justify-content:center;flex-wrap:wrap}.col{flex:1;min-width:320px;max-width:640px;background:rgba(255,255,255,.06);border-radius:16px;padding:14px}'
                '.adr{font-size:40px;font-weight:bold;background:#fff;color:#1b3a63;display:inline-block;padding:10px 22px;border-radius:14px;margin:8px 0;letter-spacing:.03em;word-break:break-all}'
                'img{width:min(38vh,90%);display:block;margin:8px auto;border-radius:10px}.pas{font-size:22px;margin:6px 0}</style>')
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
    etat = ('%d résultat(s) reçu(s) · %d téléphone(s) connecté(s) en ce moment · %d élève(s) dans la liste'
            % (len(lire_resultats()), vivants, len(classe)))
    form = ('<form method="post" action="/reglages" class="form">%s%s%s%s%s%s'
            '<button type="submit">Enregistrer mes réglages</button>'
            '<p class="etat">Tout reste sur ce PC, dans <code>reglages.json</code>, jamais publié. Adresse des téléphones : <code>%s</code>%s</p></form>'
            % (champ('ssid', 'Nom du Wi-Fi de classe', 'celui du routeur : inerWeb-Classe', r.get('ssid') or ''),
               champ('motdepasse', 'Mot de passe du Wi-Fi', 'il fait le QR code que les téléphones scannent', r.get('motdepasse') or ''),
               champ('whatsapp', 'Mon numéro WhatsApp', 'format 33612345678, pour le bouton « envoyer au professeur » des tests en ligne', str(r.get('whatsapp') or '')),
               champ('groupe_whatsapp', 'Lien du groupe WhatsApp de la classe', "dans le groupe : Inviter via un lien, copier", r.get('groupe_whatsapp') or ''),
               champ('code_prof', 'Code pour surveiller depuis mon téléphone', 'quatre chiffres ou plus, à moi seul : la page de surveillance s\'ouvre sur mon téléphone avec ce code', str(r.get('code_prof') or '')),
               champ('classe', 'La liste de ma classe', 'collée depuis École Directe, un nom par ligne : les résultats se rangent élève par élève', '\n'.join(classe), True),
               html.escape('http://%s:%d/' % (ip, PORT)),
               ' — <b style="color:#0e7a5f">réglages enregistrés ✓</b>' if ok else ''))
    return (CSS_PROF + '<style>.form{background:#fff;border:1px solid #d8dee6;border-radius:12px;padding:16px 18px;max-width:760px}'
            '.ch{display:block;margin:0 0 12px}.ch b{display:block;color:#1b3a63;font-size:16px}.ch span{display:block;color:#666;font-size:13px;margin:0 0 4px}'
            '.ch input,.ch textarea{width:100%%;font:inherit;font-size:16px;padding:8px 10px;border:1.5px solid #c9d3df;border-radius:8px;box-sizing:border-box}'
            '.form button{font:inherit;font-size:17px;font-weight:bold;background:#0e7a5f;color:#fff;border:none;border-radius:10px;padding:12px 20px;cursor:pointer}</style>'
            '<title>Ma séance sur téléphone — poste du professeur</title>'
            '<h1>Ma séance sur téléphone</h1><p class="etat">%s</p>'
            '<h2>1. Je règle (une fois)</h2>%s'
            '<h2>2. Je projette au tableau</h2><div class="grille">%s</div>'
            '<h2>3. Je suis la classe</h2><div class="grille">%s%s%s%s%s</div>%s'
            '<h2>4. Si besoin</h2><div class="grille">%s%s%s</div>'
            '<p class="pied">Les élèves scannent le QR, l\'accueil leur donne les activités dans l\'ordre. Pour arrêter : fermer la fenêtre noire. Les résultats restent dans %s.</p>'
            % (etat, form,
               bouton('/projeter', 'Projeter : Wi-Fi, adresse, groupe WhatsApp', 'les trois QR codes au tableau ; les résultats arrivent tout seuls sur ce PC', '#128c7e'),
               bouton('/bilan', 'Bilan du jour : notes et alertes', 'une ligne par élève : les trois notes, la note du jour (le meilleur vaut 20), qui n\'a pas joué le jeu, qui a raté les règles et quelles questions', '#1b3a63'),
               bouton('/surveillance', 'Surveiller la classe', 'qui est en ligne, qui est hors ligne depuis combien de temps (rouge après une minute), qui a fini', '#b3261e'),
               bouton('/resultats', 'Qui a fait quoi, résultats en direct', 'élève par élève, activité par activité, les notes'),
               bouton('/cartographie', 'Cartographie des compétences', 'élèves × compétences, de 1 à 4'),
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
            for k in ('ssid', 'motdepasse', 'whatsapp', 'groupe_whatsapp', 'code_prof'):
                r[k] = (form.get(k) or [''])[0].strip()
            r['whatsapp'] = re.sub(r'\D', '', r['whatsapp'])
            r['classe'] = [x.strip() for x in (form.get('classe') or [''])[0].splitlines() if x.strip()]
            io.open(os.path.join(ICI, 'reglages.json'), 'w', encoding='utf-8').write(json.dumps(r, ensure_ascii=False, indent=1))
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
