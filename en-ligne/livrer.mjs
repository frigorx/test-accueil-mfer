/* livrer.mjs — fabrique la station « inerWeb QCM » d'inerweb.fr à partir des pages de la classe.
   ---------------------------------------------------------------------
   POURQUOI (décision de Franck, 21/09/2026) : l'outil se coupe en deux selon OÙ VONT LES RÉSULTATS.
   La version de classe (servie par le PC du professeur) relève les notes ; la version en ligne est
   une RÉVISION LIBRE : pas de nom, pas de sorties comptées, pas de note sur 20, rien n'est envoyé,
   aucune trace de l'établissement. L'outil de classe n'est PAS modifié : ce script en tire une copie.

   GARDE-FOU : chaque remplacement doit trouver exactement le nombre de cibles attendu, et la copie
   finale ne doit plus contenir aucun nom d'établissement ni de personne. Sinon le script s'arrête
   SANS RIEN ÉCRIRE : une page de classe modifiée ne passe jamais en ligne à moitié nettoyée.

   Usage : node en-ligne/livrer.mjs [racine du site]   (défaut : C:/git/pilote-fluides) → <site>/qcm/
   Ensuite, dans le site : node build/animations.mjs et node build/retour-accueil.mjs (pages qcm/ seules).
   ===================================================================== */
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash } from 'node:crypto';

const ATELIER = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const SITE = resolve(process.argv[2] || 'C:/git/pilote-fluides');
const SORTIE = join(SITE, 'qcm');
const lire = (p) => readFileSync(join(ATELIER, p), 'utf8');
const cle = (t) => createHash('sha1').update(t).digest('hex').slice(0, 10);
if (!existsSync(join(SITE, 'moteur', 'marque.js'))) throw new Error('Pas un site inerweb.fr : ' + SITE);

/* ---- un remplacement qui doit trouver sa cible ---- */
function remplacer(texte, cible, par, attendu, page) {
  const n = typeof cible === 'string' ? texte.split(cible).length - 1 : (texte.match(cible) || []).length;
  if (n !== attendu) throw new Error(page + ' : ' + n + ' cible(s) au lieu de ' + attendu + ' pour ' + String(cible).slice(0, 90));
  return typeof cible === 'string' ? texte.split(cible).join(par) : texte.replace(cible, par);
}
const appliquer = (texte, regles, page) => regles.reduce((t, [cible, par, n = 1]) => remplacer(t, cible, par, n, page), texte);

const revisionCss = lire('en-ligne/revision.css');
const filigrane = lire('en-ligne/filigrane.svg');
const CLE_REVISION = cle(revisionCss + filigrane);
const CLE_MARQUE = cle(readFileSync(join(SITE, 'moteur', 'marque.js')));
const SUR_LE_PC = "location.protocol === 'http:' && !/github\\.io$/.test(location.hostname)";
const RETOUR = ' id="accueil" href="./"';
const RETOUR_TEXTE = "Les autres activités d'inerWeb QCM";
// marque.js ne recalcule sa place (fixe en bas à gauche, ou en fin de page) qu'au redimensionnement ;
// ces pages changent de hauteur sans redimensionnement (écran suivant, symboles chargés) : sans ce
// relais, le logo fixe restait posé sur le bouton « Afficher les noms des symboles » (mesuré le 07/10).
const MARQUE = '\n<script src="../moteur/marque.js?v=' + CLE_MARQUE + '" data-cartouche=".fr"></script>\n'
  + "<script>if ('ResizeObserver' in window) new ResizeObserver(() => window.dispatchEvent(new Event('resize'))).observe(document.body);</script>\n";
// Les pages de classe n'ont ni <head> ni <body> (et le positionnement pas de doctype) : sans <head>,
// build/retour-accueil.mjs et build/animations.mjs du site ne posent pas leurs scripts.
const entete = (description) => (t) => (/^<!doctype/i.test(t) ? '' : '<!doctype html>\n<html lang="fr">\n')
  + remplacer(remplacer(t, '<meta charset="utf-8">', '<head>\n<meta charset="utf-8">', 1, 'entête'), /<\/style>/, '</style>\n</head>\n<body>', 1, 'entête')
    .replace(/<\/title>/, ' · inerWeb QCM</title>\n<meta name="description" content="' + description
  + '">\n<link rel="stylesheet" href="revision.css?v=' + CLE_REVISION + '">');

/* ---- ce que les trois pages ont en commun ---- */
const COMMUN = [
  ['header .lycee{', 'header .marque-qcm{'],
  ['<div class="lycee">LPP JACQUES RAYNAUD</div>', '<div class="marque-qcm">inerWeb QCM · réviser en autonomie</div>'],
];
const RESULTAT_SUR_L_APPAREIL = [
  ["Ce résultat reste sur mon téléphone : la capture d\\'écran est ma preuve.", "Ce résultat reste sur cet appareil : rien n\\'est envoyé."],
  [/\s*<div class="consigne-capture">[^<]*<\/div>/, ''],
  [/<p style="margin:8px 0 2px"><b>Code de validation<\/b><\/p>\s*<div class="code" id="code"><\/div>/, '<div class="code" id="code" hidden></div>'],
  ['<label>Ma classe</label>', '<label>Ma formation</label>'],
  [/<label for="nom">[^<]*<\/label>\s*<input type="text" id="nom"[^>]*>/, '<input type="hidden" id="nom">'],
  // Le nom ne sert plus qu'à tirer les questions : un tirage neuf à chaque essai.
  ["const nom = $('nom').value.trim();", "const nom = 'révision ' + Date.now().toString(36);"],
  ["$('eleve').textContent = etat.nom;", "$('eleve').textContent = 'Révision libre';"],
  [' id="accueil" href="/" hidden', RETOUR],
  ["Retour à l'accueil : la suite des activités", RETOUR_TEXTE],
  ['Autre élève sur ce téléphone', 'Recommencer'],
];

const PAGES = [
  {
    source: 'positionnement.html', cible: 'positionnement.html',
    description: "Où j'en suis en froid, climatisation et habilitations : 196 questions sur six niveaux, de l'atelier jusqu'au niveau expert, puis ma carte des compétences (2de TNE, CAP IFCA, Bac Pro MFER). Révision libre : rien n'est envoyé.",
    regles: [
      ...COMMUN, ...RESULTAT_SUR_L_APPAREIL,
      [SUR_LE_PC, 'false', 3],
      [/<p><b>Ce test est noté sur 20[\s\S]*?<\/ul>/, `<p><b>Je révise à mon rythme.</b> Le test dit à quel niveau je suis et ce que je maîtrise déjà, compétence par compétence. Une seule bonne réponse, une explication après chaque réponse.</p>
    <ul class="regles">
      <li>Six niveaux, du niveau 0 (l'atelier et les règles) au niveau 5 (expert). Je monte tant que je réussis au moins la moitié d'un niveau. Personne n'est censé tout réussir.</li>
      <li>Le bouton 🔊 lit la question à voix haute.</li>
      <li>Rien n'est envoyé, aucun nom n'est demandé : mon résultat reste sur cet appareil. Je peux recommencer, les questions changent.</li>
    </ul>`],
      ['if (/^\\d{8,15}$/.test(wa)) COLLECTE.whatsapp = wa;', ''],
      ['function sortie(){', 'function sortie(){ return;   // révision libre : quitter la page ne compte pas\n'],
      [/ \+ ' · ' \+ minutes \+ ' min · sorties de la page : '[^;]*;/, " + ' · ' + minutes + ' min';"],
      ['Ce téléphone doit servir à un autre élève ? Le test repart de zéro.', 'Je recommence : un nouveau tirage de questions.'],
      ["ouvrir cette page depuis l'adresse donnée par le professeur, pas depuis un fichier.", 'rechargez la page.'],
      [/<footer>LPP Jacques Raynaud[^<]*<\/footer>/, '<footer>inerWeb QCM · inerweb.fr</footer>'],
      ['<script src="choisir-son-nom.js"></script>', MARQUE],
    ],
  },
  {
    source: 'manometres.html', cible: 'manometres.html',
    description: "Lire un manomètre comme sur un vrai manifold : l'aiguille, l'échelle du fluide, la température de changement d'état. Dix questions, puis « Et sur la machine ? » avec mes vrais relevés. Révision libre : rien n'est envoyé.",
    regles: [
      ...COMMUN, ...RESULTAT_SUR_L_APPAREIL,
      [SUR_LE_PC, 'false', 1],
      [/<p><b>10 questions, noté sur 20\.<\/b>[\s\S]*?<\/ul>/, `<p><b>10 questions.</b> Je lis des manomètres comme sur un vrai manifold : l'aiguille, puis l'échelle du fluide.</p>
    <ul class="regles">
      <li>Pour une lecture, j'ai droit à une petite marge : une graduation sur la pression, 2 °C sur la température.</li>
      <li>À la fin, la page « Et sur la machine ? » me sert avec mes vrais relevés.</li>
      <li>Rien n'est envoyé, aucun nom n'est demandé : mon résultat reste sur cet appareil. Je peux recommencer, les aiguilles changent.</li>
    </ul>`],
      [/<p style="font-size:30px[^>]*><b id="note"><\/b> \/ 20<\/p>/, '<p hidden><b id="note"></b></p>'],
      [" + ' · ' + pts + ' points sur ' + max", ''],
      ["$('accueil').hidden = !surLePC();", "$('accueil').hidden = false;"],
      ['Ce téléphone doit servir à un autre élève ? Tout repart de zéro.', 'Je recommence avec de nouvelles aiguilles.'],
      ["confirm('Tout effacer pour un autre élève ?')", "confirm('Tout recommencer ?')"],
      [/<br>LPP Jacques Raynaud[^<]*<\/footer>/, '<br>inerWeb QCM · inerweb.fr</footer>'],
      ['<script src="choisir-son-nom.js"></script>', MARQUE],
    ],
  },
  {
    source: 'jeux/schema-frigo/index.html', cible: 'schema-frigo.html',
    description: 'Compléter le schéma frigorifique avec les symboles normalisés : les quatre organes, puis la ligne liquide. Révision libre : rien n\'est envoyé.',
    regles: [
      ...COMMUN,
      [SUR_LE_PC, 'false', 1],
      [/<label for="nom">[\s\S]*?<\/a>/, '<input type="hidden" id="nom"><p class="petit" id="envoi" hidden></p>\n    <a class="suite"' + RETOUR + '>' + RETOUR_TEXTE + '</a>'],
      ["$('accueil').hidden = !surLePC();", "$('accueil').hidden = false;"],
      ["fetch('../../symboles.svg'", "fetch('symboles.svg'"],
      ["ouvrir cette page depuis l\\'adresse donnée par le professeur.", 'rechargez la page.'],
      [' (usine-contenu/bibliotheque-symboles)', ''],
      [/ · LPP Jacques Raynaud[^<]*<\/footer>/, ' · inerWeb QCM · inerweb.fr</footer>'],
      ['<script src="../../choisir-son-nom.js"></script>', MARQUE],
    ],
  },
];

/* ---- ce qui ne doit plus jamais rester dans une page publiée ---- */
const INTERDIT = /raynaud|henninot|warton|[ée]quatio|lyc[ée]e|\bLPP\b|campus|192\.168|C:\\/i;
function controler(nom, texte) {
  const m = texte.match(INTERDIT);
  if (m) throw new Error(nom + ' : reste « ' + texte.slice(Math.max(0, m.index - 40), m.index + 40).replace(/\s+/g, ' ') + ' »');
}

/* ---- fabrication en mémoire, puis écriture seulement si tout est passé ---- */
const fichiers = {};
for (const p of PAGES) fichiers[p.cible] = entete(p.description)(appliquer(lire(p.source), p.regles, p.source));
fichiers['index.html'] = lire('en-ligne/index.html').replace('CLE_REVISION', CLE_REVISION).replace('CLE_MARQUE', CLE_MARQUE);
fichiers['revision.css'] = revisionCss;
fichiers['filigrane.svg'] = filigrane;
// Le sprite des symboles du jeu, sans ses commentaires (chemin local, mode d'emploi).
fichiers['symboles.svg'] = lire('symboles.svg').replace(/<!--[\s\S]*?-->\s*/g, '');
// La banque, sans le champ `source` (chemins des cours sur le PC) et sans « lycée » : la station sert
// aussi en CFA et en entreprise.
const banque = JSON.parse(lire('banque.json')).map(({ source, ...q }) => q);
let texteBanque = JSON.stringify(banque);
texteBanque = appliquer(texteBanque, [
  ['Le règlement du lycée', "Le règlement de l'établissement", 3],
  ['Au lycée, je préviens d\'abord le professeur.', "En formation, je préviens d'abord le formateur.", 1],
], 'banque.json');
fichiers['banque.json'] = texteBanque;

for (const [nom, texte] of Object.entries(fichiers)) controler(nom, texte);
mkdirSync(SORTIE, { recursive: true });
for (const [nom, texte] of Object.entries(fichiers)) writeFileSync(join(SORTIE, nom), texte);
console.log('inerWeb QCM livré dans ' + SORTIE + ' : ' + Object.keys(fichiers).join(', ') + ' (' + banque.length + ' questions)');
