"""Réglages communs à tous les environnements. Toute valeur sensible vient de l'environnement."""

from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
if (BASE_DIR / ".env").exists():
    environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
ADMIN_URL = env("ADMIN_URL", default="admin/")

INSTALLED_APPS = [
    # modeltranslation doit précéder l'admin pour en surcharger les formulaires.
    "modeltranslation",
    "apps.core.admin_config.DaaraAdminConfig",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "apps.core",
    "apps.members",
    "apps.research",
    "apps.projects",
    "apps.training",
    "apps.news",
    "apps.interop",
    "apps.dashboard",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.template.context_processors.i18n",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.core.context_processors.site_settings",
            ],
        },
    },
]

DATABASES = {
    "default": env.db("DATABASE_URL", default="postgres://daara:daara@localhost:5432/daara"),
}
DATABASES["default"]["CONN_MAX_AGE"] = 60
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REDIS_URL = env("REDIS_URL", default="")
CACHES = {
    "default": (
        {"BACKEND": "django.core.cache.backends.redis.RedisCache", "LOCATION": REDIS_URL}
        if REDIS_URL
        else {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}
    )
}

AUTH_USER_MODEL = "members.User"
LOGIN_URL = "members:login"
LOGIN_REDIRECT_URL = "dashboard:home"
LOGOUT_REDIRECT_URL = "core:home"
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Langues : la liste active est une variable de configuration, jamais codée en dur (spec §5.2).
# Ajouter une langue = l'ajouter à DAARA_LANGUAGES, migrer les colonnes, traduire les .po.
LANGUAGE_NAMES = {"fr": "Français", "en": "English", "wo": "Wolof"}
ACTIVE_LANGUAGES = env.list("DAARA_LANGUAGES", default=["fr", "en"])
LANGUAGES = [(code, LANGUAGE_NAMES[code]) for code in ACTIVE_LANGUAGES]
# Langue de repli et cible du hreflang x-default (spec §5.3).
LANGUAGE_CODE = env("DAARA_DEFAULT_LANGUAGE", default="en")
# Le choix de langue persiste un an ; Accept-Language ne sert qu'au premier passage.
LANGUAGE_COOKIE_AGE = 60 * 60 * 24 * 365
LOCALE_PATHS = [BASE_DIR / "locale"]
USE_I18N = True
USE_TZ = True
TIME_ZONE = "Africa/Dakar"

# Les trois niveaux de contenu ont chacun leur liste de langues (spec §5.1, §5.5) :
# ajouter le wolof à l'interface n'oblige pas à traduire les contenus éditoriaux.
DAARA_EDITORIAL_LANGUAGES = tuple(
    code
    for code in env.list("DAARA_EDITORIAL_LANGUAGES", default=["fr", "en"])
    if code in ACTIVE_LANGUAGES
)

MODELTRANSLATION_DEFAULT_LANGUAGE = LANGUAGE_CODE
MODELTRANSLATION_LANGUAGES = tuple(code for code, _ in LANGUAGES)
# Jamais de page vide : on retombe sur la langue disponible (spec §5.3).
MODELTRANSLATION_FALLBACK_LANGUAGES = (
    LANGUAGE_CODE,
    *(code for code in MODELTRANSLATION_LANGUAGES if code != LANGUAGE_CODE),
)

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

X_FRAME_OPTIONS = "DENY"

# OpenAlex : une adresse de contact donne accès au « polite pool », plus rapide et plus stable.
OPENALEX_MAILTO = env("OPENALEX_MAILTO", default="")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("LOG_LEVEL", default="INFO")},
}
