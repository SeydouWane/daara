"""Universités publiques du Sénégal, partenaires de DAARA.

Les noms officiels ne se traduisent pas : ils sont identiques en français et en anglais.
Logos, sites web et identifiants ROR se renseignent ensuite dans l'administration, à partir
des fichiers fournis par chaque université.
"""

from django.db import migrations

UNIVERSITIES = [
    ("ucad", "UCAD", "Université Cheikh Anta Diop de Dakar", "Dakar"),
    ("ugb", "UGB", "Université Gaston Berger de Saint-Louis", "Saint-Louis"),
    ("uasz", "UASZ", "Université Assane Seck de Ziguinchor", "Ziguinchor"),
    ("uidt", "UIDT", "Université Iba Der Thiam de Thiès", "Thiès"),
    ("uadb", "UADB", "Université Alioune Diop de Bambey", "Bambey"),
    ("ussein", "USSEIN", "Université du Sine Saloum El-Hâdj Ibrahima Niass", "Kaolack"),
    ("unchk", "UNCHK", "Université numérique Cheikh Hamidou Kane", "Dakar"),
    ("uam", "UAM", "Université Amadou Mahtar Mbow", "Diamniadio"),
]


def create_universities(apps, schema_editor):
    Institution = apps.get_model("members", "Institution")
    for slug, acronym, name, city in UNIVERSITIES:
        institution, created = Institution.objects.get_or_create(
            slug=slug,
            defaults={
                "acronym": acronym,
                "name": name,
                "name_fr": name,
                "name_en": name,
                "city": city,
                "country": "SN",
                "is_partner": True,
            },
        )
        if not created and not institution.city:
            institution.city = city
            institution.save(update_fields=["city"])


def delete_universities(apps, schema_editor):
    apps.get_model("members", "Institution").objects.filter(
        slug__in=[slug for slug, *_ in UNIVERSITIES], affiliations__isnull=True
    ).delete()


class Migration(migrations.Migration):
    dependencies = [("members", "0003_axis_icon_institution_city_institution_logo_and_more")]

    operations = [migrations.RunPython(create_universities, delete_universities)]
