# apps.interop

Échanges avec les services extérieurs (module M10, spec §8).

## Import OpenAlex

`openalex.py` et la commande `import_openalex` importent les travaux d'un auteur OpenAlex et les relient au profil d'un membre : titre, année, type, revue, DOI, pages, accès ouvert, résumé, co-auteurs dans l'ordre.

```sh
# 1. Relire la liste : OpenAlex fusionne parfois des homonymes sous un même auteur.
docker compose run --rm web python manage.py import_openalex A5011347992 --member ousmane-sall --dry-run
# 2. Importer en écartant les travaux qui ne sont pas les siens.
docker compose run --rm web python manage.py import_openalex A5011347992 --member ousmane-sall --exclude W7167577444 W7171564703
```

Un nouvel import met à jour les métadonnées sans créer de doublon (rapprochement par identifiant OpenAlex puis par DOI) et conserve le statut et l'axe choisis par l'équipe. Les jeux de données sont ignorés : ils relèvent du module M4.

Réglage facultatif : `OPENALEX_MAILTO` (adresse de contact, accès plus rapide à l'API).

À venir : point d'entrée OAI-PMH, API REST publique, JSON-LD, import par DOI (Crossref, DataCite) et par ORCID.
