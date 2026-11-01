from modeltranslation.translator import TranslationOptions, register

from .models import AIModel, Dataset, Production, Publication


@register(Production)
class ProductionTranslationOptions(TranslationOptions):
    # Le titre reste dans sa langue d'origine (spec §5.1) : seul le résumé se traduit.
    fields = ("abstract",)


@register(Publication)
class PublicationTranslationOptions(TranslationOptions):
    fields = ()


@register(Dataset)
class DatasetTranslationOptions(TranslationOptions):
    fields = ()


@register(AIModel)
class AIModelTranslationOptions(TranslationOptions):
    fields = ()
