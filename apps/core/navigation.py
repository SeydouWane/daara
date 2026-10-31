"""Menus de la vitrine publique (module M1).

Un lien vers un module pas encore construit s'affiche « bientôt » sans être cliquable : il
devient un vrai lien dès que son URL existe, sans retoucher ce fichier. Un lien vers une page
éditoriale n'apparaît que si la page est publiée.
"""

from dataclasses import dataclass

from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _

from .models import Page


@dataclass(frozen=True)
class Link:
    label: str
    url_name: str
    page_slug: str = ""


@dataclass(frozen=True)
class Menu:
    label: str
    links: tuple[Link, ...]


MAIN_MENU = (
    Menu(
        _("About"),
        (
            Link(_("Mission and axes"), "core:about", "about"),
            Link(_("Governance"), "core:governance", "governance"),
            Link(_("Partners"), "core:partners", "partners"),
        ),
    ),
    Menu(
        _("Research"),
        (
            Link(_("Research axes"), "core:axes"),
            Link(_("Publications"), "research:publications"),
            Link(_("Datasets"), "research:datasets"),
            Link(_("Models and code"), "research:models"),
            Link(_("Projects"), "projects:list"),
        ),
    ),
    Menu(_("Members"), (Link(_("Members"), "directory:list"),)),
    Menu(
        _("Training and news"),
        (
            Link(_("Training courses"), "training:list"),
            Link(_("Webinars"), "training:webinars"),
            Link(_("News and calls"), "news:list"),
        ),
    ),
    Menu(_("Contact"), (Link(_("Contact"), "core:contact", "contact"),)),
)

FOOTER_LINKS = (
    Link(_("Legal notice"), "core:legal_notice", "legal-notice"),
    Link(_("Privacy policy"), "core:privacy", "privacy"),
    Link(_("Contact"), "core:contact", "contact"),
)


def _resolve(links, published, current_path):
    resolved = []
    for link in links:
        if link.page_slug and link.page_slug not in published:
            continue
        try:
            url = reverse(link.url_name)
        except NoReverseMatch:
            url = None  # module à venir
        resolved.append(
            {
                "label": link.label,
                "url": url,
                "current": url is not None and current_path.startswith(url),
            }
        )
    return resolved


def build(current_path):
    """Menus prêts à afficher. Un menu d'un seul lien devient un lien direct."""
    published = set(
        Page.objects.filter(status=Page.Status.PUBLISHED).values_list("slug", flat=True)
    )
    menus = []
    for menu in MAIN_MENU:
        links = _resolve(menu.links, published, current_path)
        if links:
            menus.append(
                {
                    "label": menu.label,
                    "links": links,
                    "single": links[0] if len(menu.links) == 1 else None,
                    "current": any(link["current"] for link in links),
                }
            )
    return {"menus": menus, "footer": _resolve(FOOTER_LINKS, published, current_path)}
