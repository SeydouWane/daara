from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InteropConfig(AppConfig):
    name = "apps.interop"
    verbose_name = _("Interoperability")
