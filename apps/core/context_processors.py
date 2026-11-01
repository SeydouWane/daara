from django.utils.functional import SimpleLazyObject

from .models import SiteSettings


def site_settings(request):
    """Textes et coordonnées de la vitrine, chargés seulement si un gabarit s'en sert."""
    return {"site_settings": SimpleLazyObject(SiteSettings.load)}
