from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from apps.core.admin import CreatedByAdminMixin

from .models import Affiliation, Axis, Grade, Institution, Member, RoleAssignment, User


class RoleAssignmentInline(admin.TabularInline):
    model = RoleAssignment
    fk_name = "user"
    extra = 0
    fields = ["role", "axis", "starts_on", "expires_on"]


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = [RoleAssignmentInline]
    list_display = ["username", "email", "first_name", "last_name", "roles", "is_staff"]

    @admin.display(description=_("active roles"))
    def roles(self, obj):
        return ", ".join(a.get_role_display() for a in obj.role_assignments.active())

    def save_formset(self, request, form, formset, change):
        for assignment in formset.save(commit=False):
            if assignment.pk is None:
                assignment.created_by = request.user
            assignment.save()
        for deleted in formset.deleted_objects:
            deleted.delete()


@admin.register(RoleAssignment)
class RoleAssignmentAdmin(CreatedByAdminMixin, admin.ModelAdmin):
    list_display = ["user", "role", "axis", "starts_on", "expires_on", "active"]
    list_filter = ["role", "axis"]
    search_fields = ["user__username", "user__first_name", "user__last_name", "user__email"]
    autocomplete_fields = ["user"]

    @admin.display(description=_("active"), boolean=True)
    def active(self, obj):
        return obj.is_active


@admin.register(Institution)
class InstitutionAdmin(CreatedByAdminMixin, TranslationAdmin):
    list_display = ["name", "acronym", "country", "is_partner"]
    list_filter = ["is_partner", "country"]
    search_fields = ["name", "acronym"]
    prepopulated_fields = {"slug": ("acronym",)}


@admin.register(Axis)
class AxisAdmin(CreatedByAdminMixin, TranslationAdmin):
    list_display = ["name", "order"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": (f"name_{settings.LANGUAGE_CODE}",)}


@admin.register(Grade)
class GradeAdmin(TranslationAdmin):
    list_display = ["name", "order"]
    list_editable = ["order"]


class AffiliationInline(admin.TabularInline):
    model = Affiliation
    extra = 1


@admin.register(Member)
class MemberAdmin(CreatedByAdminMixin, TranslationAdmin):
    list_display = ["__str__", "grade", "status"]
    list_filter = ["status", "grade", "axes", "institutions"]
    search_fields = ["user__first_name", "user__last_name", "orcid"]
    autocomplete_fields = ["user"]
    filter_horizontal = ["axes"]
    inlines = [AffiliationInline]
