from django.core.exceptions import ObjectDoesNotExist
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.core.fields import HttpsURLField
from apps.core.models import TimeStampedModel
from apps.members.models import Axis, Member


class Production(TimeStampedModel):
    """Entité commune aux productions (spec §6) : publication, jeu de données, modèle, support
    de formation. Un flux unique et une recherche transverse reposent sur cette table.

    Le titre n'est jamais traduit : il reste dans la langue d'origine (spec §5.1). Le résumé
    est un contenu de niveau 3 : anglais attendu, français recommandé.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", _("Draft")
        PENDING = "pending", _("Pending review")
        PUBLISHED = "published", _("Published")
        ARCHIVED = "archived", _("Archived")

    title = models.CharField(_("title"), max_length=500)
    slug = models.SlugField(_("slug"), max_length=120, unique=True)
    language = models.CharField(
        _("language"), max_length=8, blank=True, help_text=_("Language of the original, e.g. en.")
    )
    year = models.PositiveSmallIntegerField(_("year"), null=True, blank=True)
    abstract = models.TextField(_("abstract"), blank=True)
    axis = models.ForeignKey(
        Axis,
        verbose_name=_("research axis"),
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="productions",
    )
    license = models.CharField(_("licence"), max_length=60, blank=True)
    status = models.CharField(
        _("status"), max_length=10, choices=Status, default=Status.DRAFT, db_index=True
    )
    members = models.ManyToManyField(
        Member, through="Authorship", related_name="productions", verbose_name=_("authors")
    )

    class Meta:
        ordering = ["-year", "title"]
        verbose_name = _("research output")
        verbose_name_plural = _("research outputs")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self._unique_slug()
        super().save(*args, **kwargs)

    def _unique_slug(self):
        base = slugify(self.title)[:100].strip("-") or "production"
        candidates = [base, f"{base}-{self.year}" if self.year else None]
        for candidate in filter(None, candidates):
            if not Production.objects.filter(slug=candidate).exists():
                return candidate
        number = 2
        while Production.objects.filter(slug=f"{base}-{number}").exists():
            number += 1
        return f"{base}-{number}"

    def specific(self):
        """La production sous son vrai type : publication, jeu de données ou modèle."""
        for name in ("publication", "dataset", "aimodel"):
            try:
                return getattr(self, name)
            except ObjectDoesNotExist:
                continue
        return self


class Authorship(models.Model):
    """Auteur d'une production, dans l'ordre de la publication. Les co-auteurs extérieurs à
    DAARA n'ont qu'un nom ; les membres sont reliés à leur profil."""

    production = models.ForeignKey(Production, on_delete=models.CASCADE, related_name="authorships")
    position = models.PositiveSmallIntegerField(_("position"))
    name = models.CharField(_("name"), max_length=200)
    member = models.ForeignKey(
        Member,
        verbose_name=_("member"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="authorships",
    )

    class Meta:
        ordering = ["position"]
        verbose_name = _("author")
        verbose_name_plural = _("authors")
        constraints = [
            models.UniqueConstraint(
                fields=["production", "position"], name="unique_author_position"
            )
        ]

    def __str__(self):
        return self.name


class Publication(Production):
    """Publication scientifique (module M3)."""

    class Kind(models.TextChoices):
        JOURNAL_ARTICLE = "journal_article", _("Journal article")
        CONFERENCE_PAPER = "conference_paper", _("Conference paper")
        BOOK_CHAPTER = "book_chapter", _("Book chapter")
        BOOK = "book", _("Book")
        THESIS = "thesis", _("Doctoral thesis")
        MASTER_THESIS = "master_thesis", _("Master's thesis")
        PREPRINT = "preprint", _("Preprint")
        REPORT = "report", _("Technical report")

    kind = models.CharField(_("type"), max_length=20, choices=Kind, default=Kind.JOURNAL_ARTICLE)
    doi = models.CharField(
        _("DOI"), max_length=255, blank=True, help_text=_("Without URL prefix, e.g. 10.1109/xyz.")
    )
    venue = models.CharField(_("journal or conference"), max_length=500, blank=True)
    publisher = models.CharField(_("publisher"), max_length=300, blank=True)
    volume = models.CharField(_("volume"), max_length=30, blank=True)
    issue = models.CharField(_("issue"), max_length=30, blank=True)
    pages = models.CharField(_("pages"), max_length=30, blank=True)
    url = HttpsURLField(_("web page"), max_length=500, blank=True)
    open_access = models.BooleanField(_("open access"), default=False)
    hal_id = models.CharField(_("HAL identifier"), max_length=60, blank=True)
    dicames_id = models.CharField(_("DICAMES identifier"), max_length=60, blank=True)
    openalex_id = models.CharField(_("OpenAlex identifier"), max_length=20, blank=True)

    class Meta:
        verbose_name = _("publication")
        verbose_name_plural = _("publications")
        constraints = [
            models.UniqueConstraint(fields=["doi"], condition=~Q(doi=""), name="unique_doi"),
            models.UniqueConstraint(
                fields=["openalex_id"], condition=~Q(openalex_id=""), name="unique_openalex_id"
            ),
        ]

    def get_absolute_url(self):
        return reverse("research:publication", args=[self.slug])

    def clean_fields(self, exclude=None):
        self.doi = normalize_doi(self.doi)
        super().clean_fields(exclude)

    @property
    def doi_url(self):
        return f"https://doi.org/{self.doi}" if self.doi else ""

    @property
    def link(self):
        return self.doi_url or self.url


class Dataset(Production):
    """Jeu de données (module M4). DAARA en tient la fiche ; les données elles-mêmes sont
    déposées sur Zenodo, Hugging Face ou un entrepôt institutionnel (spec §6)."""

    class Access(models.TextChoices):
        OPEN = "open", _("Open access")
        ON_REQUEST = "on_request", _("On request")
        RESTRICTED = "restricted", _("Restricted")

    doi = models.CharField(
        _("DOI"),
        max_length=255,
        blank=True,
        help_text=_("Without URL prefix, e.g. 10.5281/zenodo.123."),
    )
    url = HttpsURLField(
        _("repository page"),
        max_length=500,
        blank=True,
        help_text=_("Zenodo record, Hugging Face dataset or institutional repository."),
    )
    access = models.CharField(_("access"), max_length=12, choices=Access, default=Access.OPEN)
    version = models.CharField(_("version"), max_length=30, blank=True)
    data_format = models.CharField(
        _("format"), max_length=100, blank=True, help_text=_("E.g. CSV, WAV audio, GeoTIFF.")
    )
    size = models.CharField(
        _("size"), max_length=60, blank=True, help_text=_("E.g. 12 GB, 40,000 sentences.")
    )
    covered_languages = models.CharField(
        _("languages covered"),
        max_length=200,
        blank=True,
        help_text=_("For corpora, e.g. Wolof, Pulaar, Serer."),
    )
    coverage = models.CharField(
        _("geographic coverage"), max_length=200, blank=True, help_text=_("E.g. Senegal, Sahel.")
    )

    class Meta:
        verbose_name = _("dataset")
        verbose_name_plural = _("datasets")
        constraints = [
            models.UniqueConstraint(fields=["doi"], condition=~Q(doi=""), name="unique_dataset_doi")
        ]

    def get_absolute_url(self):
        return reverse("research:dataset", args=[self.slug])

    def clean_fields(self, exclude=None):
        self.doi = normalize_doi(self.doi)
        super().clean_fields(exclude)

    @property
    def doi_url(self):
        return f"https://doi.org/{self.doi}" if self.doi else ""

    @property
    def link(self):
        return self.url or self.doi_url


class AIModel(Production):
    """Modèle d'IA, code ou démonstrateur (module M5), publié sur Hugging Face ou GitHub."""

    class Kind(models.TextChoices):
        MODEL = "model", _("Trained model")
        CODE = "code", _("Code or library")
        DEMO = "demo", _("Demonstrator")

    kind = models.CharField(_("type"), max_length=10, choices=Kind, default=Kind.MODEL)
    task = models.CharField(
        _("task"),
        max_length=120,
        blank=True,
        help_text=_("E.g. speech recognition, translation, crop disease detection."),
    )
    framework = models.CharField(
        _("framework"), max_length=60, blank=True, help_text=_("E.g. PyTorch, Transformers.")
    )
    huggingface_id = models.CharField(
        _("Hugging Face repository"),
        max_length=200,
        blank=True,
        validators=[RegexValidator(r"^[\w.-]+/[\w.-]+$")],
        help_text=_("owner/name, e.g. daara/wolof-asr."),
    )
    github_url = HttpsURLField(_("source code"), max_length=300, blank=True)
    demo_url = HttpsURLField(_("demonstrator"), max_length=300, blank=True)
    doi = models.CharField(_("DOI"), max_length=255, blank=True)
    covered_languages = models.CharField(_("languages covered"), max_length=200, blank=True)
    datasets = models.ManyToManyField(
        Dataset,
        verbose_name=_("training datasets"),
        related_name="trained_models",
        blank=True,
    )

    class Meta:
        verbose_name = _("model or code")
        verbose_name_plural = _("models and code")

    def get_absolute_url(self):
        return reverse("research:model", args=[self.slug])

    def clean_fields(self, exclude=None):
        self.doi = normalize_doi(self.doi)
        super().clean_fields(exclude)

    @property
    def huggingface_url(self):
        return f"https://huggingface.co/{self.huggingface_id}" if self.huggingface_id else ""

    @property
    def doi_url(self):
        return f"https://doi.org/{self.doi}" if self.doi else ""


def normalize_doi(value):
    value = (value or "").strip()
    for prefix in ("https://doi.org/", "http://doi.org/", "https://dx.doi.org/", "doi:"):
        if value.lower().startswith(prefix):
            value = value[len(prefix) :]
    return value.lower()
