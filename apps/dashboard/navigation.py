"""Sidebar de l'espace : un seul menu, construit à partir de l'ensemble des rôles actifs.

Chaque lien déclare la condition qui l'affiche ; la même condition protège la vue
(voir DashboardMixin et ManageMixin), si bien que le menu et les accès ne peuvent pas
diverger.
"""

from collections.abc import Callable
from dataclasses import dataclass

from django.contrib.admin.models import LogEntry
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.members.permissions import Module, can, can_any, may

from . import manage

REVIEWED_MODULES = (
    Module.PROFILES,
    Module.PUBLICATIONS,
    Module.DATASETS,
    Module.MODELS,
    Module.PROJECTS,
    Module.TRAININGS,
    Module.NEWS,
)


def _everyone(user):
    return True


def _has_profile(user):
    return hasattr(user, "member")


def _reviewer(user):
    return can_any(user, "V", *REVIEWED_MODULES)


def _editor(user):
    return can(user, "P", Module.EDITORIAL_PAGES)


def _monitoring(user):
    return can(user, "L", Module.DASHBOARD)


def _action_log(user):
    return may(user, "view", LogEntry)


@dataclass(frozen=True)
class Link:
    label: str
    url_name: str
    allowed: Callable
    args: tuple = ()


def _manage(label, key):
    """Lien vers une page « Gérer », affiché si l'utilisateur peut voir ce contenu."""
    model = manage.REGISTRY[key].model

    def allowed(user):
        return may(user, "view", model)

    return Link(label, "dashboard:manage_list", allowed, (key,))


@dataclass(frozen=True)
class Section:
    title: str
    links: tuple[Link, ...]


SECTIONS = (
    Section(
        _("My space"),
        (
            Link(_("Overview"), "dashboard:home", _everyone),
            Link(_("My profile"), "dashboard:profile", _has_profile),
        ),
    ),
    Section(_("Review"), (Link(_("Validation queue"), "dashboard:validation", _reviewer),)),
    Section(_("Editorial"), (Link(_("Translations"), "dashboard:translations", _editor),)),
    Section(_("Monitoring"), (Link(_("Indicators"), "dashboard:indicators", _monitoring),)),
    # Tout ce que montre la vitrine, dans l'ordre de ses menus.
    Section(
        _("Public site"),
        (
            _manage(_("Home page and footer"), "site"),
            _manage(_("Home page cards"), "home-cards"),
            _manage(_("Pages"), "pages"),
            _manage(_("Open standards"), "standards"),
            _manage(_("Partnership steps"), "partnership-steps"),
        ),
    ),
    Section(
        _("Catalogue"),
        (
            _manage(_("Research axes"), "axes"),
            _manage(_("Publications"), "publications"),
            _manage(_("Datasets"), "datasets"),
            _manage(_("Models and code"), "models"),
            _manage(_("Projects"), "projects"),
            _manage(_("Members"), "members"),
            _manage(_("Institutions"), "institutions"),
        ),
    ),
    Section(
        _("Administration"),
        (
            _manage(_("Accounts"), "accounts"),
            _manage(_("Roles"), "roles"),
            _manage(_("Grades"), "grades"),
            Link(_("Action log"), "dashboard:action_log", _action_log),
        ),
    ),
)

# Vues propres de l'espace (sans paramètre) : leur condition d'accès, par nom d'URL.
_LINKS = {link.url_name: link for section in SECTIONS for link in section.links if not link.args}


def is_allowed(user, url_name):
    return _LINKS[url_name].allowed(user)


def sidebar(user, path=""):
    """Sections visibles pour `user` : une section sans lien autorisé n'apparaît pas. Le lien
    courant est celui dont l'adresse commence la page affichée (ajout, modification…)."""
    home = reverse("dashboard:home")
    sections = []
    for section in SECTIONS:
        links = []
        for link in section.links:
            if not link.allowed(user):
                continue
            url = reverse(link.url_name, args=link.args)
            current = path == url or (url != home and path.startswith(url))
            links.append({"label": link.label, "url": url, "current": current})
        if links:
            sections.append({"title": section.title, "links": links})
    return sections
