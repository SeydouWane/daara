from django import forms
from django.conf import settings
from django.contrib.auth.password_validation import validate_password
from django.utils.text import capfirst, slugify
from django.utils.translation import gettext_lazy as _
from modeltranslation.translator import NotRegistered, translator

from apps.core.models import HomeFeature, Page, PartnershipStep, SiteSettings, Standard
from apps.members.models import (
    Affiliation,
    Axis,
    Grade,
    Institution,
    Member,
    RoleAssignment,
    User,
)
from apps.projects.models import Project
from apps.research.models import AIModel, Authorship, Dataset, Publication

INPUT_CLASSES = "mt-1 block w-full rounded border border-stone-300 px-3 py-2"
FIELD_CLASSES = (
    "mt-1 block w-full rounded-lg border border-stone-300 bg-white px-3 py-2 text-stone-900 "
    "focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-100 "
    "disabled:bg-stone-100 disabled:text-stone-500"
)
CHECK_CLASSES = "size-4 rounded border-stone-300 accent-brand-700"
FILE_CLASSES = (
    "block text-sm text-stone-600 file:mr-3 file:cursor-pointer file:rounded-lg file:border-0 "
    "file:bg-brand-50 file:px-4 file:py-2 file:font-semibold file:text-brand-800 "
    "hover:file:bg-brand-100"
)
LANGUAGES = settings.MODELTRANSLATION_LANGUAGES


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            "photo",
            *(f"position_{code}" for code in LANGUAGES),
            *(f"bio_{code}" for code in LANGUAGES),
            "orcid",
            "google_scholar_id",
            "hal_id",
            "github",
            "huggingface",
            "linkedin",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASSES
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = 5


# Formulaires des pages « Gérer » ---------------------------------------------------------


def translated_fields(model):
    """Noms des champs traduits de `model` (title, summary…)."""
    try:
        return set(translator.get_options_for_model(model).all_fields)
    except NotRegistered:
        return set()


def expand(model, sections):
    """Champs du modèle cités dans `sections`, chaque champ traduit décliné par langue."""
    translated = translated_fields(model)
    names = []
    model_fields = {field.name for field in model._meta.get_fields()}
    for _title, section in sections:
        for name in section:
            if name in translated:
                names += [f"{name}_{code}" for code in LANGUAGES]
            elif name in model_fields:
                names.append(name)
    return names


class ManageForm(forms.ModelForm):
    """Formulaire de gestion : champs mis en forme, textes longs en zone de texte, versions
    linguistiques d'un même champ côte à côte (`layout`).

    `sections` : ((titre, (noms de champs…)), …), avec les noms d'origine des champs traduits.
    """

    sections = ()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        model = self._meta.model
        self.translated = translated_fields(model)
        for name, field in self.fields.items():
            self._style(name, field)
        # Comme dans l'administration : la langue par défaut est due si le champ est requis.
        for base in self.translated:
            default = f"{base}_{settings.LANGUAGE_CODE}"
            if default in self.fields and not model._meta.get_field(base).blank:
                self.fields[default].required = True

    def _style(self, name, field):
        widget = field.widget
        db_field = next((f for f in self._meta.model._meta.fields if f.name == name), None)
        if isinstance(field, forms.DateField):
            field.widget = widget = forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})
        elif type(widget) is forms.TextInput and (getattr(db_field, "max_length", 0) or 0) >= 200:
            field.widget = widget = forms.Textarea(attrs={"rows": 4})
        elif isinstance(widget, forms.Textarea):
            widget.attrs["rows"] = 10
        if isinstance(widget, forms.CheckboxInput | forms.CheckboxSelectMultiple):
            widget.attrs["class"] = CHECK_CLASSES
        elif isinstance(widget, forms.ClearableFileInput):
            widget.attrs["class"] = FILE_CLASSES
        else:
            widget.attrs["class"] = FIELD_CLASSES

    def layout(self):
        """Sections prêtes à afficher : chaque ligne réunit un champ et ses traductions."""
        sections = []
        for title, names in self.sections:
            rows = []
            for name in names:
                if name in self.translated:
                    fields = [
                        (code, self[f"{name}_{code}"])
                        for code in LANGUAGES
                        if f"{name}_{code}" in self.fields
                    ]
                    if fields:
                        model_field = self._meta.model._meta.get_field(name)
                        rows.append(
                            {
                                "label": capfirst(model_field.verbose_name),
                                "help_text": model_field.help_text,
                                "fields": fields,
                                "translated": True,
                            }
                        )
                elif name in self.fields:
                    field = self[name]
                    rows.append(
                        {
                            "label": field.label,
                            "help_text": field.help_text,
                            "fields": [(None, field)],
                            "translated": False,
                        }
                    )
            if rows:
                sections.append({"title": title, "rows": rows})
        return sections


def unique_slug(model, base, instance=None, field="slug"):
    # Le champ peut venir d'un modèle parent (Production) : l'unicité se vérifie sur celui-ci.
    model = model._meta.get_field(field).model
    base = (base or "")[:100].strip("-") or model._meta.model_name
    slug, number = base, 2
    others = model.objects.exclude(pk=instance.pk) if instance and instance.pk else model.objects
    while others.filter(**{field: slug}).exists():
        slug, number = f"{base}-{number}", number + 1
    return slug


class AutoSlugMixin:
    """Adresse construite à partir du titre si on la laisse vide ; figée une fois créée."""

    slug_source = "title"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "slug" not in self.fields:
            return
        if self.instance.pk:
            self.fields["slug"].disabled = True
            self.fields["slug"].help_text = _("The web address does not change once created.")
        else:
            self.fields["slug"].required = False
            self.fields["slug"].help_text = _("Web address. Built from the name if left empty.")

    def clean(self):
        cleaned = super().clean()
        if "slug" in self.fields and not self.instance.pk and not cleaned.get("slug"):
            source = next(
                (
                    cleaned.get(name)
                    for name in (self.slug_source, *(f"{self.slug_source}_{c}" for c in LANGUAGES))
                    if cleaned.get(name)
                ),
                "",
            )
            cleaned["slug"] = unique_slug(self._meta.model, slugify(source), self.instance)
        return cleaned


SITE_SECTIONS = (
    (_("Home page"), ("tagline", "hero_title", "description", "hero_image", "hero_image_alt")),
    (_("Call to action “Join DAARA”"), ("cta_title", "cta_text")),
    (
        _("Contact and social networks, in the footer"),
        (
            "contact_email",
            "phone",
            "address",
            "linkedin",
            "youtube",
            "github",
            "huggingface",
            "zenodo",
        ),
    ),
    (
        _("Twelve-month goals, on the About page"),
        ("goal_publications", "goal_profiles", "goal_datasets", "goal_webinars", "goals_note"),
    ),
)


class SiteSettingsForm(ManageForm):
    sections = SITE_SECTIONS

    class Meta:
        model = SiteSettings
        fields = expand(SiteSettings, SITE_SECTIONS)


ITEM_SECTIONS = ((None, ("title", "text", "icon", "destination", "order", "is_visible")),)


class HomeFeatureForm(ManageForm):
    sections = ITEM_SECTIONS

    class Meta:
        model = HomeFeature
        fields = expand(HomeFeature, ITEM_SECTIONS)


STANDARD_SECTIONS = ((None, ("name", "description", "order", "is_visible")),)


class StandardForm(ManageForm):
    sections = STANDARD_SECTIONS

    class Meta:
        model = Standard
        fields = expand(Standard, STANDARD_SECTIONS)


STEP_SECTIONS = ((None, ("title", "text", "order", "is_visible")),)


class PartnershipStepForm(ManageForm):
    sections = STEP_SECTIONS

    class Meta:
        model = PartnershipStep
        fields = expand(PartnershipStep, STEP_SECTIONS)


PAGE_SECTIONS = (
    (None, ("title", "slug", "status", "menu", "summary")),
    (_("Content"), ("body",)),
    (_("Cover image"), ("image", "image_alt")),
)


class PageForm(AutoSlugMixin, ManageForm):
    sections = PAGE_SECTIONS

    class Meta:
        model = Page
        fields = expand(Page, PAGE_SECTIONS)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for code in LANGUAGES:
            self.fields[f"body_{code}"].widget.attrs["rows"] = 18
        if self.instance.is_built_in:
            # Une page fixe garde sa place dans les menus.
            self.fields["menu"].disabled = True
            self.fields["menu"].help_text = _("Built-in page: its place in the menus is fixed.")


AXIS_SECTIONS = ((None, ("name", "slug", "icon", "order", "description")),)


class AxisForm(AutoSlugMixin, ManageForm):
    sections = AXIS_SECTIONS
    slug_source = "name"

    class Meta:
        model = Axis
        fields = expand(Axis, AXIS_SECTIONS)


INSTITUTION_SECTIONS = (
    (None, ("name", "acronym", "slug", "is_partner", "logo")),
    (_("Location and identifiers"), ("city", "country", "website", "ror_id")),
)


class InstitutionForm(AutoSlugMixin, ManageForm):
    sections = INSTITUTION_SECTIONS
    slug_source = "acronym"

    class Meta:
        model = Institution
        fields = expand(Institution, INSTITUTION_SECTIONS)


GRADE_SECTIONS = ((None, ("name", "order")),)


class GradeForm(ManageForm):
    sections = GRADE_SECTIONS

    class Meta:
        model = Grade
        fields = expand(Grade, GRADE_SECTIONS)


MEMBER_SECTIONS = (
    (
        _("Identity"),
        (
            "first_name",
            "last_name",
            "account",
            "slug",
            "position",
            "grade",
            "status",
            "joined_on",
            "left_on",
        ),
    ),
    (_("Photo"), ("photo",)),
    (_("Biography"), ("bio",)),
    (
        _("Research"),
        ("primary_institution", "other_institutions", "axes", "orcid", "openalex_id"),
    ),
    (_("Other profiles"), ("google_scholar_id", "hal_id", "github", "huggingface", "linkedin")),
)


class MemberForm(AutoSlugMixin, ManageForm):
    """Le nom affiché vient du compte : il se modifie ici, avec le reste du profil. À la
    création, un compte est ouvert pour le membre si aucun compte existant n'est choisi."""

    sections = MEMBER_SECTIONS
    slug_source = "full_name"

    first_name = forms.CharField(label=capfirst(_("first name")), max_length=150)
    last_name = forms.CharField(label=capfirst(_("last name")), max_length=150)
    account = forms.ModelChoiceField(
        label=_("Existing account"),
        queryset=User.objects.filter(member__isnull=True),
        required=False,
        help_text=_("Leave empty to open a new account for this member."),
    )
    primary_institution = forms.ModelChoiceField(
        label=_("Main institution"), queryset=Institution.objects.all(), required=False
    )
    other_institutions = forms.ModelMultipleChoiceField(
        label=_("Other institutions"),
        queryset=Institution.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    class Meta:
        model = Member
        fields = expand(Member, MEMBER_SECTIONS)
        widgets = {"axes": forms.CheckboxSelectMultiple}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        member = self.instance
        if member.pk:
            del self.fields["account"]
            self.initial.update(
                first_name=member.user.first_name,
                last_name=member.user.last_name,
                primary_institution=member.primary_institution,
                other_institutions=[
                    a.institution for a in member.affiliations.all() if not a.is_primary
                ],
            )

    def clean(self):
        self.cleaned_data["full_name"] = (
            f"{self.cleaned_data.get('first_name', '')} {self.cleaned_data.get('last_name', '')}"
        )
        return super().clean()

    def save(self, commit=True):
        member = super().save(commit=False)
        user = member.user if member.user_id else self.cleaned_data.get("account")
        if user is None:
            user = User(username=unique_slug(User, member.slug, field="username"))
            user.set_unusable_password()  # un administrateur lui ouvre l'accès ensuite
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data["last_name"]
        user.save()
        member.user = user
        member.save()
        self.save_m2m()
        self._save_affiliations(member)
        return member

    def _save_affiliations(self, member):
        primary = self.cleaned_data.get("primary_institution")
        wanted = {institution.pk: False for institution in self.cleaned_data["other_institutions"]}
        if primary:
            wanted[primary.pk] = True
        member.affiliations.exclude(institution_id__in=wanted).delete()
        # Une seule affiliation principale : on retire l'ancienne avant de poser la nouvelle.
        member.affiliations.filter(is_primary=True).exclude(
            institution_id=getattr(primary, "pk", None)
        ).update(is_primary=False)
        for institution_id, is_primary in wanted.items():
            Affiliation.objects.update_or_create(
                member=member, institution_id=institution_id, defaults={"is_primary": is_primary}
            )


PUBLICATION_SECTIONS = (
    (None, ("title", "slug", "kind", "status", "axis", "year", "language")),
    (_("Publication details"), ("venue", "publisher", "volume", "issue", "pages", "doi", "url")),
    (_("Abstract"), ("abstract",)),
    (_("Access and identifiers"), ("open_access", "license", "hal_id", "dicames_id")),
)


class PublicationForm(AutoSlugMixin, ManageForm):
    sections = PUBLICATION_SECTIONS

    class Meta:
        model = Publication
        fields = expand(Publication, PUBLICATION_SECTIONS)


DATASET_SECTIONS = (
    (None, ("title", "slug", "status", "axis", "year", "language")),
    (_("Description"), ("abstract",)),
    (
        _("Access and identifiers"),
        ("doi", "url", "access", "license", "version"),
    ),
    (_("Contents"), ("data_format", "size", "covered_languages", "coverage")),
)


class DatasetForm(AutoSlugMixin, ManageForm):
    sections = DATASET_SECTIONS

    class Meta:
        model = Dataset
        fields = expand(Dataset, DATASET_SECTIONS)


MODEL_SECTIONS = (
    (None, ("title", "slug", "kind", "status", "axis", "year")),
    (_("Description"), ("abstract", "task", "framework", "covered_languages")),
    (
        _("Links and identifiers"),
        ("huggingface_id", "github_url", "demo_url", "doi", "license"),
    ),
    (_("Training datasets"), ("datasets",)),
)


class AIModelForm(AutoSlugMixin, ManageForm):
    sections = MODEL_SECTIONS

    class Meta:
        model = AIModel
        fields = expand(AIModel, MODEL_SECTIONS)
        widgets = {"datasets": forms.CheckboxSelectMultiple}


PROJECT_SECTIONS = (
    (None, ("title", "acronym", "slug", "status", "axis", "summary")),
    (_("Description"), ("description",)),
    (_("Team and partners"), ("lead", "members", "partners", "funding")),
    (_("Dates and links"), ("starts_on", "ends_on", "website")),
    (_("Research outputs"), ("outputs",)),
    (_("Cover image"), ("image", "image_alt")),
)


class ProjectForm(AutoSlugMixin, ManageForm):
    sections = PROJECT_SECTIONS

    class Meta:
        model = Project
        fields = expand(Project, PROJECT_SECTIONS)
        widgets = {
            "members": forms.CheckboxSelectMultiple,
            "partners": forms.CheckboxSelectMultiple,
            "outputs": forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["outputs"].queryset = self.fields["outputs"].queryset.order_by("-year")


ACCOUNT_SECTIONS = (
    (None, ("username", "first_name", "last_name", "email", "is_active", "password")),
)


class AccountForm(ManageForm):
    sections = ACCOUNT_SECTIONS

    password = forms.CharField(
        label=_("New password"),
        required=False,
        strip=False,
        widget=forms.PasswordInput(render_value=False, attrs={"autocomplete": "new-password"}),
        help_text=_("Leave empty to keep the current password."),
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]

    def clean_password(self):
        password = self.cleaned_data["password"]
        if password:
            validate_password(password, self.instance)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        if self.cleaned_data["password"]:
            user.set_password(self.cleaned_data["password"])
        elif not user.pk:
            user.set_unusable_password()
        user.save()
        return user


ROLE_SECTIONS = ((None, ("user", "role", "axis", "starts_on", "expires_on")),)


class RoleAssignmentForm(ManageForm):
    sections = ROLE_SECTIONS

    class Meta:
        model = RoleAssignment
        fields = ["user", "role", "axis", "starts_on", "expires_on"]


class AuthorshipForm(forms.ModelForm):
    class Meta:
        model = Authorship
        fields = ["position", "name", "member"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = FIELD_CLASSES.replace("mt-1 ", "")


def authorship_formset(parent_model):
    """Auteurs d'une production, dans l'ordre ; un co-auteur extérieur n'a qu'un nom."""
    return forms.inlineformset_factory(
        parent_model, Authorship, form=AuthorshipForm, extra=2, can_delete=True
    )
