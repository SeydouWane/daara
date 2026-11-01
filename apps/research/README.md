# apps.research

Productions scientifiques (modules M3, M4, M5).

## Modèles

- `Production` : table commune à toutes les productions (spec §6) : titre dans sa langue d'origine (jamais traduit, §5.1), langue, année, résumé traduit (niveau 3 : anglais attendu, français recommandé), axe, licence, statut (brouillon, en attente, publié, archivé). `specific()` rend la production sous son vrai type.
- `Authorship` : auteurs dans l'ordre de la publication ; un co-auteur extérieur n'a qu'un nom, un membre est relié à son profil.
- `Publication(Production)` : type (article, communication, chapitre, ouvrage, thèse, mémoire, prépublication, rapport), DOI normalisé, revue ou conférence, éditeur, volume, numéro, pages, accès ouvert, identifiants HAL, DICAMES et OpenAlex.
- `Dataset(Production)` : DOI, page de l'entrepôt (Zenodo, Hugging Face…), accès (ouvert, sur demande, restreint), version, format, taille, langues et zone couvertes. DAARA tient la fiche, les données restent dans l'entrepôt.
- `AIModel(Production)` : modèle entraîné, code ou démonstrateur ; tâche, cadriciel, dépôt Hugging Face, code source, démonstrateur, DOI, langues couvertes, données d'entraînement.

Les supports de formation viendront s'ajouter comme autre sous-type de `Production`.

## Pages publiques

- `/{langue}/publications/`, `/{langue}/datasets/`, `/{langue}/models/` : recherche, filtres par année, auteur, axe et type (ou accès) ; avec HTMX, la liste se met à jour sans recharger la page (`ProductionListView`). Un catalogue vide l'annonce plutôt que d'afficher une liste blanche.
- Fiches : résumé (avec bandeau de repli si la traduction manque), auteurs reliés à leurs profils, projets liés.
  - publication : référence prête à copier, BibTeX affiché et téléchargeable (`…/bibtex/`), lien vers le DOI ;
  - jeu de données : référence à la manière de DataCite, métadonnées, modèles entraînés dessus, données structurées schema.org/Dataset pour Google Dataset Search ;
  - modèle : liens Hugging Face, code et démonstrateur, données d'entraînement.
- Le profil de chaque membre liste ses productions ; l'accueil affiche les compteurs et les trois publications les plus récentes.

`citation.py` produit le BibTeX et les références lisibles. RIS et CSL-JSON restent à faire.
