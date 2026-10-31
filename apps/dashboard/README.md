# apps.dashboard

Espace connecté (`/{langue}/dashboard/`) : un sidebar unique qui réunit les droits de tous les rôles actifs de l'utilisateur (module M9).

- `navigation.py` : registre des sections et des liens. Chaque lien porte la condition qui l'affiche, et `DashboardMixin` applique la même condition à la vue : le menu et les accès ne peuvent pas diverger. Pour ajouter une page, déclarer son lien ici, puis sa vue avec `url_name`.
- `views.py` : vue d'ensemble, profil (modifiable par son titulaire), file de validation (vide jusqu'aux productions, phase 2), traductions manquantes (du plus ancien au plus récent), premiers indicateurs (le tableau de bord observateur complet arrive au lot 4).
