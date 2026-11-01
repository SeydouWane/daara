# apps.core

Socle transverse et vitrine publique (module M1) : accueil, pages éditoriales, menus, logo, bascule de langue, sonde `/healthz`.

## Pages éditoriales

`Page` (titre, résumé, corps en Markdown, traduits) : à propos, gouvernance, partenaires, contact, mentions légales, politique de confidentialité. La migration `0002_seed_pages` les crée avec des textes de départ tirés de la documentation ; l'éditeur les relit et les complète dans l'administration.

- Une page n'est publiée que si elle a un titre et un corps dans chaque langue éditoriale (niveau 2, spec §5.1).
- Les mentions légales et la politique de confidentialité restent en brouillon tant que l'éditeur juridique et l'hébergeur ne sont pas choisis (lot 0) : elles n'apparaissent pas dans le pied de page.
- Le Markdown est rendu par le filtre `render_markdown`, puis nettoyé (`nh3`) : seules les balises de mise en forme passent.
- Si une traduction manque, la page s'affiche dans la langue disponible avec un bandeau « Disponible en français uniquement » (`i18n.py`, spec §5.3).

## Menus : `navigation.py`

Registre des menus de l'en-tête et du pied de page. Un lien vers un module pas encore construit (publications, formations…) s'affiche « bientôt », sans être cliquable ; il devient un vrai lien dès que son URL existe. Un lien vers une page éditoriale n'apparaît que si la page est publiée.

Les menus déroulants et le menu mobile sont des éléments `<details>` : ils marchent au clavier et sans JavaScript. `static/js/ui.js` ajoute la fermeture au clic extérieur et avec Échap.

## Images et illustrations

- `images.py` : toute image téléversée (logo d'institution, couverture de page) produit à l'enregistrement des déclinaisons WebP (`renditions/…-<largeur>w.webp`), jamais agrandies. La balise `{% responsive_image %}` les sert avec `srcset`, dimensions explicites et chargement différé (spec §7.5). Taille maximale : 5 Mo.
- Illustrations dessinées pour DAARA, en SVG intégré (quelques Ko, aucun fichier à télécharger) : `components/illustration_network.html` (accueil), `components/axis_icon.html` (une par type d'axe, choisi dans l'administration), `components/icon.html` (pictogrammes).
- Motifs de fond en CSS pur dans `assets/css/main.css` : grille de points (`.pattern-dots`) et halo (`.hero-glow`).

## Autres fichiers

- `views.py` : accueil, pages, axes de recherche, partenaires, planche du logo (développement), `healthz`, `switch_language`.
- `templatetags/daara.py` : `hreflang_links`, `switch_language_url`, `public_navigation`, `render_markdown`.
- `fields.py` : `HttpsURLField`, qui complète une adresse sans schéma en `https://`.
- Logo : variante « Signal » en boucle de 12 s : le trait se fixe en point, puis DAARA monte et laisse la place à sa signification, qui monte à son tour avant le retour de DAARA (gabarits `components/logo.html` et `components/logo_symbol.html`, styles `.logo-ticker`, pause dans `static/js/motion.js`). La planche `/fr/dev/logo/` montre les deux temps en image fixe.
