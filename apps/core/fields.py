from django.db import models


class HttpsURLField(models.URLField):
    """URLField dont le formulaire complète une adresse sans schéma en https://.

    C'est le comportement par défaut de Django 6 ; ce champ l'adopte dès maintenant.
    """

    def formfield(self, **kwargs):
        return super().formfield(**{"assume_scheme": "https", **kwargs})
