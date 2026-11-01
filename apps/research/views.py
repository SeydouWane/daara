import json

from django.db.models import Prefetch, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from apps.core.i18n import fallback_notice
from apps.members.models import Axis, Member

from . import citation
from .models import AIModel, Authorship, Dataset, Production, Publication


def published(model):
    """Productions visibles du public, auteurs préchargés dans l'ordre."""
    return model.objects.filter(status=Production.Status.PUBLISHED).prefetch_related(
        Prefetch("authorships", queryset=Authorship.objects.select_related("member"))
    )


def published_publications():
    return published(Publication)


class ProductionListView(ListView):
    """Liste filtrable d'un type de production : recherche, année, axe et un champ de choix
    (type, accès…). Avec HTMX, seule la liste est renvoyée."""

    model = None
    paginate_by = 20
    search_fields = ("title", "authorships__name")
    choice_field = None  # champ à choix proposé en filtre
    partial_template = None

    def get_queryset(self):
        params = self.request.GET
        items = published(self.model)
        if query := params.get("q", "").strip():
            condition = Q()
            for name in self.search_fields:
                condition |= Q(**{f"{name}__icontains": query})
            items = items.filter(condition)
        if self.choice_field and params.get(self.choice_field) in self._choices():
            items = items.filter(**{self.choice_field: params[self.choice_field]})
        if params.get("year", "").isdigit():
            items = items.filter(year=params["year"])
        if params.get("axis"):
            items = items.filter(axis__slug=params["axis"])
        if params.get("member"):
            items = items.filter(authorships__member__slug=params["member"])
        return items.distinct().order_by("-year", "title")

    def _choices(self):
        return dict(self.model._meta.get_field(self.choice_field).choices)

    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            return [self.partial_template]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        visible = self.model.objects.filter(status=Production.Status.PUBLISHED)
        if self.choice_field:
            context["choices"] = self._choices().items()
            context["current_choice"] = self.request.GET.get(self.choice_field, "")
        context["years"] = (
            visible.exclude(year=None).values_list("year", flat=True).distinct().order_by("-year")
        )
        context["axes"] = Axis.objects.filter(productions__in=visible).distinct()
        context["authors"] = (
            Member.objects.filter(authorships__production__in=visible)
            .select_related("user")
            .distinct()
        )
        context["filters"] = self.request.GET
        query = self.request.GET.copy()
        query.pop("page", None)
        context["query_string"] = query.urlencode()
        context["edit_targets"] = [self.model]
        return context


class PublicationListView(ProductionListView):
    """Publications (module M3) : recherche dans le titre, les auteurs et la revue."""

    model = Publication
    template_name = "research/publication_list.html"
    partial_template = "research/_publication_results.html"
    context_object_name = "publications"
    search_fields = ("title", "venue", "authorships__name")
    choice_field = "kind"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["kinds"] = Publication.Kind.choices
        return context


class DatasetListView(ProductionListView):
    """Jeux de données (module M4)."""

    model = Dataset
    template_name = "research/production_list.html"
    partial_template = "research/_production_results.html"
    search_fields = ("title", "authorships__name", "covered_languages", "coverage")
    choice_field = "access"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            title=_("Datasets"),
            summary=_(
                "Corpora and data produced by DAARA members, deposited on Zenodo or Hugging "
                "Face with a DOI and a ready-made citation."
            ),
            choice_label=_("Access"),
            search_label=_("Title, author or language"),
            item_template="components/dataset_item.html",
            empty_text=_("No dataset matches these filters."),
            list_url_name="research:datasets",
        )
        return context


class ModelListView(ProductionListView):
    """Modèles, code et démonstrateurs (module M5)."""

    model = AIModel
    template_name = "research/production_list.html"
    partial_template = "research/_production_results.html"
    search_fields = ("title", "authorships__name", "task", "covered_languages")
    choice_field = "kind"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(
            title=_("Models and code"),
            summary=_(
                "Trained models, libraries and demonstrators by DAARA members, published on "
                "Hugging Face and GitHub."
            ),
            choice_label=_("Type"),
            search_label=_("Title, author or task"),
            item_template="components/model_item.html",
            empty_icon="chip",
            empty_text=_("No model or code matches these filters."),
            list_url_name="research:models",
        )
        return context


class ProductionDetailView(DetailView):
    model = None

    def get_queryset(self):
        return published(self.model).select_related("axis")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        production = self.object
        context["fallback"] = (
            fallback_notice(production, "abstract") if production.abstract else None
        )
        context["projects"] = production.projects.exclude(status="draft")
        context["edit_targets"] = [production]
        return context


class PublicationDetailView(ProductionDetailView):
    model = Publication
    template_name = "research/publication_detail.html"
    context_object_name = "publication"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reference"] = citation.reference(self.object)
        context["bibtex"] = citation.bibtex(self.object)
        return context


class DatasetDetailView(ProductionDetailView):
    model = Dataset
    template_name = "research/dataset_detail.html"
    context_object_name = "dataset"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["reference"] = citation.dataset_reference(self.object)
        context["models"] = published(AIModel).filter(datasets=self.object)
        context["jsonld"] = dataset_jsonld(self.object, self.request)
        return context


class ModelDetailView(ProductionDetailView):
    model = AIModel
    template_name = "research/model_detail.html"
    context_object_name = "model"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["datasets"] = self.object.datasets.filter(status=Production.Status.PUBLISHED)
        return context


def dataset_jsonld(dataset, request):
    """Données structurées schema.org/Dataset, lues par Google Dataset Search (spec §8)."""
    data = {
        "@context": "https://schema.org",
        "@type": "Dataset",
        "name": dataset.title,
        "description": dataset.abstract or dataset.title,
        "url": request.build_absolute_uri(dataset.get_absolute_url()),
        "creator": [
            {"@type": "Person", "name": authorship.name} for authorship in dataset.authorships.all()
        ],
        "isAccessibleForFree": dataset.access == Dataset.Access.OPEN,
    }
    optional = {
        "identifier": dataset.doi_url,
        "license": dataset.license,
        "version": dataset.version,
        "datePublished": str(dataset.year) if dataset.year else "",
        "spatialCoverage": dataset.coverage,
        "inLanguage": dataset.language,
    }
    data.update({key: value for key, value in optional.items() if value})
    if dataset.url:
        distribution = {"@type": "DataDownload", "contentUrl": dataset.url}
        if dataset.data_format:
            distribution["encodingFormat"] = dataset.data_format
        data["distribution"] = [distribution]
    # « < » échappé : le JSON ne peut pas fermer la balise <script> qui le contient.
    return mark_safe(json.dumps(data, ensure_ascii=False).replace("<", "\\u003c"))


def publication_bibtex(request, slug):
    publication = get_object_or_404(published_publications(), slug=slug)
    return HttpResponse(
        citation.bibtex(publication),
        content_type="application/x-bibtex; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{publication.slug}.bib"'},
    )
