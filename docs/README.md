# Documentation technique

Ce dossier rassemble la documentation technique de DAARA et les notes de passation : toute passation de rôle donne lieu à une note écrite de deux pages déposée ici (spec §2.3).

## Écarts assumés par rapport à la spécification v1

| Sujet | Spécification | Choix retenu | Raison |
|---|---|---|---|
| Formatage | ruff **et** black | ruff seul (`ruff format`) | `ruff format` reproduit black ; deux outils feraient doublon. |
| Bascule de langue | sélecteur par cookie | lien GET `/i18n/<langue>/?next=…` | le formulaire POST de Django impose un jeton CSRF dans chaque page, incompatible avec le cache de 15 minutes des pages publiques (§7.5). |
| Logo animé | pas d'animation imposée | boucle continue de 6 s, avec un bouton « Mettre en pause les animations » en pied de page | une animation automatique de plus de 5 s doit pouvoir être arrêtée (WCAG 2.1 critère 2.2.2, niveau A, exigé par §10.4). La préférence système « réduire les animations » coupe aussi la boucle. |
| Profils | un profil par utilisateur | rôles cumulables, droits = union des rôles actifs ; un seul sidebar qui réunit les sections de tous les rôles | demande du porteur de projet ; règle aussi le cas du responsable d'axe, qui n'a que « V » dans la matrice et cumule en pratique le rôle de chercheur. |
| Grades | liste fixe (PT, MC, CT…) | table modifiable dans l'administration | les grades diffèrent selon les pays des universités partenaires. |
| Menus de la vitrine | pages du module M1 | menus complets dès maintenant (à propos, recherche, membres, formation et actualités, contact) ; les modules à venir s'affichent « bientôt », sans lien | montrer l'arborescence finale sans lien cassé ; chaque entrée s'active seule quand son module existe. |
| Corps des pages éditoriales | non précisé | Markdown, nettoyé à l'affichage | lisible dans l'administration, sans éditeur riche à maintenir. |
| Logos des universités | non précisé | téléversés dans l'administration depuis les fichiers officiels, monogramme en attendant | un logo est une marque : il se récupère auprès du service communication de chaque université, avec son accord, plutôt que copié d'un site web. |
| Illustrations | images WebP (§7.5) | illustrations SVG dessinées pour DAARA ; photos de couverture facultatives, converties en WebP | quelques Ko au lieu de centaines, aucune question de droits, cohérence avec la charte. |
| Périmètre institutionnel | UNCHK et USSEIN | toutes les universités partenaires | correction du porteur de projet : les institutions seront une donnée, pas deux valeurs codées en dur. |

## Valeurs provisoires

La palette (vert `#0f5c4a`, ocre `#b45309`), les polices (Inter, Space Grotesk) et le favicon sont provisoires, en attendant la charte graphique du lot 0.
