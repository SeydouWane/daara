from django import forms
from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group
from django.db.models import Count, Q
from django.utils.html import format_html
from django.utils.text import capfirst, slugify
from django.utils.translation import gettext_lazy as _
from modeltranslation.admin import TranslationAdmin

from apps.core.admin import CreatedByAdminMixin

from .models import Affiliation, Axis, Grade, Institution, Member, RoleAssignment, User

# Les rôles de DAARA remplacent les groupes Django (voir backends.py).
admin.site.unregister(Group)


def thumbnail(field_file, rounded=False):
    if not field_file:
        return "—"
    return format_html(
        '<img src="{}" alt="" style="height:40px;width:{};object-fit:{};border-radius:{}">',
        field_file.url,
        "40px" if rounded else "auto",
        "cover" if rounded else "contain",
        "50%" if rounded else "4px",
    )


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
    list_display = [
        "logo_preview",
        "name",
        "acronym",
        "city",
        "country",
        "is_partner",
        "active_members",
    ]
    list_display_links = ["logo_preview", "name"]
    list_editable = ["is_partner"]
    list_filter = ["is_partner", "country"]
    search_fields = ["name", "acronym"]
    prepopulated_fields = {"slug": ("acronym",)}
    fieldsets = [
        (None, {"fields": ["name", "acronym", "slug", "is_partner"]}),
        (_("Logo"), {"fields": ["logo_preview", "logo"]}),
        (_("Location and identifiers"), {"fields": ["city", "country", "website", "ror_id"]}),
    ]
    readonly_fields = ["logo_preview"]

    def get_queryset(self, request):
        active = Q(affiliations__member__status=Member.Status.ACTIVE)
        return super().get_queryset(request).annotate(member_count=Count("affiliations", active))

    @admin.display(description=_("logo"))
    def logo_preview(self, obj):
        return thumbnail(obj.logo)

    # Pas « members » : le nom désignerait la relation inverse Member.institutions.
    @admin.display(description=_("active members"), ordering="member_count")
    def active_members(self, obj):
        return obj.member_count


@admin.register(Axis)
class AxisAdmin(CreatedByAdminMixin, TranslationAdmin):
    list_display = ["name", "icon", "order", "active_members", "lead"]
    list_editable = ["order"]
    prepopulated_fields = {"slug": (f"name_{settings.LANGUAGE_CODE}",)}

    def get_queryset(self, request):
        active = Q(members__status=Member.Status.ACTIVE)
        return (
            super()
            .get_queryset(request)
            .annotate(member_count=Count("members", active))
            .prefetch_related("role_assignments__user")
        )

    @admin.display(description=_("active members"), ordering="member_count")
    def active_members(self, obj):
        return obj.member_count

    @admin.display(description=_("axis lead"))
    def lead(self, obj):
        user = obj.current_lead()
        return user.get_full_name() if user else "—"


@admin.register(Grade)
class GradeAdmin(TranslationAdmin):
    list_display = ["name", "order"]
    list_editable = ["order"]


class AffiliationInline(admin.TabularInline):
    model = Affiliation
    extra = 1


class MemberAdminForm(forms.ModelForm):
    """Le nom affiché vient du compte : on le modifie ici, avec le reste du profil.

    À la création, un compte est ouvert pour le membre si aucun compte existant n'est choisi :
    ajouter un membre se fait en une seule étape.
    """

    first_name = forms.CharField(label=capfirst(_("first name")), max_length=150)
    last_name = forms.CharField(label=capfirst(_("last name")), max_length=150)
    account = forms.ModelChoiceField(
        label=capfirst(_("existing account")),
        queryset=User.objects.filter(member__isnull=True),
        required=False,
        help_text=_("Leave empty to open a new account for this member."),
    )

    class Meta:
        model = Member
        # L'administration impose ses propres champs (MemberAdmin.fieldsets).
        fields = ["slug", "position", "grade", "status", "photo", "bio", "axes"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.user_id:
            self.initial.setdefault("first_name", self.instance.user.first_name)
            self.initial.setdefault("last_name", self.instance.user.last_name)
        if "slug" in self.fields:
            self.fields["slug"].required = False
            self.fields["slug"].help_text = _("Web address of the profile. Built from the name.")

    def clean(self):
        cleaned = super().clean()
        if "slug" in self.fields and not cleaned.get("slug"):
            base = slugify(f"{cleaned.get('first_name', '')} {cleaned.get('last_name', '')}")
            slug, number = base or "membre", 2
            while Member.objects.filter(slug=slug).exclude(pk=self.instance.pk).exists():
                slug, number = f"{base}-{number}", number + 1
            cleaned["slug"] = slug
        return cleaned

    def save(self, commit=True):
        member = super().save(commit=False)
        if member.user_id:
            user = member.user
        else:
            user = self.cleaned_data.get("account") or self._new_account(member.slug)
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()
        member.user = user
        if commit:
            member.save()
            self.save_m2m()
        return member

    @staticmethod
    def _new_account(slug):
        username, number = slug, 2
        while User.objects.filter(username=username).exists():
            username, number = f"{slug}-{number}", number + 1
        user = User(username=username)
        user.set_unusable_password()  # connexion après qu'un administrateur l'a ouverte
        return user


def member_fieldsets(account_field):
    return [
        (
            _("Identity"),
            {
                "fields": [
                    ("first_name", "last_name"),
                    account_field,
                    "slug",
                    "position",
                    "grade",
                    ("status", "joined_on", "left_on"),
                ]
            },
        ),
        (_("Photo"), {"fields": ["photo_preview", "photo"]}),
        (_("Biography"), {"fields": ["bio"]}),
        (_("Research"), {"fields": ["axes", "orcid", "openalex_id"]}),
        (
            _("Other profiles"),
            {
                "classes": ["collapse"],
                "fields": ["google_scholar_id", "hal_id", "github", "huggingface", "linkedin"],
            },
        ),
    ]


@admin.register(Member)
class MemberAdmin(CreatedByAdminMixin, TranslationAdmin):
    form = MemberAdminForm
    list_display = ["photo_preview", "__str__", "position", "institution", "status"]
    list_display_links = ["photo_preview", "__str__"]
    list_filter = ["status", "grade", "axes", "institutions"]
    search_fields = ["user__first_name", "user__last_name", "orcid", "position"]
    list_select_related = ["user"]
    filter_horizontal = ["axes"]
    inlines = [AffiliationInline]
    readonly_fields = ["photo_preview", "user"]
    # Le compte est choisi ou créé à l'ajout, puis affiché en lecture seule.
    fieldsets = member_fieldsets("user")
    add_fieldsets = member_fieldsets("account")

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("affiliations__institution")

    @admin.display(description=_("photo"))
    def photo_preview(self, obj):
        return thumbnail(obj.photo, rounded=True)

    @admin.display(description=_("institution"))
    def institution(self, obj):
        return obj.primary_institution or "—"
