from urllib.parse import urlsplit

from django.conf import settings
from django.db import connection
from django.db.models import Count, F, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import Resolver404, resolve, reverse, translate_url
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from apps.members.models import Axis, Institution, Member
from apps.research.models import AIModel, Dataset, Publication
from apps.research.views import published, published_publications

from .i18n import fallback_notice
from .models import HomeFeature, Page, PartnershipStep, SiteSettings, Standard

ACTIVE_MEMBERS = Q(members__status=Member.Status.ACTIVE)


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        publications = published_publications()
        context["counters"] = [
            (_("Publications"), publications.count(), "document"),
            (_("Datasets"), published(Dataset).count(), "database"),
            (_("Models and code"), published(AIModel).count(), "chip"),
            (
                _("Active members"),
                Member.objects.filter(status=Member.Status.ACTIVE).count(),
                "users",
            ),
        ]
        context["features"] = HomeFeature.objects.filter(is_visible=True)
        context["latest_publications"] = publications.order_by("-year", "-created_at")[:3]
        context["axes"] = Axis.objects.annotate(
            member_count=Count("members", filter=ACTIVE_MEMBERS)
        )
        context["partners"] = Institution.objects.filter(is_partner=True)
        # Raccourcis « Modifier » de la barre d'administration (components/admin_bar.html).
        context["edit_targets"] = [
            SiteSettings.load(),
            HomeFeature,
            Axis,
            Publication,
            Institution,
        ]
        return context


class PageView(TemplateView):
    """Page éditoriale publiée (module M1). Les pages fixes ont leur adresse, les pages
    ajoutées dans l'administration sont servies sous /pages/<slug>/."""

    template_name = "core/page.html"
    slug = None
    section = None  # rubrique du menu, affichée dans le fil d'Ariane
    edit_models = ()  # listes de la page modifiables dans l'administration

    def get_page(self):
        slug = self.kwargs.get("slug")
        if slug is None:
            slug = self.slug
        elif slug in Page.ROUTES:
            raise Http404  # une page fixe n'a qu'une adresse
        return get_object_or_404(Page, slug=slug, status=Page.Status.PUBLISHED)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = self.get_page()
        context["page"] = page
        context["section"] = self.section
        if self.section is None and page.menu == Page.Menu.ABOUT:
            context["section"] = _("About")
        context["fallback"] = fallback_notice(page, "body")
        context["edit_targets"] = [page, *self.edit_models]
        return context


class AboutView(PageView):
    template_name = "core/about.html"
    slug = "about"
    section = _("About")
    edit_models = (Standard, Member)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Objectifs à 12 mois de la spec §1.4, cibles réglées dans l'administration.
        goals = SiteSettings.load()
        context["edit_targets"].append(goals)
        members = Member.objects.filter(status=Member.Status.ACTIVE)
        publication_count = published_publications().count()
        # Profil complet : photo et biographie dans chaque langue éditoriale.
        complete_profiles = members.exclude(photo="")
        for code in settings.DAARA_EDITORIAL_LANGUAGES:
            complete_profiles = complete_profiles.exclude(**{f"bio_{code}": ""})

        context["axes"] = Axis.objects.all()
        context["figures"] = [
            (_("Active members"), members.count(), "users"),
            (_("Publications"), publication_count, "document"),
            (
                _("Partner universities"),
                Institution.objects.filter(is_partner=True).count(),
                "handshake",
            ),
            (_("Research axes"), Axis.objects.count(), "pin"),
        ]
        # Les profils avec photo d'abord : l'aperçu de l'équipe reste vivant.
        context["team"] = (
            members.select_related("user", "grade")
            .prefetch_related("affiliations__institution")
            .order_by(F("photo_width").desc(nulls_last=True), "user__last_name")[:8]
        )
        context["objectives"] = [
            {
                "label": label,
                "value": value,
                "target": target,
                "percent": min(100, round(100 * value / target)),
            }
            for label, value, target in [
                (_("Referenced publications"), publication_count, goals.goal_publications),
                (_("Complete member profiles"), complete_profiles.count(), goals.goal_profiles),
                (
                    _("Datasets published with a DOI"),
                    published(Dataset).exclude(doi="").count(),
                    goals.goal_datasets,
                ),
                (_("Webinars archived with a DOI"), 0, goals.goal_webinars),
            ]
            if target
        ]
        context["standards"] = Standard.objects.filter(is_visible=True)
        return context


class PartnersView(PageView):
    template_name = "core/partners.html"
    slug = "partners"
    section = _("About")
    edit_models = (Institution, PartnershipStep)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["institutions"] = Institution.objects.filter(is_partner=True).annotate(
            member_count=Count(
                "affiliations",
                filter=Q(affiliations__member__status=Member.Status.ACTIVE),
            )
        )
        # Procédure d'adhésion de la gouvernance (spec §2.2).
        context["steps"] = PartnershipStep.objects.filter(is_visible=True)
        return context


class AxesView(TemplateView):
    template_name = "core/axes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["axes"] = Axis.objects.annotate(
            member_count=Count("members", filter=ACTIVE_MEMBERS)
        ).prefetch_related("role_assignments__user__member")
        context["edit_targets"] = [Axis]
        return context


class LogoSheetView(TemplateView):
    """Planche du logo aux tailles et sur les fonds exigés par la charte, en développement."""

    template_name = "core/logo_sheet.html"

    def get(self, request, *args, **kwargs):
        if not settings.DEBUG:
            raise Http404
        return super().get(request, *args, **kwargs)


def healthz(request):
    """Sonde de disponibilité pour Docker et le reverse proxy ; vérifie aussi la base."""
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    return HttpResponse("ok", content_type="text/plain")


@require_GET
def switch_language(request, lang):
    """Change de langue en gardant la page courante, sinon renvoie à l'accueil (spec §5.3).

    Un lien GET plutôt que le formulaire POST de Django : sans jeton CSRF dans la page,
    les pages publiques restent cachables (spec §7.5).
    """
    if lang not in dict(settings.LANGUAGES):
        raise Http404

    next_url = request.GET.get("next", "")
    target = None
    if next_url and url_has_allowed_host_and_scheme(
        next_url, allowed_hosts={request.get_host()}, require_https=request.is_secure()
    ):
        try:
            resolve(urlsplit(next_url).path)
        except Resolver404:
            pass
        else:
            target = translate_url(next_url, lang)
    if target is None:
        with translation.override(lang):
            target = reverse("core:home")

    response = HttpResponseRedirect(target)
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        lang,
        max_age=settings.LANGUAGE_COOKIE_AGE,
        path=settings.LANGUAGE_COOKIE_PATH,
        domain=settings.LANGUAGE_COOKIE_DOMAIN,
        secure=settings.LANGUAGE_COOKIE_SECURE,
        httponly=settings.LANGUAGE_COOKIE_HTTPONLY,
        samesite=settings.LANGUAGE_COOKIE_SAMESITE,
    )
    return response
