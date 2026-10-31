from django.contrib import admin
from django.contrib.admin.models import LogEntry


class CreatedByAdminMixin:
    """Renseigne `created_by` à la création depuis l'administration."""

    def save_model(self, request, obj, form, change):
        if not change and obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


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
