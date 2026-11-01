from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.fields import HttpsURLField
from apps.core.images import generate_renditions, validate_image_size
from apps.core.models import TimeStampedModel

from .identifiers import normalize_orcid, normalize_ror, validate_orcid, validate_ror


class User(AbstractUser):
    """Compte de connexion.

    Défini dès la phase 0 : un modèle d'utilisateur personnalisé ne peut plus être introduit
    après la première migration. Le profil public est porté par `Member`, les droits par
    `RoleAssignment`.
    """


class Institution(TimeStampedModel):
    """Université ou organisme partenaire. Les institutions sont une donnée, jamais une liste
    codée en dur : DAARA travaille avec toutes les universités partenaires."""

    name = models.CharField(_("name"), max_length=200)
    acronym = models.CharField(_("acronym"), max_length=30, blank=True)
    slug = models.SlugField(_("slug"), unique=True)
    country = models.CharField(
        _("country"),
        max_length=2,
        validators=[RegexValidator(r"^[A-Z]{2}$")],
        help_text=_("ISO 3166-1 alpha-2 code, e.g. SN."),
    )
    ror_id = models.CharField(
        _("ROR identifier"), max_length=9, blank=True, validators=[validate_ror]
    )
    website = HttpsURLField(_("website"), blank=True)
    city = models.CharField(_("city"), max_length=80, blank=True)
    is_partner = models.BooleanField(_("partner institution"), default=True)
    logo = models.ImageField(
        _("logo"),
        upload_to="institutions/",
        blank=True,
        width_field="logo_width",
        height_field="logo_height",
        validators=[validate_image_size],
        help_text=_(
            "Official file supplied by the institution, PNG or JPEG with a transparent or "
            "white background. Converted to WebP automatically."
        ),
    )
    logo_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    logo_height = models.PositiveIntegerField(null=True, blank=True, editable=False)

    LOGO_WIDTHS = (160, 320)

    class Meta:
        ordering = ["name"]
        verbose_name = _("institution")
        verbose_name_plural = _("institutions")
        constraints = [
            models.UniqueConstraint(
                fields=["ror_id"], condition=~Q(ror_id=""), name="unique_institution_ror"
            )
        ]

    def __str__(self):
        return self.acronym or self.name

    def clean_fields(self, exclude=None):
        self.ror_id = normalize_ror(self.ror_id)
        super().clean_fields(exclude)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        generate_renditions(self.logo, self.LOGO_WIDTHS)


class Axis(TimeStampedModel):
    """Axe thématique. Son responsable est désigné par un rôle « responsable d'axe »."""

    class Icon(models.TextChoices):
        """Illustrations SVG de templates/components/axis_icon.html."""

        DATA = "data", _("Data")
        LANGUAGE = "language", _("Languages")
        HEALTH = "health", _("Health")
        GEOSPATIAL = "geospatial", _("Geospatial")
        VISION = "vision", _("Computer vision")
        AGRICULTURE = "agriculture", _("Agriculture")
        EDUCATION = "education", _("Education")
        CLIMATE = "climate", _("Climate and environment")

    name = models.CharField(_("name"), max_length=150)
    description = models.TextField(_("description"), blank=True)
    slug = models.SlugField(_("slug"), unique=True)
    order = models.PositiveSmallIntegerField(_("order"), default=0)
    icon = models.CharField(_("icon"), max_length=20, choices=Icon, default=Icon.DATA)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = _("research axis")
        verbose_name_plural = _("research axes")

    def __str__(self):
        return self.name

    def current_lead(self):
        """Responsable d'axe actif, ou None. Profite des affectations préchargées."""
        for assignment in self.role_assignments.all():
            if assignment.is_active:
                return assignment.user
        return None


class Grade(models.Model):
    """Grade académique. Une table plutôt qu'une liste fixe : les grades varient d'un pays et
    d'une université partenaire à l'autre."""

    name = models.CharField(_("name"), max_length=100)
    order = models.PositiveSmallIntegerField(
        _("order"), default=0, help_text=_("Sort order in the directory, most senior first.")
    )

    class Meta:
        ordering = ["order", "name"]
        verbose_name = _("grade")
        verbose_name_plural = _("grades")

    def __str__(self):
        return self.name


class Member(TimeStampedModel):
    """Profil public d'un membre de l'équipe (module M2)."""

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        ALUMNI = "alumni", _("Alumni")

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name=_("account"),
        on_delete=models.PROTECT,
        related_name="member",
    )
    slug = models.SlugField(_("slug"), unique=True)
    grade = models.ForeignKey(
        Grade, verbose_name=_("grade"), on_delete=models.PROTECT, null=True, blank=True
    )
    institutions = models.ManyToManyField(
        Institution,
        verbose_name=_("institutions"),
        through="Affiliation",
        related_name="members",
        blank=True,
    )
    axes = models.ManyToManyField(
        Axis, verbose_name=_("research axes"), related_name="members", blank=True
    )
    orcid = models.CharField(_("ORCID iD"), max_length=19, blank=True, validators=[validate_orcid])
    bio = models.TextField(_("biography"), blank=True)
    google_scholar_id = models.CharField(_("Google Scholar ID"), max_length=40, blank=True)
    hal_id = models.CharField(_("HAL identifier"), max_length=60, blank=True)
    github = models.CharField(_("GitHub username"), max_length=39, blank=True)
    huggingface = models.CharField(_("Hugging Face username"), max_length=96, blank=True)
    linkedin = HttpsURLField(_("LinkedIn profile"), blank=True)
    status = models.CharField(_("status"), max_length=10, choices=Status, default=Status.ACTIVE)
    joined_on = models.DateField(_("joined on"), null=True, blank=True)
    left_on = models.DateField(_("left on"), null=True, blank=True)

    class Meta:
        ordering = ["user__last_name", "user__first_name"]
        verbose_name = _("member")
        verbose_name_plural = _("members")
        constraints = [
            models.UniqueConstraint(
                fields=["orcid"], condition=~Q(orcid=""), name="unique_member_orcid"
            )
        ]

    def __str__(self):
        return self.user.get_full_name() or self.user.get_username()

    def get_absolute_url(self):
        return reverse("directory:detail", args=[self.slug])

    @property
    def initials(self):
        parts = [self.user.first_name, self.user.last_name]
        return "".join(part[0] for part in parts if part).upper() or self.user.username[:2].upper()

    @property
    def primary_institution(self):
        for affiliation in self.affiliations.all():
            if affiliation.is_primary:
                return affiliation.institution
        return None

    def external_links(self):
        """Profils externes renseignés, sous forme (libellé, URL)."""
        links = [
            ("ORCID", self.orcid and f"https://orcid.org/{self.orcid}"),
            (
                "Google Scholar",
                self.google_scholar_id
                and f"https://scholar.google.com/citations?user={self.google_scholar_id}",
            ),
            ("HAL", self.hal_id and f"https://cv.hal.science/{self.hal_id}"),
            ("GitHub", self.github and f"https://github.com/{self.github}"),
            ("Hugging Face", self.huggingface and f"https://huggingface.co/{self.huggingface}"),
            ("LinkedIn", self.linkedin),
        ]
        return [(label, url) for label, url in links if url]

    def clean_fields(self, exclude=None):
        self.orcid = normalize_orcid(self.orcid)
        super().clean_fields(exclude)

    def clean(self):
        # Un alumni garde son profil en ligne avec la période de présence (spec §3.3).
        if self.status == self.Status.ALUMNI and not self.left_on:
            raise ValidationError({"left_on": _("An alumni profile needs a departure date.")})


class Affiliation(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="affiliations")
    institution = models.ForeignKey(
        Institution,
        verbose_name=_("institution"),
        on_delete=models.PROTECT,
        related_name="affiliations",
    )
    is_primary = models.BooleanField(_("primary affiliation"), default=False)

    class Meta:
        verbose_name = _("affiliation")
        verbose_name_plural = _("affiliations")
        constraints = [
            models.UniqueConstraint(fields=["member", "institution"], name="unique_affiliation"),
            models.UniqueConstraint(
                fields=["member"], condition=Q(is_primary=True), name="one_primary_affiliation"
            ),
        ]

    def __str__(self):
        return f"{self.member} — {self.institution}"


class Role(models.TextChoices):
    """Profils de la spec §3.1. Le visiteur n'est pas un rôle : c'est l'absence de connexion."""

    LEARNER = "learner", _("Learner")
    PHD_STUDENT = "phd_student", _("PhD student")
    RESEARCHER = "researcher", _("Researcher")
    AXIS_LEAD = "axis_lead", _("Axis lead")
    EDITOR = "editor", _("Editor and translator")
    EXTERNAL = "external", _("External collaborator")
    OBSERVER = "observer", _("Observer")
    ADMIN = "admin", _("Administrator")


def one_year_after(day):
    try:
        return day.replace(year=day.year + 1)
    except ValueError:  # 29 février
        return day.replace(year=day.year + 1, day=28)


class RoleAssignmentQuerySet(models.QuerySet):
    def active(self, on=None):
        on = on or timezone.localdate()
        return self.filter(starts_on__lte=on).filter(
            Q(expires_on__isnull=True) | Q(expires_on__gte=on)
        )


class RoleAssignment(TimeStampedModel):
    """Attribution d'un rôle. Un utilisateur cumule autant de rôles que nécessaire : ses droits
    sont l'union de ses rôles actifs (voir permissions.py)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        on_delete=models.CASCADE,
        related_name="role_assignments",
    )
    role = models.CharField(_("role"), max_length=20, choices=Role)
    axis = models.ForeignKey(
        Axis,
        verbose_name=_("research axis"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="role_assignments",
        help_text=_("Required for axis leads, empty for every other role."),
    )
    starts_on = models.DateField(_("starts on"), default=timezone.localdate)
    expires_on = models.DateField(
        _("expires on"),
        null=True,
        blank=True,
        help_text=_("Required for observers: 12 months at most, renewable."),
    )

    objects = RoleAssignmentQuerySet.as_manager()

    class Meta:
        ordering = ["user", "role"]
        verbose_name = _("role assignment")
        verbose_name_plural = _("role assignments")
        constraints = [
            models.UniqueConstraint(
                fields=["user", "role", "axis"],
                nulls_distinct=False,
                name="unique_role_assignment",
            ),
            models.CheckConstraint(
                condition=Q(role=Role.AXIS_LEAD, axis__isnull=False)
                | (~Q(role=Role.AXIS_LEAD) & Q(axis__isnull=True)),
                name="axis_only_for_axis_lead",
            ),
            models.CheckConstraint(
                condition=~Q(role=Role.OBSERVER) | Q(expires_on__isnull=False),
                name="observer_has_expiry",
            ),
            models.CheckConstraint(
                condition=Q(expires_on__isnull=True) | Q(expires_on__gte=F("starts_on")),
                name="expiry_after_start",
            ),
        ]

    def __str__(self):
        label = self.get_role_display()
        if self.axis_id:
            label = f"{label} ({self.axis})"
        return f"{self.user} — {label}"

    @property
    def is_active(self):
        today = timezone.localdate()
        return self.starts_on <= today and (self.expires_on is None or self.expires_on >= today)

    def clean(self):
        errors = {}
        if self.role == Role.AXIS_LEAD and not self.axis_id:
            errors["axis"] = _("An axis lead must be assigned to an axis.")
        if self.role != Role.AXIS_LEAD and self.axis_id:
            errors["axis"] = _("Only axis leads are assigned to an axis.")
        if self.role == Role.OBSERVER:
            start = self.starts_on or timezone.localdate()
            if not self.expires_on:
                errors["expires_on"] = _("An observer access must have an expiry date.")
            elif self.expires_on > one_year_after(start):
                errors["expires_on"] = _("An observer access lasts 12 months at most.")
        if self.expires_on and self.starts_on and self.expires_on < self.starts_on:
            errors["expires_on"] = _("The expiry date cannot precede the start date.")
        if self.role == Role.AXIS_LEAD and self.axis_id:
            # Un seul responsable par axe (spec §2.1).
            other_leads = (
                RoleAssignment.objects.active()
                .filter(role=Role.AXIS_LEAD, axis_id=self.axis_id)
                .exclude(pk=self.pk)
            )
            if other_leads.exists():
                errors["axis"] = _("This axis already has an active lead.")
        if errors:
            raise ValidationError(errors)
