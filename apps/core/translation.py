from modeltranslation.translator import TranslationOptions, register

from .models import HomeFeature, Page, PartnershipStep, SiteSettings, Standard


@register(Page)
class PageTranslationOptions(TranslationOptions):
    fields = ("title", "summary", "body", "image_alt")


@register(SiteSettings)
class SiteSettingsTranslationOptions(TranslationOptions):
    fields = (
        "tagline",
        "hero_title",
        "description",
        "hero_image_alt",
        "cta_title",
        "cta_text",
        "address",
        "goals_note",
    )


@register(HomeFeature)
class HomeFeatureTranslationOptions(TranslationOptions):
    fields = ("title", "text")


@register(Standard)
class StandardTranslationOptions(TranslationOptions):
    fields = ("description",)


@register(PartnershipStep)
class PartnershipStepTranslationOptions(TranslationOptions):
    fields = ("title", "text")
