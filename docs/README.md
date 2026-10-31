# Documentation technique

Ce dossier rassemble la documentation technique de DAARA et les notes de passation : toute passation de rôle donne lieu à une note écrite de deux pages déposée ici (spec §2.3).

## Écarts assumés par rapport à la spécification v1

| Sujet | Spécification | Choix retenu | Raison |
|---|---|---|---|
| Formatage | ruff **et** black | ruff seul (`ruff format`) | `ruff format` reproduit black ; deux outils feraient doublon. |
| Bascule de langue | sélecteur par cookie | lien GET `/i18n/<langue>/?next=…` | le formulaire POST de Django impose un jeton CSRF dans chaque page, incompatible avec le cache de 15 minutes des pages publiques (§7.5). |
| Périmètre institutionnel | UNCHK et USSEIN | toutes les universités partenaires | correction du porteur de projet : les institutions seront une donnée, pas deux valeurs codées en dur. |

## Valeurs provisoires

La palette (vert `#0f5c4a`, ocre `#b45309`), les polices (Inter, Space Grotesk) et le favicon sont provisoires, en attendant la charte graphique du lot 0.
