from django.conf import settings
from modeltranslation.translator import TranslationOptions, register

from .models import Axis, Grade, Institution, Member


@register(Institution)
class InstitutionTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Axis)
class AxisTranslationOptions(TranslationOptions):
    # Contenu éditorial (niveau 2, spec §5.1) : bilingue obligatoire.
    fields = ("name", "description")
    required_languages = {code: ("name",) for code in settings.DAARA_EDITORIAL_LANGUAGES}


@register(Grade)
class GradeTranslationOptions(TranslationOptions):
    fields = ("name",)


@register(Member)
class MemberTranslationOptions(TranslationOptions):
    fields = ("position", "bio")
