from django.db.models import Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from apps.core.i18n import fallback_notice
from apps.members.models import Axis, Member

from . import citation
from .models import Authorship, Publication


def published_publications():
    """Publications visibles du public, auteurs préchargés dans l'ordre."""
    return Publication.objects.filter(status=Publication.Status.PUBLISHED).prefetch_related(
        Prefetch("authorships", queryset=Authorship.objects.select_related("member"))
    )


class PublicationListView(ListView):
    """Liste des publications (module M3) : recherche, filtres par année, type, axe et auteur.
    Avec HTMX, seule la liste est renvoyée."""

    template_name = "research/publication_list.html"
    context_object_name = "publications"
    paginate_by = 20

    def get_queryset(self):
        params = self.request.GET
        publications = published_publications()
        if query := params.get("q", "").strip():
            publications = publications.filter(
                Q(title__icontains=query)
                | Q(venue__icontains=query)
                | Q(authorships__name__icontains=query)
            )
        if params.get("kind") in Publication.Kind.values:
            publications = publications.filter(kind=params["kind"])
        if params.get("year", "").isdigit():
            publications = publications.filter(year=params["year"])
        if params.get("axis"):
            publications = publications.filter(axis__slug=params["axis"])
        if params.get("member"):
            publications = publications.filter(authorships__member__slug=params["member"])
        return publications.distinct().order_by("-year", "title")

    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            return ["research/_publication_results.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        published = Publication.objects.filter(status=Publication.Status.PUBLISHED)
        context["kinds"] = Publication.Kind.choices
        context["years"] = (
            published.exclude(year=None).values_list("year", flat=True).distinct().order_by("-year")
        )
        context["axes"] = Axis.objects.filter(productions__in=published).distinct()
        context["authors"] = (
            Member.objects.filter(authorships__production__in=published)
            .select_related("user")
            .distinct()
        )
        context["filters"] = self.request.GET
        query = self.request.GET.copy()
        query.pop("page", None)
        context["query_string"] = query.urlencode()
        context["edit_targets"] = [Publication]
        return context


class PublicationDetailView(DetailView):
    template_name = "research/publication_detail.html"
    context_object_name = "publication"

    def get_queryset(self):
        return published_publications().select_related("axis")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        publication = self.object
        context["fallback"] = (
            fallback_notice(publication, "abstract") if publication.abstract else None
        )
        context["reference"] = citation.reference(publication)
        context["bibtex"] = citation.bibtex(publication)
        context["edit_targets"] = [publication]
        return context


def publication_bibtex(request, slug):
    publication = get_object_or_404(published_publications(), slug=slug)
    return HttpResponse(
        citation.bibtex(publication),
        content_type="application/x-bibtex; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{publication.slug}.bib"'},
    )
