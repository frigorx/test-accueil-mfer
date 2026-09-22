/* Choisir son nom dans la liste de la classe, au lieu de le taper.
 *
 * Pourquoi : le 22/09/2026, sur vingt résultats reçus, quatre étaient signés « Mini sicario »,
 * « Waaaaaayyyli », « Waayyyli » ou d'un prénom seul — impossibles à rattacher à un élève.
 * Un nom se choisit d'un clic, il ne se retape pas.
 *
 * Fonctionnement : le champ #nom reste la source de vérité (aucun autre code ne change).
 * Toucher un bouton le remplit. Si le serveur ne donne pas de liste — page en ligne, aucune
 * classe réglée — la saisie libre reste en place, exactement comme avant.
 */
(function () {
  var champ = document.getElementById('nom');
  if (!champ) return;
  var etiquette = document.querySelector('label[for="nom"]');

  // Servie par le PC du professeur ? Même test que le reste des pages. Ailleurs (version en
  // ligne, fichier ouvert seul) on ne demande rien : pas de liste à obtenir, et pas de 404
  // inutile dans la console.
  if (!(location.protocol === 'http:' && !/github\.io$/.test(location.hostname))) return;

  fetch('/classe.json', { cache: 'no-store' })
    .then(function (r) { return r.ok ? r.json() : Promise.reject(); })
    .then(function (d) {
      var eleves = (d && d.eleves) || [];
      if (!eleves.length) return;                       // pas de liste : on ne touche à rien

      var zone = document.createElement('div');
      zone.className = 'liste-classe';
      zone.setAttribute('role', 'group');
      zone.setAttribute('aria-label', 'Je touche mon nom');

      eleves.forEach(function (nom) {
        var b = document.createElement('button');
        b.type = 'button';
        b.className = 'nom-eleve';
        b.textContent = nom;
        b.addEventListener('click', function () {
          champ.value = nom;
          [].forEach.call(zone.querySelectorAll('.nom-eleve'), function (x) { x.classList.remove('choisi'); });
          b.classList.add('choisi');
          var c = document.getElementById('commencer');
          if (c) c.scrollIntoView({ block: 'nearest', behavior: 'smooth' });
        });
        zone.appendChild(b);
      });

      // Sortie de secours : un élève arrivé en cours d'année, un remplaçant, un oubli de liste.
      var autre = document.createElement('button');
      autre.type = 'button';
      autre.className = 'nom-autre';
      autre.textContent = "Mon nom n'est pas dans la liste";
      autre.addEventListener('click', function () {
        champ.hidden = false;
        champ.value = '';
        champ.focus();
        autre.hidden = true;
      });
      zone.appendChild(autre);

      champ.hidden = true;                              // caché, pas supprimé : il reste la source de vérité
      if (etiquette) etiquette.textContent = 'Je touche mon nom' + (d.classe ? ' — ' + d.classe : '');
      champ.parentNode.insertBefore(zone, champ);

      var css = document.createElement('style');
      css.textContent =
        '.liste-classe{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 12px}' +
        '.liste-classe .nom-eleve{flex:1 1 44%;min-height:52px;font:inherit;font-size:17px;' +
        'background:#fff;color:#1b3a63;border:2px solid #c9d3df;border-radius:10px;padding:10px 12px;cursor:pointer;text-align:left}' +
        '.liste-classe .nom-eleve.choisi{background:#1b3a63;color:#fff;border-color:#1b3a63;font-weight:bold}' +
        '.liste-classe .nom-autre{flex:1 1 100%;font:inherit;font-size:15px;background:transparent;' +
        'color:#5d6b7c;border:1px dashed #c9d3df;border-radius:10px;padding:10px;cursor:pointer}';
      document.head.appendChild(css);
    })
    .catch(function () { /* pas de serveur : la saisie libre reste, rien à signaler à l'élève */ });
})();
