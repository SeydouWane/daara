from django.db.models import Q
from django.views.generic import DetailView, ListView

from apps.core.i18n import fallback_notice
from apps.members.models import Axis
from apps.research.models import Production

from .models import Project


def visible_projects():
    """Projets montrés au public : tous sauf les brouillons."""
    return Project.objects.exclude(status=Project.Status.DRAFT).select_related("axis", "lead__user")


class ProjectListView(ListView):
    """Projets de recherche (module M6) : filtres par état et par axe, recherche ; avec HTMX,
    seule la liste est renvoyée."""

    template_name = "projects/project_list.html"
    context_object_name = "projects"
    paginate_by = 12

    def get_queryset(self):
        params = self.request.GET
        projects = visible_projects().prefetch_related("partners")
        if query := params.get("q", "").strip():
            projects = projects.filter(
                Q(title__icontains=query)
                | Q(acronym__icontains=query)
                | Q(summary__icontains=query)
            )
        if params.get("status") in (Project.Status.ONGOING, Project.Status.COMPLETED):
            projects = projects.filter(status=params["status"])
        if params.get("axis"):
            projects = projects.filter(axis__slug=params["axis"])
        return projects

    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            return ["projects/_project_results.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["statuses"] = [
            (Project.Status.ONGOING, Project.Status.ONGOING.label),
            (Project.Status.COMPLETED, Project.Status.COMPLETED.label),
        ]
        context["axes"] = Axis.objects.filter(projects__in=visible_projects()).distinct()
        context["filters"] = self.request.GET
        query = self.request.GET.copy()
        query.pop("page", None)
        context["query_string"] = query.urlencode()
        context["edit_targets"] = [Project]
        return context


class ProjectDetailView(DetailView):
    template_name = "projects/project_detail.html"
    context_object_name = "project"

    def get_queryset(self):
        return visible_projects().prefetch_related("members__user", "partners")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        context["fallback"] = (
            fallback_notice(project, "description") if project.description else None
        )
        outputs = project.outputs.filter(status=Production.Status.PUBLISHED).select_related(
            "publication", "dataset", "aimodel"
        )
        context["outputs"] = [output.specific() for output in outputs.order_by("-year")]
        context["edit_targets"] = [project]
        return context
