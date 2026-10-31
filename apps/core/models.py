from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """Horodatage et auteur, portés par chaque entité (spec §6.2)."""

    created_at = models.DateTimeField(_("created at"), auto_now_add=True)
    updated_at = models.DateTimeField(_("updated at"), auto_now=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("created by"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        editable=False,
        related_name="+",
    )

    class Meta:
        abstract = True


class Page(TimeStampedModel):
    """Page éditoriale de la vitrine (module M1) : à propos, gouvernance, contact…

    Contenu de niveau 2 (spec §5.1) : une page n'est publiée que si elle existe dans toutes
    les langues éditoriales. Le corps est rédigé en Markdown.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PUBLISHED = "published", _("Published")

    slug = models.SlugField(_("slug"), unique=True)
    title = models.CharField(_("title"), max_length=60)
    summary = models.CharField(
        _("summary"), max_length=300, blank=True, help_text=_("One or two sentences.")
    )
    body = models.TextField(_("body"), blank=True, help_text=_("Markdown."))
    status = models.CharField(_("status"), max_length=10, choices=Status, default=Status.DRAFT)

    class Meta:
        ordering = ["slug"]
        verbose_name = _("editorial page")
        verbose_name_plural = _("editorial pages")

    def __str__(self):
        return self.title

    def clean(self):
        if self.status != self.Status.PUBLISHED:
            return
        missing = [
            code
            for code in settings.DAARA_EDITORIAL_LANGUAGES
            if not getattr(self, f"title_{code}") or not getattr(self, f"body_{code}")
        ]
        if missing:
            raise ValidationError(
                _("A published page needs a title and a body in every language. Missing: %s.")
                % ", ".join(code.upper() for code in missing)
            )
