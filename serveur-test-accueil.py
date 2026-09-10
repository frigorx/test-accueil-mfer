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
import csv, html, io, json, os, socket, sys
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


SUIVI = {}   # qui est connecté en ce moment : clé nom|classe → dernier signe de vie


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


def page_resultats(lignes):
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


def qr_png():
    """Le QR code de l'adresse élèves, si le module qrcode est installé (pip install qrcode[pil]) ; sinon None."""
    try:
        import qrcode
    except ImportError:
        return None
    buf = io.BytesIO()
    qrcode.make(adresse_eleves(), box_size=12, border=2).save(buf, format='PNG')
    return buf.getvalue()


def page_projeter():
    """La page à projeter au tableau : l'adresse en très gros, le QR code s'il est possible."""
    url = adresse_eleves()
    qr = qr_png()
    corps = ('<img src="/qr.png" alt="QR code" style="width:min(60vh,60vw)">' if qr else
             '<p style="font-size:22px;color:#c9451a">Pas de QR code : sur ce PC, lancer une fois <code>pip install qrcode[pil]</code> puis relancer le serveur. En attendant, les élèves tapent l\'adresse.</p>')
    return ('<meta charset="utf-8"><meta http-equiv="refresh" content="60"><title>Se connecter au test</title>'
            '<style>body{font-family:Calibri,Segoe UI,sans-serif;margin:0;background:#1b3a63;color:#fff;text-align:center;padding:24px}'
            'h1{font-size:34px;margin:10px 0}code{font-family:Consolas,monospace}.adr{font-size:48px;font-weight:bold;background:#fff;color:#1b3a63;'
            'display:inline-block;padding:14px 28px;border-radius:14px;margin:14px 0;letter-spacing:.03em}.pas{font-size:24px;margin:8px 0}</style>'
            '<h1>Je me connecte au Wi-Fi du professeur, puis j\'ouvre :</h1><div class="adr">%s</div><br>%s'
            '<p class="pas">1. Wi-Fi du professeur &nbsp;·&nbsp; 2. cette adresse dans le navigateur &nbsp;·&nbsp; 3. mon nom, ma classe, je commence</p>'
            '<p style="font-size:16px;opacity:.85">Positionnement : %spositionnement.html &nbsp;·&nbsp; Le professeur suit tout sur http://localhost:%d/resultats</p>'
            '<p style="font-size:14px;opacity:.7">Si cette adresse ne répond pas, essayer : %s (avec le point d\'accès mobile de Windows, c\'est en général 192.168.137.1)</p>'
            % (html.escape(url), corps, html.escape(url), PORT, html.escape(' · '.join('http://%s:%d/' % (ip, PORT) for ip in adresses()) or '—')))


class Gestionnaire(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ICI, **k)

    def log_message(self, fmt, *args):  # journal court : seulement les résultats reçus
        if args and 'POST /resultat' in args[0]:
            sys.stdout.write('%s %s\n' % (datetime.now().strftime('%H:%M:%S'), args[0]))

    def repondre(self, code, corps, type_='text/html; charset=utf-8'):
        b = corps.encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', type_)
        self.send_header('Content-Length', str(len(b)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith('/projeter'):
            self.repondre(200, page_projeter())
            return
        if self.path.startswith('/qr.png'):
            png = qr_png()
            if not png:
                self.repondre(404, 'pas de QR : installer le module qrcode (pip install qrcode[pil])')
                return
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', str(len(png)))
            self.end_headers()
            self.wfile.write(png)
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
        if self.path in ('/', ''):
            self.path = '/index.html'
        return super().do_GET()

    def do_POST(self):
        if self.path.startswith('/suivi'):
            try:
                import time
                n = int(self.headers.get('Content-Length') or 0)
                d = json.loads(self.rfile.read(n).decode('utf-8') or '{}')
                if isinstance(d, dict) and d.get('nom'):
                    d['_t'] = time.time()
                    SUIVI['%s|%s' % (d.get('nom'), d.get('classe'))] = d
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
    return ips


if __name__ == '__main__':
    os.makedirs(DOSSIER, exist_ok=True)
    print('=' * 64)
    print('  TEST D\'ACCUEIL — serveur local (Ctrl+C pour arrêter)')
    print('=' * 64)
    for ip in adresses() or ['(pas de réseau détecté)']:
        print('  Élèves     : http://%s:%d/' % (ip, PORT))
    print('  Test d\'accueil    : http://%s:%d/' % ((adresses() or ['localhost'])[0], PORT))
    print('  Positionnement    : http://%s:%d/positionnement.html' % ((adresses() or ['localhost'])[0], PORT))
    print('  À projeter : http://localhost:%d/projeter   (adresse en grand, QR code si le module qrcode est installé)' % PORT)
    print('  Professeur : http://localhost:%d/resultats   (qui est connecté, où il en est, les résultats)' % PORT)
    print('  Cartographie : http://localhost:%d/cartographie   (CSV : /cartographie.csv)' % PORT)
    print('  Tableau    : http://localhost:%d/resultats.csv' % PORT)
    print('  Résultats  : %s' % JSONL)
    print('=' * 64)
    ThreadingHTTPServer(('0.0.0.0', PORT), Gestionnaire).serve_forever()
