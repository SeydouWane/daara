"""L'UAM n'est pas partenaire de DAARA (décision du porteur de projet, novembre 2026).

L'institution reste en base : un membre pourra toujours y être rattaché.
"""

from django.db import migrations


def remove_partner_flag(apps, schema_editor):
    apps.get_model("members", "Institution").objects.filter(slug="uam").update(is_partner=False)


def restore_partner_flag(apps, schema_editor):
    apps.get_model("members", "Institution").objects.filter(slug="uam").update(is_partner=True)


class Migration(migrations.Migration):
    dependencies = [("members", "0007_alter_member_openalex_id")]

    operations = [migrations.RunPython(remove_partner_flag, restore_partner_flag)]
