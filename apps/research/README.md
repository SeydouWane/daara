# apps.research

Productions scientifiques (modules M3, M4, M5).

## Modèles

- `Production` : table commune à toutes les productions (spec §6) : titre dans sa langue d'origine (jamais traduit, §5.1), langue, année, résumé traduit (niveau 3 : anglais attendu, français recommandé), axe, licence, statut (brouillon, en attente, publié, archivé).
- `Authorship` : auteurs dans l'ordre de la publication ; un co-auteur extérieur n'a qu'un nom, un membre est relié à son profil.
- `Publication(Production)` : type (article, communication, chapitre, ouvrage, thèse, mémoire, prépublication, rapport), DOI normalisé, revue ou conférence, éditeur, volume, numéro, pages, accès ouvert, identifiants HAL, DICAMES et OpenAlex.

Jeux de données, modèles et supports de formation viendront s'ajouter comme autres sous-types de `Production`.

## Pages publiques

- `/{langue}/publications/` : recherche (titre, auteur, revue), filtres par année, type, auteur et axe ; avec HTMX, la liste se met à jour sans recharger la page.
- `/{langue}/publications/<slug>/` : résumé (avec bandeau de repli si la traduction manque), référence prête à copier, BibTeX affiché et téléchargeable (`…/bibtex/`), lien vers le DOI.
- Le profil de chaque membre liste ses publications ; l'accueil affiche le compteur et les trois plus récentes.

`citation.py` produit le BibTeX et la référence lisible. RIS et CSL-JSON restent à faire.
