from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from apps.core.fields import HttpsURLField
from apps.core.images import generate_renditions, validate_image_size
from apps.core.models import TimeStampedModel
from apps.members.models import Axis, Institution, Member
from apps.research.models import Production


class Project(TimeStampedModel):
    """Projet de recherche (module M6) : équipe, partenaires, financements et productions."""

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        ONGOING = "ongoing", _("Ongoing")
        COMPLETED = "completed", _("Completed")

    title = models.CharField(_("title"), max_length=200)
    acronym = models.CharField(_("acronym"), max_length=30, blank=True)
    slug = models.SlugField(_("slug"), max_length=120, unique=True)
    summary = models.CharField(_("summary"), max_length=300, help_text=_("One or two sentences."))
    description = models.TextField(_("description"), blank=True, help_text=_("Markdown."))
    status = models.CharField(_("status"), max_length=10, choices=Status, default=Status.DRAFT)
    axis = models.ForeignKey(
        Axis,
        verbose_name=_("research axis"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="projects",
    )
    lead = models.ForeignKey(
        Member,
        verbose_name=_("project lead"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_projects",
    )
    members = models.ManyToManyField(
        Member, verbose_name=_("team"), related_name="projects", blank=True
    )
    partners = models.ManyToManyField(
        Institution, verbose_name=_("partner institutions"), related_name="projects", blank=True
    )
    funding = models.CharField(
        _("funding"), max_length=300, blank=True, help_text=_("Funding bodies and programmes.")
    )
    starts_on = models.DateField(_("start date"), null=True, blank=True)
    ends_on = models.DateField(_("end date"), null=True, blank=True)
    website = HttpsURLField(_("website"), blank=True)
    outputs = models.ManyToManyField(
        Production, verbose_name=_("research outputs"), related_name="projects", blank=True
    )
    image = models.ImageField(
        _("cover image"),
        upload_to="projects/",
        blank=True,
        width_field="image_width",
        height_field="image_height",
        validators=[validate_image_size],
        help_text=_("Optional photo. Converted to WebP."),
    )
    image_alt = models.CharField(
        _("image description"),
        max_length=200,
        blank=True,
        help_text=_("Describe the photo for people who cannot see it."),
    )
    image_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    image_height = models.PositiveIntegerField(null=True, blank=True, editable=False)

    IMAGE_WIDTHS = (480, 960)

    class Meta:
        ordering = ["-starts_on", "slug"]
        verbose_name = _("project")
        verbose_name_plural = _("projects")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        generate_renditions(self.image, self.IMAGE_WIDTHS)

    def get_absolute_url(self):
        return reverse("projects:detail", args=[self.slug])

    def clean(self):
        if self.starts_on and self.ends_on and self.ends_on < self.starts_on:
            raise ValidationError({"ends_on": _("The end date cannot precede the start date.")})
