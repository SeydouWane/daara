# apps.projects

Projets de recherche (module M6).

- `Project` : titre, résumé et description traduits (Markdown), acronyme, état (brouillon, en cours, terminé), axe, porteur, équipe, institutions partenaires, financements, dates, site web, image de couverture, productions liées (publications, jeux de données, modèles).
- `/{langue}/projects/` : cartes filtrables par état et par axe, recherche ; avec HTMX, la liste se met à jour sans recharger la page. Les brouillons ne sont jamais montrés.
- `/{langue}/projects/<slug>/` : présentation, équipe, partenaires (logos), financements, productions. Le profil de chaque membre liste ses projets.
- Gestion : pages « Gérer » de l'espace (`apps/dashboard`).
