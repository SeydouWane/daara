"""Matrice des droits (spec §3.2) et droits d'un utilisateur aux rôles cumulés.

Lettres : L lire · C créer · M modifier ses contenus · P publier sans validation ·
V valider les contenus d'autrui · A administrer (vaut toutes les autres).

Les droits d'un utilisateur sont l'union de la colonne « visiteur » et des colonnes de ses
rôles actifs. Exemple : un chercheur également responsable d'axe obtient L C M P (chercheur)
plus V (responsable d'axe) sur les publications.
"""

from enum import StrEnum

from .models import Member, Role

ALL = frozenset("LCMPVA")
WRITE = frozenset("CMPV")
VISITOR = "visitor"


class Module(StrEnum):
    EDITORIAL_PAGES = "editorial_pages"
    PROFILES = "profiles"
    PUBLICATIONS = "publications"
    DATASETS = "datasets"
    MODELS = "models"
    PROJECTS = "projects"
    TRAININGS = "trainings"
    REGISTRATIONS = "registrations"
    NEWS = "news"
    DASHBOARD = "dashboard"
    ADMINISTRATION = "administration"


# Recopie exacte du tableau de la spec §3.2, colonne par colonne.
_COLUMNS = (
    VISITOR,
    Role.LEARNER,
    Role.PHD_STUDENT,
    Role.RESEARCHER,
    Role.AXIS_LEAD,
    Role.EDITOR,
    Role.EXTERNAL,
    Role.OBSERVER,
    Role.ADMIN,
)
# fmt: off
_ROWS = {
    #                         visit. apprenant doctorant chercheur resp.axe éditeur externe observ. admin
    Module.EDITORIAL_PAGES: ("L",   "L",      "L",      "L",      "L",     "LCMP",  "L",    "L",    "A"),
    Module.PROFILES:        ("L",   "L",      "LCM",    "LCM",    "LCMV",  "LM",    "LM",   "L",    "A"),
    Module.PUBLICATIONS:    ("L",   "L",      "LCM",    "LCMP",   "V",     "LM",    "LCM",  "L",    "A"),
    Module.DATASETS:        ("L",   "L",      "LCM",    "LCMP",   "V",     "LM",    "LCM",  "L",    "A"),
    Module.MODELS:          ("L",   "L",      "LCM",    "LCMP",   "V",     "L",     "LCM",  "L",    "A"),
    Module.PROJECTS:        ("L",   "L",      "L",      "LCMP",   "V",     "LM",    "L",    "L",    "A"),
    Module.TRAININGS:       ("L",   "L",      "L",      "LCM",    "V",     "LCMP",  "",     "L",    "A"),
    Module.REGISTRATIONS:   ("C",   "LM",     "L",      "L",      "L",     "L",     "",     "L",    "A"),
    Module.NEWS:            ("L",   "L",      "CM",     "CM",     "V",     "LCMP",  "",     "L",    "A"),
    Module.DASHBOARD:       ("",    "",       "L",      "L",      "L",     "L",     "",     "L",    "A"),
    Module.ADMINISTRATION:  ("",    "",       "",       "",       "",      "",      "",     "",     "A"),
}
# fmt: on
MATRIX = {module: dict(zip(_COLUMNS, row, strict=True)) for module, row in _ROWS.items()}


def active_assignments(user):
    """Affectations actives de `user`, gardées sur l'objet le temps de la requête."""
    cached = getattr(user, "_active_assignments", None)
    if cached is None:
        cached = list(user.role_assignments.active().select_related("axis"))
        user._active_assignments = cached
    return cached


def granted(user, module, *, axis=None):
    """Lettres accordées à `user` sur `module`.

    `axis` limite les droits de responsable d'axe aux contenus de cet axe. Un alumni perd
    ses droits d'écriture mais garde la lecture (spec §3.3).
    """
    letters = set(MATRIX[module][VISITOR])
    if not user.is_authenticated:
        return frozenset(letters)
    for assignment in active_assignments(user):
        if assignment.role == Role.AXIS_LEAD and axis is not None and assignment.axis_id != axis.pk:
            continue
        letters.update(MATRIX[module][assignment.role])
    if user.is_superuser or "A" in letters:
        return ALL
    member = getattr(user, "member", None)
    if member is not None and member.status == Member.Status.ALUMNI:
        letters -= WRITE
    return frozenset(letters)


def can(user, letter, module, *, axis=None):
    return letter in granted(user, module, axis=axis)


def can_any(user, letter, *modules):
    return any(can(user, letter, module) for module in modules)
