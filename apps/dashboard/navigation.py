"""Sidebar de l'espace : un seul menu, construit à partir de l'ensemble des rôles actifs.

Chaque lien déclare la condition qui l'affiche ; la même condition protège la vue
(voir DashboardMixin), si bien que le menu et les accès ne peuvent pas diverger.
"""

from collections.abc import Callable
from dataclasses import dataclass

from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.members.backends import is_back_office
from apps.members.permissions import Module, can, can_any

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


def _may_change(perm):
    """Lien vers l'administration : droits tirés des rôles (apps/members/backends.py), qui
    exigent en plus le statut « équipe »."""

    def allowed(user):
        return user.has_perm(perm)

    return allowed


@dataclass(frozen=True)
class Link:
    label: str
    url_name: str
    allowed: Callable


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
            Link(
                _("Home page and footer"),
                "admin:core_sitesettings_changelist",
                _may_change("core.change_sitesettings"),
            ),
            Link(_("Pages"), "admin:core_page_changelist", _may_change("core.change_page")),
            Link(
                _("Research axes"),
                "admin:members_axis_changelist",
                _may_change("members.change_axis"),
            ),
            Link(
                _("Publications"),
                "admin:research_publication_changelist",
                _may_change("research.change_publication"),
            ),
            Link(
                _("Members"),
                "admin:members_member_changelist",
                _may_change("members.change_member"),
            ),
            Link(
                _("Partner institutions"),
                "admin:members_institution_changelist",
                _may_change("members.change_institution"),
            ),
        ),
    ),
    Section(
        _("Administration"),
        (
            Link(
                _("Members and roles"),
                "admin:members_roleassignment_changelist",
                _may_change("members.change_roleassignment"),
            ),
            Link(
                _("Action log"),
                "admin:admin_logentry_changelist",
                _may_change("admin.view_logentry"),
            ),
            Link(_("All the administration"), "admin:index", is_back_office),
        ),
    ),
)

_LINKS = {link.url_name: link for section in SECTIONS for link in section.links}


def is_allowed(user, url_name):
    return _LINKS[url_name].allowed(user)


def sidebar(user, current=None):
    """Sections visibles pour `user` : une section sans lien autorisé n'apparaît pas."""
    sections = []
    for section in SECTIONS:
        links = [
            {
                "label": link.label,
                "url": reverse(link.url_name),
                "current": link.url_name == current,
            }
            for link in section.links
            if link.allowed(user)
        ]
        if links:
            sections.append({"title": section.title, "links": links})
    return sections
