from django.conf import settings
from django.utils.translation import get_language
from django.utils.translation import gettext_lazy as _

# Bandeau affiché quand un contenu n'existe pas dans la langue demandée (spec §5.3).
ONLY_AVAILABLE_IN = {
    "fr": _("Available in French only"),
    "en": _("Available in English only"),
    "wo": _("Available in Wolof only"),
}


def displayed_language(obj, field):
    """Langue réellement affichée pour un champ traduit : la langue active si le champ y est
    renseigné, sinon la première langue de repli qui l'est. Jamais de page vide."""
    current = get_language()
    if getattr(obj, f"{field}_{current}", None):
        return current
    for code in settings.MODELTRANSLATION_FALLBACK_LANGUAGES:
        if getattr(obj, f"{field}_{code}", None):
            return code
    return current


def fallback_notice(obj, field):
    """Contexte du bandeau de repli : None si le contenu existe dans la langue active."""
    shown = displayed_language(obj, field)
    if shown == get_language():
        return None
    return {"lang": shown, "message": ONLY_AVAILABLE_IN.get(shown, "")}
