"""Droits de l'administration Django, tirés de la matrice des rôles (permissions.py).

L'administration est le back-office des éditeurs et des administrateurs : il faut le statut
« équipe » et l'un de ces deux rôles. Chaque modèle y relève d'un module de la matrice. Par
défaut, le voir ou le modifier demande M, en ajouter C, en supprimer A ; RULES précise les
exceptions. Ainsi un administrateur qui n'est pas super-utilisateur gère tout le site, et un
éditeur les textes de la vitrine, sans aucune permission Django à cocher à la main.
"""

from django.contrib.auth.backends import BaseBackend

from .permissions import Module, can

DEFAULT = {"view": "M", "add": "C", "change": "M", "delete": "A"}

RULES = {
    # Vitrine : l'éditeur en rédige les textes ; seul l'administrateur crée ou retire une page.
    "core.sitesettings": (Module.EDITORIAL_PAGES, {}),
    "core.homefeature": (Module.EDITORIAL_PAGES, {"delete": "P"}),
    "core.standard": (Module.EDITORIAL_PAGES, {"delete": "P"}),
    "core.partnershipstep": (Module.EDITORIAL_PAGES, {"delete": "P"}),
    "core.page": (Module.EDITORIAL_PAGES, {"add": "A"}),
    # Les axes sont créés par l'administrateur, leurs textes traduits par l'éditeur.
    "members.axis": (Module.EDITORIAL_PAGES, {"add": "A"}),
    "members.member": (Module.PROFILES, {"add": "A"}),
    "members.affiliation": (Module.PROFILES, {"add": "A", "change": "A"}),
    "research.publication": (Module.PUBLICATIONS, {}),
    "research.authorship": (Module.PUBLICATIONS, {"add": "A", "change": "A"}),
    "members.institution": (Module.ADMINISTRATION, {}),
    "members.grade": (Module.ADMINISTRATION, {}),
    "members.user": (Module.ADMINISTRATION, {}),
    "members.roleassignment": (Module.ADMINISTRATION, {}),
    "admin.logentry": (Module.ADMINISTRATION, {}),
}


def is_back_office(user):
    """Éditeur ou administrateur avec le statut « équipe »."""
    return user.is_active and user.is_staff and can(user, "P", Module.EDITORIAL_PAGES)


class RolePermissionBackend(BaseBackend):
    def has_perm(self, user_obj, perm, obj=None):
        if not is_back_office(user_obj):
            return False
        app_label, _dot, codename = perm.partition(".")
        action, _underscore, model = codename.partition("_")
        rule = RULES.get(f"{app_label}.{model}")
        if rule is None or action not in DEFAULT:
            return False
        module, exceptions = rule
        return can(user_obj, exceptions.get(action, DEFAULT[action]), module)

    def has_module_perms(self, user_obj, app_label):
        return any(
            self.has_perm(user_obj, f"{label}.view_{model}")
            for label, _dot, model in (key.partition(".") for key in RULES)
            if label == app_label
        )
