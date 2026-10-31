from django.db.models import Prefetch, Q
from django.views.generic import DetailView, ListView

from apps.core.i18n import fallback_notice

from .models import Affiliation, Axis, Grade, Institution, Member


def _members():
    return Member.objects.select_related("user", "grade").prefetch_related(
        "axes",
        Prefetch(
            "affiliations",
            queryset=Affiliation.objects.select_related("institution").order_by("-is_primary"),
        ),
    )


class DirectoryView(ListView):
    """Annuaire des membres (module M2) : filtres par institution, axe, grade et nom.

    Tri alphabétique par défaut, par grade sur demande. Avec HTMX, seule la liste est
    renvoyée : les filtres s'appliquent sans recharger la page.
    """

    template_name = "members/directory.html"
    context_object_name = "members"
    paginate_by = 20

    def get_queryset(self):
        params = self.request.GET
        status = Member.Status.ALUMNI if params.get("status") == "alumni" else Member.Status.ACTIVE
        members = _members().filter(status=status)
        if params.get("institution"):
            members = members.filter(institutions__slug=params["institution"])
        if params.get("axis"):
            members = members.filter(axes__slug=params["axis"])
        if params.get("grade", "").isdigit():
            members = members.filter(grade_id=params["grade"])
        if query := params.get("q", "").strip():
            members = members.filter(
                Q(user__first_name__icontains=query) | Q(user__last_name__icontains=query)
            )
        order = ["user__last_name", "user__first_name"]
        if params.get("sort") == "grade":
            order = ["grade__order", *order]
        return members.order_by(*order).distinct()

    def get_template_names(self):
        if self.request.headers.get("HX-Request"):
            return ["members/_directory_results.html"]
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["institutions"] = Institution.objects.all()
        context["axes"] = Axis.objects.all()
        context["grades"] = Grade.objects.all()
        context["filters"] = self.request.GET
        query = self.request.GET.copy()
        query.pop("page", None)
        context["query_string"] = query.urlencode()
        return context


class ProfileView(DetailView):
    template_name = "members/profile.html"
    context_object_name = "member"

    def get_queryset(self):
        return _members()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["fallback"] = fallback_notice(self.object, "bio") if self.object.bio else None
        return context
