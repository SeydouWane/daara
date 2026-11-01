"""Menus de la vitrine publique (module M1).

Un lien vers un module pas encore construit s'affiche « bientôt » sans être cliquable : il
devient un vrai lien dès que son URL existe, sans retoucher ce fichier. Un lien vers une page
éditoriale n'apparaît que si la page est publiée. Les pages ajoutées dans l'administration
s'ajoutent au menu choisi dans leur champ `menu`.
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
    page_menu: str = ""  # valeur de Page.menu des pages ajoutées à ce menu


MAIN_MENU = (
    Menu(
        _("About"),
        (
            Link(_("Mission and axes"), "core:about", "about"),
            Link(_("Governance"), "core:governance", "governance"),
            Link(_("Partners"), "core:partners", "partners"),
        ),
        Page.Menu.ABOUT,
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


def _added_pages(pages, page_menu, current_path):
    links = []
    for page in pages:
        if page_menu and page.menu == page_menu and not page.is_built_in:
            url = page.get_absolute_url()
            links.append({"label": page.title, "url": url, "current": current_path == url})
    return links


def build(current_path):
    """Menus prêts à afficher. Un menu d'un seul lien devient un lien direct."""
    pages = list(Page.objects.filter(status=Page.Status.PUBLISHED))
    published = {page.slug for page in pages}
    menus = []
    for menu in MAIN_MENU:
        links = _resolve(menu.links, published, current_path)
        links += _added_pages(pages, menu.page_menu, current_path)
        if links:
            menus.append(
                {
                    "label": menu.label,
                    "links": links,
                    "single": links[0] if len(links) == 1 and len(menu.links) == 1 else None,
                    "current": any(link["current"] for link in links),
                }
            )
    footer = _resolve(FOOTER_LINKS, published, current_path)
    return {
        "menus": menus,
        "footer": footer + _added_pages(pages, Page.Menu.FOOTER, current_path),
        "contact": reverse("core:contact") if "contact" in published else None,
    }
