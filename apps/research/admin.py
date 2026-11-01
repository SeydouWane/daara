from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from apps.core.admin import CreatedByAdminMixin

from .models import Authorship, Publication


class AuthorshipInline(admin.TabularInline):
    model = Authorship
    extra = 0
    fields = ["position", "name", "member"]
    autocomplete_fields = ["member"]


@admin.register(Publication)
class PublicationAdmin(CreatedByAdminMixin, TranslationAdmin):
    list_display = ["title", "kind", "year", "venue", "status", "open_access"]
    list_filter = ["status", "kind", "year", "axis", "open_access", "members"]
    search_fields = ["title", "doi", "venue", "authorships__name"]
    inlines = [AuthorshipInline]
    readonly_fields = ["openalex_id"]
    actions = ["publish", "archive"]

    @admin.action(description=_("Publish the selected publications"), permissions=["change"])
    def publish(self, request, queryset):
        count = queryset.update(status=Publication.Status.PUBLISHED)
        self.message_user(request, _("%d publication(s) published.") % count)

    @admin.action(description=_("Withdraw the selected publications"), permissions=["change"])
    def archive(self, request, queryset):
        count = queryset.update(status=Publication.Status.ARCHIVED)
        self.message_user(request, _("%d publication(s) withdrawn from the site.") % count)

    fieldsets = [
        (None, {"fields": ["title", "slug", "kind", "status", "axis", "year", "language"]}),
        (
            _("Publication details"),
            {"fields": ["venue", "publisher", "volume", "issue", "pages", "doi", "url"]},
        ),
        (_("Abstract"), {"fields": ["abstract"]}),
        (
            _("Access and identifiers"),
            {"fields": ["open_access", "license", "hal_id", "dicames_id", "openalex_id"]},
        ),
    ]
