"""Fabrique a-projeter/Projeter-en-classe.html : les deux QR codes (test d'accueil, positionnement) portant
le lien public avec le numéro WhatsApp du professeur (…?wa=NUMERO), l'adresse en gros, la marche à suivre.
Usage : python faire-la-page-a-projeter.py 33612345678      (numéro au format international, sans + ni espaces)
Le dossier a-projeter/ n'est pas versionné : le numéro n'entre jamais dans le dépôt public."""
import base64, io, os, re, sys
try:
    import qrcode
except ImportError:
    sys.exit("Module qrcode absent : python -m pip install --user \"qrcode[pil]\"")

NUM = sys.argv[1] if len(sys.argv) > 1 else ''
if not re.fullmatch(r'\d{8,15}', NUM):
    sys.exit("Donner le numéro au format international, sans + ni espaces (ex. : 33612345678)")
BASE = 'https://frigorx.github.io/test-accueil-mfer/'
PAGES = [
    ("Test d'accueil", "sécurité, règlement, règles de la classe · noté sur 20 · 1 h", BASE + '?wa=' + NUM, 'frigorx.github.io/test-accueil-mfer'),
    ("Positionnement", "six niveaux, non noté · le niveau atteint et mes compétences", BASE + 'positionnement.html?wa=' + NUM, 'frigorx.github.io/test-accueil-mfer/positionnement.html'),
]
lisible = '0' + NUM[2:] if NUM.startswith('33') else '+' + NUM
lisible = ' '.join(lisible[i:i + 2] for i in range(0, len(lisible), 2)) if lisible.startswith('0') else lisible

def qr(url):
    img = qrcode.make(url, box_size=10, border=2)
    b = io.BytesIO(); img.save(b, format='PNG')
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()

colonnes = ''.join(f"""
  <section>
    <h2>{titre}</h2>
    <p class="sous">{sous}</p>
    <img src="{qr(url)}" alt="QR code">
    <p class="adresse">{court}</p>
  </section>""" for titre, sous, url, court in PAGES)

html = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>À projeter — tests sur téléphone</title>
<style>
  body{{font-family:Calibri,'Segoe UI',sans-serif;margin:0;background:#fff;color:#22303f}}
  main{{display:flex;gap:24px;padding:18px 28px 0}}
  section{{flex:1;text-align:center;border:2px solid #d8dee6;border-radius:12px;padding:14px 10px}}
  h2{{margin:0;color:#1b3a63;font-size:34px}} .sous{{margin:4px 0 8px;font-size:18px;color:#555}}
  img{{width:min(38vh,360px);height:auto}}
  .adresse{{font-family:Consolas,monospace;font-size:24px;margin:8px 0 0;word-break:break-all}}
  ol{{font-size:24px;margin:16px 28px;padding-left:34px}} li{{margin:4px 0}}
  .num{{font-size:30px;text-align:center;margin:6px 0 14px;color:#128c7e;font-weight:bold}}
</style></head><body>
<main>{colonnes}</main>
<ol>
  <li>Je scanne le QR code (ou je tape l'adresse). Wi-Fi ou 4G, au choix.</li>
  <li>Mon nom, ma classe, « Commencer ».</li>
  <li>Je réponds. <b>Je ne quitte pas la page</b> : chaque sortie est comptée.</li>
  <li>À la fin : capture d'écran du cadre, puis « Envoyer par WhatsApp au professeur ».</li>
</ol>
<p class="num">WhatsApp du professeur : {lisible}</p>
</body></html>
"""
os.makedirs('a-projeter', exist_ok=True)
chemin = os.path.join('a-projeter', 'Projeter-en-classe.html')
open(chemin, 'w', encoding='utf-8').write(html)
print(chemin, ':', len(html) // 1024, 'Ko —', ' · '.join(p[2] for p in PAGES))
