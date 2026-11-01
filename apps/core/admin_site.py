"""Site d'administration de DAARA : les modèles y sont rangés comme sur la vitrine publique.

Plutôt que par application technique (core, members, research), l'accueil et le menu latéral
de l'administration suivent les rubriques que voit le visiteur : on retrouve ce qu'on veut
modifier là où on l'a vu.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

SECTIONS = (
    ("home", _("Home page and footer"), ("core.sitesettings", "core.homefeature")),
    (
        "pages",
        _("Pages: About, Partners, Contact…"),
        ("core.page", "core.standard", "core.partnershipstep"),
    ),
    ("research", _("Research"), ("members.axis", "research.publication")),
    ("members", _("Members"), ("members.member", "members.grade")),
    ("partners", _("Partner institutions"), ("members.institution",)),
    ("accounts", _("Accounts and roles"), ("members.user", "members.roleassignment")),
    ("audit", _("Action log"), ("admin.logentry",)),
)


class DaaraAdminSite(admin.AdminSite):
    site_header = _("DAARA administration")
    site_title = _("DAARA administration")
    index_title = _("Everything shown on the public site")

    def get_app_list(self, request, app_label=None):
        app_list = super().get_app_list(request, app_label)
        if app_label is not None:
            return app_list
        models = {
            entry["model"]._meta.label_lower: entry for app in app_list for entry in app["models"]
        }
        sections = []
        for key, name, labels in SECTIONS:
            entries = [models.pop(label) for label in labels if label in models]
            if entries:
                sections.append(self._section(key, name, entries))
        if models:  # un modèle oublié dans SECTIONS reste accessible
            sections.append(self._section("other", _("Other"), list(models.values())))
        return sections

    @staticmethod
    def _section(key, name, entries):
        return {
            "name": name,
            "app_label": key,
            # Le titre de la rubrique mène à son premier élément.
            "app_url": entries[0].get("admin_url") or "#",
            "has_module_perms": True,
            "models": entries,
        }
