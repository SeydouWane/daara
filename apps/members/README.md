# apps.members

Comptes, institutions partenaires, axes thématiques, profils de membres et rôles (module M2 et spec §3).

## Modèles

- `User` : modèle d'utilisateur personnalisé (`AUTH_USER_MODEL = "members.User"`).
- `Institution` : université ou organisme partenaire (nom traduit, sigle, pays ISO, identifiant ROR normalisé). Aucune institution n'est codée en dur.
- `Axis` : axe thématique ; nom obligatoire dans chaque langue éditoriale (`DAARA_EDITORIAL_LANGUAGES`).
- `Grade` : table de grades, ordonnée du plus élevé au moins élevé (les grades varient selon les pays).
- `Member` : profil public, relié à un `User` ; rattachements multiples via `Affiliation` (un seul principal), ORCID normalisé et vérifié (clé ISO 7064), statut actif ou alumni.
- `RoleAssignment` : un rôle attribué à un utilisateur, avec dates de début et d'expiration. Contraintes : un responsable d'axe est rattaché à un axe et un seul responsable actif par axe ; un observateur a une expiration de 12 mois au plus.

## Droits : `permissions.py`

La matrice de la spec §3.2 y est recopiée telle quelle. Les droits d'un utilisateur sont l'**union** de la colonne visiteur et de ses rôles actifs : les rôles se cumulent.

```python
from apps.members.permissions import Module, can

can(user, "V", Module.PUBLICATIONS, axis=publication.axis)  # valider dans cet axe ?
```

Un alumni garde la lecture mais perd l'écriture (spec §3.3). Le rôle de collaborateur externe sera limité à un projet quand le module Projets existera (phase 3).

## Démonstration

`python manage.py seed_demo` (développement seulement) crée trois institutions, trois axes, des grades et quatre comptes aux rôles combinés, mot de passe `daara-demo-2026`.
