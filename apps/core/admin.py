from django.contrib import admin
from django.contrib.admin.models import LogEntry
from modeltranslation.admin import TranslationAdmin

from apps.members.permissions import Module, can

from .models import Page


class CreatedByAdminMixin:
    """Renseigne `created_by` à la création depuis l'administration."""

    def save_model(self, request, obj, form, change):
        if not change and obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Page)
class PageAdmin(CreatedByAdminMixin, TranslationAdmin):
    """Pages éditoriales : l'éditeur les modifie et les publie, l'administrateur seul en crée
    ou en supprime (les menus de la vitrine renvoient à des pages fixes)."""

    list_display = ["title", "slug", "status", "updated_at"]
    list_filter = ["status"]
    search_fields = ["title", "body"]

    def _can_edit(self, request):
        return can(request.user, "M", Module.EDITORIAL_PAGES)

    def has_module_permission(self, request):
        return self._can_edit(request)

    def has_view_permission(self, request, obj=None):
        return self._can_edit(request)

    def has_change_permission(self, request, obj=None):
        return self._can_edit(request)

    def has_add_permission(self, request):
        return can(request.user, "A", Module.ADMINISTRATION)

    def has_delete_permission(self, request, obj=None):
        return can(request.user, "A", Module.ADMINISTRATION)

    def get_readonly_fields(self, request, obj=None):
        return ["slug"] if obj else []


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    """Journal des actions d'administration, en lecture seule (spec §3.3)."""

    list_display = ["action_time", "user", "content_type", "object_repr", "action_flag"]
    list_filter = ["action_flag", "content_type"]
    search_fields = ["object_repr", "change_message", "user__username"]
    date_hierarchy = "action_time"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
