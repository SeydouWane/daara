from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _

from .fields import HttpsURLField
from .images import generate_renditions, validate_image_size


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

    class Menu(models.TextChoices):
        NONE = "", _("No menu")
        ABOUT = "about", _("“About” menu")
        FOOTER = "footer", _("Footer, “Information” column")

    # Pages fixes de la vitrine : leur adresse et leur place dans les menus sont dans le code.
    # Les autres pages sont servies sous /pages/<slug>/ et placées par leur champ `menu`.
    ROUTES = {
        "about": "core:about",
        "governance": "core:governance",
        "partners": "core:partners",
        "contact": "core:contact",
        "legal-notice": "core:legal_notice",
        "privacy": "core:privacy",
    }

    slug = models.SlugField(_("slug"), unique=True)
    menu = models.CharField(
        _("menu"),
        max_length=10,
        choices=Menu,
        default=Menu.NONE,
        blank=True,
        help_text=_(
            "Where a page you add appears once published. Built-in pages keep their place."
        ),
    )
    title = models.CharField(_("title"), max_length=60)
    summary = models.CharField(
        _("summary"), max_length=300, blank=True, help_text=_("One or two sentences.")
    )
    body = models.TextField(_("body"), blank=True, help_text=_("Markdown."))
    status = models.CharField(_("status"), max_length=10, choices=Status, default=Status.DRAFT)
    image = models.ImageField(
        _("cover image"),
        upload_to="pages/",
        blank=True,
        width_field="image_width",
        height_field="image_height",
        validators=[validate_image_size],
        help_text=_("Optional photo shown at the top of the page. Converted to WebP."),
    )
    image_alt = models.CharField(
        _("image description"),
        max_length=200,
        blank=True,
        help_text=_("Describe the photo for people who cannot see it."),
    )
    image_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    image_height = models.PositiveIntegerField(null=True, blank=True, editable=False)

    IMAGE_WIDTHS = (480, 960, 1440)

    class Meta:
        ordering = ["slug"]
        verbose_name = _("editorial page")
        verbose_name_plural = _("editorial pages")

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        generate_renditions(self.image, self.IMAGE_WIDTHS)

    def get_absolute_url(self):
        if self.slug in self.ROUTES:
            return reverse(self.ROUTES[self.slug])
        return reverse("core:page", args=[self.slug])

    @property
    def is_built_in(self):
        return self.slug in self.ROUTES

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


class SiteSettings(TimeStampedModel):
    """Textes et coordonnées de la vitrine hors pages éditoriales : accroche de l'accueil,
    appel à rejoindre, pied de page, objectifs à douze mois. Une seule ligne, créée par la
    migration 0005 ; l'administration la modifie sans passer par le code."""

    tagline = models.CharField(
        _("tagline"), max_length=60, help_text=_("Short line above the home page title.")
    )
    hero_title = models.CharField(_("home page title"), max_length=120)
    description = models.CharField(
        _("short description"),
        max_length=300,
        help_text=_("Shown under the home page title, in the footer and to search engines."),
    )
    hero_image = models.ImageField(
        _("home page photo"),
        upload_to="site/",
        blank=True,
        width_field="hero_image_width",
        height_field="hero_image_height",
        validators=[validate_image_size],
        help_text=_("Optional; replaces the network illustration. Converted to WebP."),
    )
    hero_image_alt = models.CharField(
        _("photo description"),
        max_length=200,
        blank=True,
        help_text=_("Describe the photo for people who cannot see it."),
    )
    hero_image_width = models.PositiveIntegerField(null=True, blank=True, editable=False)
    hero_image_height = models.PositiveIntegerField(null=True, blank=True, editable=False)
    cta_title = models.CharField(_("call to action title"), max_length=80)
    cta_text = models.CharField(_("call to action text"), max_length=300)
    contact_email = models.EmailField(_("contact email"), blank=True)
    phone = models.CharField(_("phone"), max_length=30, blank=True)
    address = models.CharField(_("postal address"), max_length=200, blank=True)
    linkedin = HttpsURLField(_("LinkedIn page"), blank=True)
    youtube = HttpsURLField(_("YouTube channel"), blank=True)
    github = HttpsURLField(_("GitHub organisation"), blank=True)
    huggingface = HttpsURLField(_("Hugging Face organisation"), blank=True)
    zenodo = HttpsURLField(_("Zenodo community"), blank=True)
    goal_publications = models.PositiveSmallIntegerField(_("referenced publications"), default=100)
    goal_profiles = models.PositiveSmallIntegerField(_("complete member profiles"), default=20)
    goal_datasets = models.PositiveSmallIntegerField(_("datasets with a DOI"), default=10)
    goal_webinars = models.PositiveSmallIntegerField(_("webinars with a DOI"), default=6)
    goals_note = models.CharField(
        _("note under the goals"),
        max_length=300,
        blank=True,
        help_text=_("Goals that cannot be measured on the platform."),
    )

    IMAGE_WIDTHS = (480, 960)

    class Meta:
        verbose_name = _("home page, footer and goals")
        verbose_name_plural = _("home page, footer and goals")

    def __str__(self):
        return str(self._meta.verbose_name).capitalize()

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        generate_renditions(self.hero_image, self.IMAGE_WIDTHS)

    def get_absolute_url(self):
        return reverse("core:home")

    @classmethod
    def load(cls):
        return cls.objects.get_or_create(pk=1)[0]

    def social_links(self):
        """Réseaux renseignés, sous forme (libellé, URL)."""
        links = [
            ("LinkedIn", self.linkedin),
            ("YouTube", self.youtube),
            ("GitHub", self.github),
            ("Hugging Face", self.huggingface),
            ("Zenodo", self.zenodo),
        ]
        return [(label, url) for label, url in links if url]


class Icon(models.TextChoices):
    """Icônes de templates/components/icon.html proposées dans l'administration."""

    DOCUMENT = "document", _("Document")
    DATABASE = "database", _("Database")
    CHIP = "chip", _("Chip")
    CAP = "cap", _("Graduation cap")
    USERS = "users", _("People")
    HANDSHAKE = "handshake", _("Handshake")
    PIN = "pin", _("Location")
    GLOBE = "globe", _("Globe")


class OrderedItem(TimeStampedModel):
    """Élément d'une liste de la vitrine, que l'administration ordonne et masque."""

    order = models.PositiveSmallIntegerField(_("order"), default=0)
    is_visible = models.BooleanField(_("visible"), default=True)

    PUBLIC_URL = "core:home"

    class Meta:
        abstract = True
        ordering = ["order", "pk"]

    def get_absolute_url(self):
        return reverse(self.PUBLIC_URL)


class HomeFeature(OrderedItem):
    """Carte « Ce que vous trouverez » de l'accueil."""

    class Destination(models.TextChoices):
        PUBLICATIONS = "research:publications", _("Publications")
        DATASETS = "research:datasets", _("Datasets")
        MODELS = "research:models", _("Models and code")
        PROJECTS = "projects:list", _("Projects")
        TRAINING = "training:list", _("Training")
        MEMBERS = "directory:list", _("Members")
        AXES = "core:axes", _("Research axes")

    icon = models.CharField(_("icon"), max_length=20, choices=Icon, default=Icon.DOCUMENT)
    title = models.CharField(_("title"), max_length=60)
    text = models.CharField(_("text"), max_length=200)
    destination = models.CharField(
        _("link"),
        max_length=40,
        choices=Destination,
        help_text=_("A module that is not built yet is shown as “soon”."),
    )

    class Meta(OrderedItem.Meta):
        verbose_name = _("home page card")
        verbose_name_plural = _("home page cards")

    def __str__(self):
        return self.title

    @property
    def url(self):
        """Adresse du module, ou None tant qu'il n'est pas construit."""
        try:
            return reverse(self.destination)
        except NoReverseMatch:
            return None


class Standard(OrderedItem):
    """Standard ouvert présenté sur la page « À propos »."""

    name = models.CharField(_("name"), max_length=40)
    description = models.CharField(_("description"), max_length=200)

    PUBLIC_URL = "core:about"

    class Meta(OrderedItem.Meta):
        verbose_name = _("open standard (About page)")
        verbose_name_plural = _("open standards (About page)")

    def __str__(self):
        return self.name


class PartnershipStep(OrderedItem):
    """Étape de la procédure d'adhésion, sur la page « Partenaires »."""

    title = models.CharField(_("title"), max_length=80)
    text = models.CharField(_("text"), max_length=300)

    PUBLIC_URL = "core:partners"

    class Meta(OrderedItem.Meta):
        verbose_name = _("partnership step (Partners page)")
        verbose_name_plural = _("partnership steps (Partners page)")

    def __str__(self):
        return self.title
