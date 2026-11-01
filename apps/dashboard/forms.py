from django import forms
from django.conf import settings

from apps.members.models import Member

INPUT_CLASSES = "mt-1 block w-full rounded border border-stone-300 px-3 py-2"


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            "photo",
            *(f"position_{code}" for code in settings.MODELTRANSLATION_LANGUAGES),
            *(f"bio_{code}" for code in settings.MODELTRANSLATION_LANGUAGES),
            "orcid",
            "google_scholar_id",
            "hal_id",
            "github",
            "huggingface",
            "linkedin",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASSES
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs["rows"] = 5
