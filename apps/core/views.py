from urllib.parse import urlsplit

from django.conf import settings
from django.db import connection
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import NoReverseMatch, Resolver404, resolve, reverse, translate_url
from django.utils import translation
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_GET
from django.views.generic import TemplateView

from apps.members.models import Axis, Institution, Member

from .i18n import fallback_notice
from .models import Page

ACTIVE_MEMBERS = Q(members__status=Member.Status.ACTIVE)


def _url_or_none(url_name):
    """URL d'un module, ou None tant qu'il n'est pas construit."""
    try:
        return reverse(url_name)
    except NoReverseMatch:
        return None


class HomeView(TemplateView):
    template_name = "core/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Publications, données et formations restent à 0 jusqu'aux modules M3, M4 et M7.
        context["counters"] = [
            (_("Publications"), 0, "document"),
            (_("Datasets"), 0, "database"),
            (_("Training courses"), 0, "cap"),
            (
                _("Active members"),
                Member.objects.filter(status=Member.Status.ACTIVE).count(),
                "users",
            ),
        ]
        context["offer"] = [
            {
                "icon": icon,
                "title": title,
                "text": text,
                "url": _url_or_none(url_name),
            }
            for icon, title, text, url_name in [
                (
                    "document",
                    _("Publications"),
                    _("Articles, papers and theses, imported by DOI and exported to BibTeX."),
                    "research:publications",
                ),
                (
                    "database",
                    _("Datasets"),
                    _("African corpora and data deposited on Zenodo, with a DOI and a citation."),
                    "research:datasets",
                ),
                (
                    "chip",
                    _("Models and code"),
                    _("Models and demonstrators synchronised from Hugging Face and GitHub."),
                    "research:models",
                ),
                (
                    "cap",
                    _("Training"),
                    _("Courses, archived webinars and teaching materials with a DOI."),
                    "training:list",
                ),
            ]
        ]
        context["latest"] = [
            ("actualites", _("Latest news"), _("No news yet."), "document"),
            (
                "productions",
                _("Latest research outputs"),
                _("No research outputs yet."),
                "database",
            ),
        ]
        context["axes"] = Axis.objects.annotate(
            member_count=Count("members", filter=ACTIVE_MEMBERS)
        )
        context["partners"] = Institution.objects.filter(is_partner=True)
        return context


class PageView(TemplateView):
    """Page éditoriale publiée, identifiée par son `slug` (module M1)."""

    template_name = "core/page.html"
    slug = None
    section = None  # rubrique du menu, affichée dans le fil d'Ariane

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        page = get_object_or_404(Page, slug=self.slug, status=Page.Status.PUBLISHED)
        context["page"] = page
        context["section"] = self.section
        context["fallback"] = fallback_notice(page, "body")
        return context


class AboutView(PageView):
    template_name = "core/about.html"
    slug = "about"
    section = _("About")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["axes"] = Axis.objects.all()
        return context


class PartnersView(PageView):
    template_name = "core/partners.html"
    slug = "partners"
    section = _("About")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["institutions"] = Institution.objects.filter(is_partner=True).annotate(
            member_count=Count(
                "affiliations",
                filter=Q(affiliations__member__status=Member.Status.ACTIVE),
            )
        )
        return context


class AxesView(TemplateView):
    template_name = "core/axes.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["axes"] = Axis.objects.annotate(
            member_count=Count("members", filter=ACTIVE_MEMBERS)
        ).prefetch_related("role_assignments__user__member")
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
