"""Registre des pages « Gérer » de l'espace : tout ce que montre le site public s'y modifie.

Chaque contenu déclare son formulaire, les colonnes de sa liste et ses champs de recherche ;
les vues génériques de views.py font le reste. Les droits viennent des rôles
(permissions.MANAGE_RULES), jamais de l'administration Django.
"""

from dataclasses import dataclass, field

from django.db.models import Q
from django.urls import reverse
from django.utils.text import capfirst
from django.utils.translation import gettext_lazy as _

from apps.core.models import HomeFeature, Page, PartnershipStep, SiteSettings, Standard
from apps.members.models import Axis, Grade, Institution, Member, RoleAssignment, User
from apps.projects.models import Project
from apps.research.models import AIModel, Dataset, Publication

from . import forms


@dataclass(frozen=True)
class Column:
    attr: str  # attribut ou méthode de l'objet ; get_<champ>_display pour un choix
    label: str = ""
    kind: str = "text"  # text, bool, image


@dataclass(frozen=True)
class Managed:
    key: str
    model: type
    form: type
    columns: tuple[Column, ...]
    search: tuple[str, ...] = ()
    formset: object = None
    singleton: bool = False
    select_related: tuple[str, ...] = field(default=())
    prefetch_related: tuple[str, ...] = field(default=())
    ordering: tuple[str, ...] = field(default=())  # sinon, l'ordre du modèle

    @property
    def title(self):
        return capfirst(self.model._meta.verbose_name_plural)

    @property
    def verbose_name(self):
        return self.model._meta.verbose_name

    def headers(self):
        return [column.label or self._label(column.attr) for column in self.columns]

    def _label(self, attr):
        name = attr.removeprefix("get_").removesuffix("_display")
        return capfirst(self.model._meta.get_field(name).verbose_name)

    def queryset(self, query=""):
        objects = self.model.objects.select_related(*self.select_related).prefetch_related(
            *self.prefetch_related
        )
        if self.ordering:
            objects = objects.order_by(*self.ordering)
        if query and self.search:
            condition = Q()
            for name in self.search:
                condition |= Q(**{f"{name}__icontains": query})
            objects = objects.filter(condition).distinct()
        return objects

    def cells(self, obj):
        values = []
        for column in self.columns:
            value = getattr(obj, column.attr, "")
            values.append({"value": value() if callable(value) else value, "kind": column.kind})
        return values

    def list_url(self):
        return reverse("dashboard:manage_list", args=[self.key])

    def edit_url(self, obj):
        return reverse("dashboard:manage_edit", args=[self.key, obj.pk])


PRODUCTION_SEARCH = ("title", "authorships__name")

REGISTRY = {
    managed.key: managed
    for managed in (
        Managed("site", SiteSettings, forms.SiteSettingsForm, (), singleton=True),
        Managed(
            "home-cards",
            HomeFeature,
            forms.HomeFeatureForm,
            (
                Column("title"),
                Column("get_destination_display"),
                Column("order"),
                Column("is_visible", kind="bool"),
            ),
        ),
        Managed(
            "pages",
            Page,
            forms.PageForm,
            (Column("title"), Column("slug"), Column("get_status_display"), Column("updated_at")),
            search=("title_fr", "title_en", "body_fr", "body_en"),
        ),
        Managed(
            "standards",
            Standard,
            forms.StandardForm,
            (
                Column("name"),
                Column("description"),
                Column("order"),
                Column("is_visible", kind="bool"),
            ),
        ),
        Managed(
            "partnership-steps",
            PartnershipStep,
            forms.PartnershipStepForm,
            (Column("title"), Column("order"), Column("is_visible", kind="bool")),
        ),
        Managed(
            "axes",
            Axis,
            forms.AxisForm,
            (Column("name"), Column("get_icon_display"), Column("order")),
        ),
        Managed(
            "publications",
            Publication,
            forms.PublicationForm,
            (
                Column("title"),
                Column("year"),
                Column("get_kind_display"),
                Column("get_status_display"),
            ),
            search=(*PRODUCTION_SEARCH, "doi", "venue"),
            formset=forms.authorship_formset(Publication),
        ),
        Managed(
            "datasets",
            Dataset,
            forms.DatasetForm,
            (
                Column("title"),
                Column("year"),
                Column("get_access_display"),
                Column("get_status_display"),
            ),
            search=(*PRODUCTION_SEARCH, "doi"),
            formset=forms.authorship_formset(Dataset),
        ),
        Managed(
            "models",
            AIModel,
            forms.AIModelForm,
            (
                Column("title"),
                Column("year"),
                Column("get_kind_display"),
                Column("get_status_display"),
            ),
            search=(*PRODUCTION_SEARCH, "huggingface_id"),
            formset=forms.authorship_formset(AIModel),
        ),
        Managed(
            "projects",
            Project,
            forms.ProjectForm,
            (Column("title"), Column("acronym"), Column("get_status_display"), Column("starts_on")),
            search=("title_fr", "title_en", "acronym"),
        ),
        Managed(
            "members",
            Member,
            forms.MemberForm,
            (
                Column("photo", kind="image"),
                Column("__str__", _("Name")),
                Column("position"),
                Column("primary_institution", _("Institution")),
                Column("get_status_display"),
            ),
            search=("user__first_name", "user__last_name", "position_fr", "position_en"),
            select_related=("user",),
            prefetch_related=("affiliations__institution",),
        ),
        Managed(
            "institutions",
            Institution,
            forms.InstitutionForm,
            (
                Column("logo", kind="image"),
                Column("name"),
                Column("acronym"),
                Column("city"),
                Column("is_partner", kind="bool"),
            ),
            search=("name_fr", "name_en", "acronym", "city"),
        ),
        Managed("grades", Grade, forms.GradeForm, (Column("name"), Column("order"))),
        Managed(
            "accounts",
            User,
            forms.AccountForm,
            (
                Column("username"),
                Column("get_full_name", _("Name")),
                Column("email"),
                Column("is_active", kind="bool"),
            ),
            search=("username", "first_name", "last_name", "email"),
            ordering=("last_name", "first_name", "username"),
        ),
        Managed(
            "roles",
            RoleAssignment,
            forms.RoleAssignmentForm,
            (
                Column("user"),
                Column("get_role_display"),
                Column("axis"),
                Column("starts_on"),
                Column("expires_on"),
            ),
            search=("user__username", "user__first_name", "user__last_name"),
            select_related=("user", "axis"),
        ),
    )
}


def for_model(model):
    return next((managed for managed in REGISTRY.values() if managed.model is model), None)
