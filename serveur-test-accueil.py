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
COLONNES = ['recu', 'nom', 'diplome', 'note', 'sorties', 'arret', 'repondu', 'total', 'code', 'competences', 'blocs', 'reponses', 'ip']


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
            '<h1>Résultats du test d\'accueil — %d élève(s)</h1>'
            '<p>Rafraîchi toutes les 10 secondes · <a href="/resultats.csv">télécharger le tableau (CSV)</a> · fichier : %s</p>'
            '<table><tr><th>Heure</th><th>Nom</th><th>Classe · date</th><th>Note /20</th><th>Sorties</th><th>Répondu</th><th>Code</th><th>Compétences</th></tr>%s</table>'
            % (len(lignes), html.escape(JSONL), ''.join(tr) or '<tr><td colspan="8">Aucun résultat pour l\'instant.</td></tr>'))


class Gestionnaire(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=ICI, **k)

    def log_message(self, fmt, *args):  # journal court
        if '/resultat' in (args[0] if args else ''):
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
        if not self.path.startswith('/resultat'):
            self.repondre(404, 'non')
            return
        try:
            n = int(self.headers.get('Content-Length') or 0)
            d = json.loads(self.rfile.read(n).decode('utf-8') or '{}')
            if not isinstance(d, dict) or not d.get('nom'):
                raise ValueError('résultat sans nom')
            d = {k: d.get(k, '') for k in COLONNES if k not in ('recu', 'ip')} | {'recu': datetime.now().isoformat(timespec='seconds'), 'ip': self.client_address[0]}
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
    print('  Professeur : http://localhost:%d/resultats' % PORT)
    print('  Tableau    : http://localhost:%d/resultats.csv' % PORT)
    print('  Résultats  : %s' % JSONL)
    print('=' * 64)
    ThreadingHTTPServer(('0.0.0.0', PORT), Gestionnaire).serve_forever()
