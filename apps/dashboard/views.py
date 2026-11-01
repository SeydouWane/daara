from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import ADDITION, CHANGE, DELETION, LogEntry
from django.contrib.admin.utils import construct_change_message
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Count, ProtectedError, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import ListView, TemplateView, UpdateView

from apps.core.models import Page
from apps.members.models import Axis, Institution, Member
from apps.members.permissions import active_assignments, may
from apps.projects.models import Project

from . import manage, navigation
from .forms import ProfileForm


class DashboardMixin(LoginRequiredMixin):
    """Vues de l'espace : connexion obligatoire, accès réglé par le registre du sidebar."""

    url_name = None

    def has_access(self, user):
        return navigation.is_allowed(user, self.url_name)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not self.has_access(request.user):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sidebar"] = navigation.sidebar(self.request.user, self.request.path)
        context["assignments"] = active_assignments(self.request.user)
        return context


class HomeView(DashboardMixin, TemplateView):
    template_name = "dashboard/home.html"
    url_name = "dashboard:home"


class ProfileView(DashboardMixin, UpdateView):
    template_name = "dashboard/profile.html"
    url_name = "dashboard:profile"
    form_class = ProfileForm
    success_url = reverse_lazy("dashboard:profile")

    def get_object(self, queryset=None):
        return self.request.user.member

    def form_valid(self, form):
        messages.success(self.request, _("Your profile has been saved."))
        return super().form_valid(form)


class ValidationQueueView(DashboardMixin, TemplateView):
    """File de validation (module M9). Elle se remplit avec les productions, en phase 2."""

    template_name = "dashboard/validation.html"
    url_name = "dashboard:validation"


def _missing_languages(obj, field):
    """Langues manquantes d'un champ traduit déjà renseigné dans au moins une langue."""
    values = {code: getattr(obj, f"{field}_{code}") for code in settings.DAARA_EDITORIAL_LANGUAGES}
    if not any(values.values()):
        return []
    return [code for code, value in values.items() if not value]


class TranslationsView(DashboardMixin, TemplateView):
    """Contenus à traduire, du plus ancien au plus récent (spec §5.4)."""

    template_name = "dashboard/translations.html"
    url_name = "dashboard:translations"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        sources = [
            (_("Member biography"), Member.objects.select_related("user"), "bio"),
            (_("Axis description"), Axis.objects.all(), "description"),
            (_("Project description"), Project.objects.all(), "description"),
            (_("Editorial page"), Page.objects.all(), "body"),
        ]
        user = self.request.user
        items = []
        for kind, queryset, field in sources:
            managed = manage.for_model(queryset.model)
            editable = may(user, "change", queryset.model)
            for obj in queryset:
                missing = _missing_languages(obj, field)
                if missing:
                    items.append(
                        {
                            "kind": kind,
                            "label": str(obj),
                            "missing": missing,
                            "updated_at": obj.updated_at,
                            "url": managed.edit_url(obj) if editable else None,
                        }
                    )
        context["items"] = sorted(items, key=lambda item: item["updated_at"])
        return context


class IndicatorsView(DashboardMixin, TemplateView):
    """Premiers indicateurs ; le tableau de bord observateur complet arrive au lot 4."""

    template_name = "dashboard/indicators.html"
    url_name = "dashboard:indicators"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        active = Q(affiliations__member__status=Member.Status.ACTIVE)
        primary = Q(affiliations__is_primary=True)
        institutions = Institution.objects.annotate(
            member_count=Count("affiliations", filter=active & primary)
        ).order_by("-member_count", "name")
        total = sum(institution.member_count for institution in institutions)
        context["counters"] = [
            (_("Active members"), Member.objects.filter(status=Member.Status.ACTIVE).count()),
            (_("Alumni"), Member.objects.filter(status=Member.Status.ALUMNI).count()),
            (_("Partner institutions"), Institution.objects.filter(is_partner=True).count()),
            (_("Research axes"), Axis.objects.count()),
        ]
        context["distribution"] = [
            {
                "institution": institution,
                "count": institution.member_count,
                "share": round(100 * institution.member_count / total) if total else 0,
            }
            for institution in institutions
        ]
        return context


class ManageMixin(DashboardMixin):
    """Pages « Gérer » : le contenu vient du registre (manage.py), les droits des rôles."""

    action = "view"

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.managed = manage.REGISTRY.get(kwargs["key"])
        if self.managed is None:
            raise Http404

    def has_access(self, user):
        return may(user, self.action, self.managed.model)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        model, singleton = self.managed.model, self.managed.singleton
        context["managed"] = self.managed
        context["can_add"] = not singleton and may(self.request.user, "add", model)
        context["can_delete"] = not singleton and may(self.request.user, "delete", model)
        return context


class ManageListView(ManageMixin, ListView):
    template_name = "dashboard/manage/list.html"
    paginate_by = 25

    def get(self, request, *args, **kwargs):
        if self.managed.singleton:
            return redirect(self.managed.edit_url(self.managed.model.load()))
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        return self.managed.queryset(self.request.GET.get("q", "").strip())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["headers"] = self.managed.headers()
        context["rows"] = [
            {"object": obj, "url": self.managed.edit_url(obj), "cells": self.managed.cells(obj)}
            for obj in context["object_list"]
        ]
        context["query"] = query = self.request.GET.get("q", "")
        context["query_string"] = urlencode({"q": query}) if query else ""
        return context


class ManageEditView(ManageMixin, UpdateView):
    """Ajout (sans identifiant dans l'adresse) ou modification d'un contenu, avec ses auteurs
    pour une production. Chaque enregistrement est inscrit au journal des actions."""

    template_name = "dashboard/manage/form.html"

    def has_access(self, user):
        return may(user, "change" if "pk" in self.kwargs else "add", self.managed.model)

    def get_form_class(self):
        return self.managed.form

    def get_object(self, queryset=None):
        if "pk" not in self.kwargs:
            return None
        return get_object_or_404(self.managed.model, pk=self.kwargs["pk"])

    def get_formset(self):
        if self.managed.formset is None:
            return None
        data = (self.request.POST, self.request.FILES) if self.request.method == "POST" else ()
        instance = self.object or self.managed.model()
        return self.managed.formset(*data, instance=instance, prefix="authors")

    def get_context_data(self, **kwargs):
        kwargs.setdefault("formset", self.get_formset())
        return super().get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form, formset = self.get_form(), self.get_formset()
        if form.is_valid() and (formset is None or formset.is_valid()):
            return self.save(form, formset)
        return self.render_to_response(self.get_context_data(form=form, formset=formset))

    @transaction.atomic
    def save(self, form, formset):
        is_new = self.object is None
        if is_new and hasattr(form.instance, "created_by_id"):
            form.instance.created_by = self.request.user
        obj = form.save()
        if formset is not None:
            formset.instance = obj
            formset.save()
        LogEntry.objects.log_actions(
            self.request.user.pk,
            [obj],
            ADDITION if is_new else CHANGE,
            construct_change_message(form, [formset] if formset else [], is_new),
            single_object=True,
        )
        messages.success(self.request, _("“%(object)s” has been saved.") % {"object": obj})
        if self.managed.singleton or "continue" in self.request.POST:
            return redirect(self.managed.edit_url(obj))
        return redirect(self.managed.list_url())


class ManageDeleteView(ManageMixin, TemplateView):
    template_name = "dashboard/manage/delete.html"
    action = "delete"

    def has_access(self, user):
        return not self.managed.singleton and super().has_access(user)

    def get_object(self):
        return get_object_or_404(self.managed.model, pk=self.kwargs["pk"])

    def get_context_data(self, **kwargs):
        return super().get_context_data(object=self.get_object(), **kwargs)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        label = str(obj)
        if obj == request.user:
            messages.error(request, _("You cannot delete your own account."))
            return redirect(self.managed.edit_url(obj))
        try:
            with transaction.atomic():
                LogEntry.objects.log_actions(request.user.pk, [obj], DELETION, single_object=True)
                obj.delete()
        except ProtectedError:
            messages.error(
                request,
                _("“%(object)s” is still used elsewhere and cannot be deleted.")
                % {"object": label},
            )
            return redirect(self.managed.edit_url(obj))
        messages.success(request, _("“%(object)s” has been deleted.") % {"object": label})
        return redirect(self.managed.list_url())


class ActionLogView(DashboardMixin, ListView):
    """Journal des ajouts, modifications et suppressions faits dans l'espace (spec §3.3)."""

    template_name = "dashboard/action_log.html"
    url_name = "dashboard:action_log"
    paginate_by = 50

    def get_queryset(self):
        return LogEntry.objects.select_related("user", "content_type")
