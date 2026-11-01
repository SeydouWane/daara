from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.admin.models import LogEntry
from django.db import models
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from .models import HomeFeature, Page, PartnershipStep, SiteSettings, Standard


class CreatedByAdminMixin:
    """Renseigne `created_by` à la création depuis l'administration."""

    def save_model(self, request, obj, form, change):
        if not change and obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


class LongTextMixin:
    """Les textes de plus d'une ligne (résumés, descriptions) s'écrivent dans une zone de
    texte plutôt que dans un champ d'une ligne."""

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if isinstance(db_field, models.CharField) and (db_field.max_length or 0) >= 200:
            kwargs["widget"] = forms.Textarea(attrs={"rows": 3, "class": "vLargeTextField"})
        return super().formfield_for_dbfield(db_field, request, **kwargs)


@admin.register(SiteSettings)
class SiteSettingsAdmin(LongTextMixin, TranslationAdmin):
    """Une seule fiche : la liste mène directement au formulaire."""

    fieldsets = [
        (
            _("Home page"),
            {"fields": ["tagline", "hero_title", "description", "hero_image", "hero_image_alt"]},
        ),
        (_("Call to action “Join DAARA”"), {"fields": ["cta_title", "cta_text"]}),
        (
            _("Contact and social networks, in the footer"),
            {
                "fields": [
                    "contact_email",
                    "phone",
                    "address",
                    "linkedin",
                    "youtube",
                    "github",
                    "huggingface",
                    "zenodo",
                ]
            },
        ),
        (
            _("Twelve-month goals, on the About page"),
            {
                "description": _("Progress is computed from the published contents."),
                "fields": [
                    "goal_publications",
                    "goal_profiles",
                    "goal_datasets",
                    "goal_webinars",
                    "goals_note",
                ],
            },
        ),
    ]

    def changelist_view(self, request, extra_context=None):
        site_settings = SiteSettings.load()
        return redirect(reverse("admin:core_sitesettings_change", args=[site_settings.pk]))

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class OrderedItemAdmin(LongTextMixin, CreatedByAdminMixin, TranslationAdmin):
    list_editable = ["order", "is_visible"]


@admin.register(HomeFeature)
class HomeFeatureAdmin(OrderedItemAdmin):
    list_display = ["title", "destination", "icon", "order", "is_visible"]
    fields = ["title", "text", "icon", "destination", "order", "is_visible"]


@admin.register(Standard)
class StandardAdmin(OrderedItemAdmin):
    list_display = ["name", "description", "order", "is_visible"]
    fields = ["name", "description", "order", "is_visible"]


@admin.register(PartnershipStep)
class PartnershipStepAdmin(OrderedItemAdmin):
    list_display = ["title", "order", "is_visible"]
    fields = ["title", "text", "order", "is_visible"]


@admin.register(Page)
class PageAdmin(LongTextMixin, CreatedByAdminMixin, TranslationAdmin):
    """Pages éditoriales, côté administration technique (l'équipe les gère dans l'espace)."""

    list_display = ["title", "slug", "placement", "status", "updated_at"]
    list_filter = ["status"]
    search_fields = ["title", "body"]
    fieldsets = [
        (None, {"fields": ["title", "slug", "status", "menu", "summary"]}),
        (_("Content"), {"fields": ["body"]}),
        (_("Cover image"), {"fields": ["image", "image_alt"]}),
    ]

    @admin.display(description=_("menu"))
    def placement(self, obj):
        return _("built-in page") if obj.is_built_in else obj.get_menu_display()

    def get_readonly_fields(self, request, obj=None):
        if obj is None:
            return []
        # Une page fixe garde son adresse et sa place dans les menus.
        return ["slug", "menu"] if obj.is_built_in else ["slug"]

    def get_prepopulated_fields(self, request, obj=None):
        return {} if obj else {"slug": [f"title_{settings.LANGUAGE_CODE}"]}


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
