# apps.core

Socle transverse : accueil, pages éditoriales (module M1), gabarits de base, logo, bascule de langue et sonde `/healthz`.

- `views.py` : `HomeView`, `LogoSheetView` (planche du logo, développement seulement), `healthz`, `switch_language`.
- Logo : variante « Signal » en boucle, choisie le 31 octobre 2026. Gabarits `components/logo.html` (déclinaisons réduite, icône, complète) et `components/logo_symbol.html` ; styles dans `assets/css/main.css` ; pause des animations dans `static/js/motion.js`.
- `templatetags/daara.py` : `hreflang_links` (balises hreflang réciproques) et `switch_language_url`.
- Les modèles abstraits communs (horodatage, statut éditorial) arrivent avec le premier modèle concret, en phase 1.
