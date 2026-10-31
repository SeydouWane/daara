from .base import *  # noqa: F403
from .base import SECRET_KEY

DEBUG = True
SECRET_KEY = SECRET_KEY or "dev-only-insecure-key"
ALLOWED_HOSTS = ["localhost", "127.0.0.1", "0.0.0.0"]

STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
}

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
