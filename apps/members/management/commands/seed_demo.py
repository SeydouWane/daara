import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from apps.members.models import (
    Affiliation,
    Axis,
    Grade,
    Institution,
    Member,
    Role,
    RoleAssignment,
    User,
)

DEMO_PASSWORD = "daara-demo-2026"

# Données fictives pour essayer l'espace. Les vrais axes et institutions se décident au lot 0.
INSTITUTIONS = [
    (
        "unchk",
        "UNCHK",
        "SN",
        "Université numérique Cheikh Hamidou Kane",
        "Cheikh Hamidou Kane Digital University",
    ),
    (
        "ussein",
        "USSEIN",
        "SN",
        "Université du Sine Saloum El-Hâdj Ibrahima Niass",
        "Sine Saloum El-Hâdj Ibrahima Niass University",
    ),
    (
        "upd",
        "UPD",
        "CI",
        "Université partenaire de démonstration",
        "Demonstration partner university",
    ),
]
AXES = [
    ("langues", "Langues africaines et TAL", "African languages and NLP"),
    ("sante", "Données de santé", "Health data"),
    ("geo", "Vision et données géospatiales", "Vision and geospatial data"),
]
GRADES = [
    ("Professeur titulaire", "Full professor"),
    ("Maître de conférences", "Associate professor"),
    ("Maître-assistant", "Senior lecturer"),
    ("Post-doctorant", "Postdoctoral researcher"),
    ("Doctorant", "PhD student"),
]


class Command(BaseCommand):
    help = (
        "Crée des données de démonstration (développement seulement) : institutions, axes, "
        "grades et quatre comptes aux rôles combinés."
    )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo ne tourne qu'en développement (DEBUG=True).")
        with transaction.atomic():
            institutions = {
                slug: Institution.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "acronym": acronym,
                        "country": country,
                        "name_fr": name_fr,
                        "name_en": name_en,
                    },
                )[0]
                for slug, acronym, country, name_fr, name_en in INSTITUTIONS
            }
            axes = {
                slug: Axis.objects.update_or_create(
                    slug=slug, defaults={"name_fr": name_fr, "name_en": name_en, "order": order}
                )[0]
                for order, (slug, name_fr, name_en) in enumerate(AXES)
            }
            grades = [
                Grade.objects.update_or_create(
                    name_fr=name_fr, defaults={"name_en": name_en, "order": order}
                )[0]
                for order, (name_fr, name_en) in enumerate(GRADES)
            ]

            admin = self._user("admin", "Aminata", "Diallo", superuser=True)
            self._roles(admin, Role.ADMIN)
            self._member(admin, grades[0], institutions["unchk"], [axes["sante"]])

            lead = self._user("moussa", "Moussa", "Ndiaye")
            self._roles(lead, Role.RESEARCHER, Role.EDITOR, (Role.AXIS_LEAD, axes["langues"]))
            member = self._member(lead, grades[1], institutions["ussein"], [axes["langues"]])
            if not member.bio_fr:
                # Biographie en français seulement : elle apparaît dans « Traductions ».
                member.bio_fr = "Chercheur en traitement automatique des langues africaines."
                member.save()

            student = self._user("awa", "Awa", "Sarr")
            self._roles(student, Role.PHD_STUDENT)
            self._member(student, grades[4], institutions["unchk"], [axes["langues"]])

            observer = self._user("fatou", "Fatou", "Ba")
            self._roles(observer, Role.OBSERVER)

        self.stdout.write(self.style.SUCCESS("Données de démonstration prêtes."))
        self.stdout.write(f"Mot de passe commun : {DEMO_PASSWORD}")
        for username, description in [
            ("admin", "administratrice"),
            ("moussa", "chercheur + responsable d'axe + éditeur"),
            ("awa", "doctorante"),
            ("fatou", "observatrice, accès de 6 mois"),
        ]:
            self.stdout.write(f"  {username:<8} {description}")

    def _user(self, username, first_name, last_name, superuser=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "email": f"{username}@demo.daara.invalid",
                "is_staff": superuser,
                "is_superuser": superuser,
            },
        )
        if created:
            user.set_password(DEMO_PASSWORD)
            user.save()
        return user

    def _roles(self, user, *roles):
        today = timezone.localdate()
        for entry in roles:
            role, axis = entry if isinstance(entry, tuple) else (entry, None)
            expires_on = today + datetime.timedelta(days=182) if role == Role.OBSERVER else None
            RoleAssignment.objects.get_or_create(
                user=user, role=role, axis=axis, defaults={"expires_on": expires_on}
            )

    def _member(self, user, grade, institution, axes):
        member, _ = Member.objects.get_or_create(
            user=user,
            defaults={"slug": slugify(user.get_full_name()), "grade": grade},
        )
        Affiliation.objects.get_or_create(
            member=member, institution=institution, defaults={"is_primary": True}
        )
        member.axes.add(*axes)
        return member
