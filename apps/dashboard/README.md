# apps.dashboard

Espace connecté (`/{langue}/dashboard/`) : un sidebar unique qui réunit les droits de tous les rôles actifs de l'utilisateur (module M9).

- `navigation.py` : registre des sections et des liens. Chaque lien porte la condition qui l'affiche, et `DashboardMixin` applique la même condition à la vue : le menu et les accès ne peuvent pas diverger. Pour ajouter une page, déclarer son lien ici, puis sa vue avec `url_name`.
- `views.py` : vue d'ensemble, profil (modifiable par son titulaire), file de validation (vide jusqu'aux productions, phase 2), traductions manquantes (du plus ancien au plus récent), premiers indicateurs (le tableau de bord observateur complet arrive au lot 4), journal des actions.

## Pages « Gérer »

Le back-office des éditeurs et des administrateurs, dans le design de l'espace : tout ce que montre le site public s'y modifie (accueil et pied de page, cartes de l'accueil, pages, standards, étapes de partenariat, axes, publications, jeux de données, modèles et code, projets, membres, institutions), plus les comptes, les rôles et les grades.

- `manage.py` : registre des contenus. Chacun déclare son formulaire, les colonnes de sa liste et ses champs de recherche ; quatre vues génériques servent la liste, l'ajout, la modification et la suppression (`/dashboard/manage/<clé>/…`). Pour rendre un nouveau contenu gérable : un formulaire dans `forms.py`, une entrée dans le registre, une règle dans `MANAGE_RULES`, un lien dans le sidebar.
- Droits : `permissions.may()` lit `MANAGE_RULES` (apps/members/permissions.py), tirée de la matrice §3.2. Il faut être éditeur ou administrateur ; l'éditeur rédige les textes, seul l'administrateur touche à la structure (institutions, comptes, rôles) et supprime.
- `forms.py` : `ManageForm` met en forme les champs, passe les textes longs en zone de texte et place les versions FR / EN d'un champ côte à côte. Les adresses (slug) se construisent à partir du titre et ne changent plus ensuite. Ajouter un membre lui ouvre son compte ; les auteurs d'une production s'éditent avec elle.
- Chaque ajout, modification et suppression est inscrit au journal des actions (`LogEntry`), consultable par l'administrateur.
