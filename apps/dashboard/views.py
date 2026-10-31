from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.urls import reverse, reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, UpdateView

from apps.members.models import Axis, Institution, Member
from apps.members.permissions import active_assignments

from . import navigation
from .forms import ProfileForm


class DashboardMixin(LoginRequiredMixin):
    """Vues de l'espace : connexion obligatoire, accès réglé par le registre du sidebar."""

    url_name = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated and not navigation.is_allowed(request.user, self.url_name):
            raise PermissionDenied
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["sidebar"] = navigation.sidebar(self.request.user, self.url_name)
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
            (_("Member biography"), Member.objects.select_related("user"), "bio", "member"),
            (_("Axis description"), Axis.objects.all(), "description", "axis"),
        ]
        items = []
        for kind, queryset, field, model_name in sources:
            for obj in queryset:
                missing = _missing_languages(obj, field)
                if missing:
                    items.append(
                        {
                            "kind": kind,
                            "label": str(obj),
                            "missing": missing,
                            "updated_at": obj.updated_at,
                            "url": reverse(f"admin:members_{model_name}_change", args=[obj.pk]),
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
