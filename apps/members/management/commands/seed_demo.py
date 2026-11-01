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

# Données fictives pour essayer la plateforme. Les institutions sont les universités réelles
# créées par la migration members/0004 ; les vrais axes se décident au lot 0.
AXES = [
    (
        "langues",
        Axis.Icon.LANGUAGE,
        ("Langues africaines et TAL", "African languages and NLP"),
        (
            "Corpus, reconnaissance de la parole et traduction automatique pour le wolof, le "
            "pulaar, le sérère et d'autres langues africaines.",
            "Corpora, speech recognition and machine translation for Wolof, Pulaar, Serer and "
            "other African languages.",
        ),
    ),
    (
        "sante",
        Axis.Icon.HEALTH,
        ("Données de santé", "Health data"),
        (
            "Données cliniques et épidémiologiques, aide au diagnostic et santé publique.",
            "Clinical and epidemiological data, diagnostic support and public health.",
        ),
    ),
    (
        "geo",
        Axis.Icon.GEOSPATIAL,
        ("Vision et données géospatiales", "Vision and geospatial data"),
        (
            "Imagerie satellitaire, cartographie et vision par ordinateur pour l'agriculture, "
            "le climat et l'aménagement du territoire.",
            "Satellite imagery, mapping and computer vision for agriculture, climate and "
            "land planning.",
        ),
    ),
]
GRADES = [
    ("Professeur titulaire", "Full professor"),
    ("Maître de conférences", "Associate professor"),
    ("Maître-assistant", "Senior lecturer"),
    ("Post-doctorant", "Postdoctoral researcher"),
    ("Doctorant", "PhD student"),
]
# Membres supplémentaires sans compte de démonstration : (identifiant, prénom, nom, grade,
# institution, axe, rôle, alumni)
EXTRA_MEMBERS = [
    ("khady", "Khady", "Diop", 2, "ugb", "sante", Role.RESEARCHER, False),
    ("ibrahima", "Ibrahima", "Fall", 3, "ucad", "geo", Role.RESEARCHER, False),
    ("mariama", "Mariama", "Sow", 4, "uasz", "geo", Role.PHD_STUDENT, False),
    ("cheikh", "Cheikh", "Mbaye", 0, "uidt", "sante", Role.RESEARCHER, False),
    ("ousmane", "Ousmane", "Gueye", 3, "uadb", "langues", Role.RESEARCHER, True),
]


class Command(BaseCommand):
    help = (
        "Crée des données de démonstration (développement seulement) : axes, grades, "
        "membres et quatre comptes aux rôles combinés."
    )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo ne tourne qu'en développement (DEBUG=True).")
        institutions = Institution.objects.in_bulk(field_name="slug")
        if "unchk" not in institutions:
            raise CommandError("Appliquez d'abord les migrations (python manage.py migrate).")
        with transaction.atomic():
            # Ancienne institution fictive des premières versions de cette commande.
            Institution.objects.filter(slug="upd", affiliations__isnull=True).delete()
            axes = {
                slug: Axis.objects.update_or_create(
                    slug=slug,
                    defaults={
                        "icon": icon,
                        "order": order,
                        "name_fr": names[0],
                        "name_en": names[1],
                        "description_fr": descriptions[0],
                        "description_en": descriptions[1],
                    },
                )[0]
                for order, (slug, icon, names, descriptions) in enumerate(AXES)
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
                member.bio_fr = (
                    "Chercheur en traitement automatique des langues africaines, Moussa "
                    "Ndiaye travaille sur la reconnaissance de la parole en wolof."
                )
                member.save()

            student = self._user("awa", "Awa", "Sarr")
            self._roles(student, Role.PHD_STUDENT)
            self._member(student, grades[4], institutions["unchk"], [axes["langues"]])

            observer = self._user("fatou", "Fatou", "Ba")
            self._roles(observer, Role.OBSERVER)

            for username, first, last, grade, school, axis, role, alumni in EXTRA_MEMBERS:
                user = self._user(username, first, last)
                self._roles(user, role)
                if username == "cheikh":
                    self._roles(user, (Role.AXIS_LEAD, axes["sante"]))
                extra = self._member(user, grades[grade], institutions[school], [axes[axis]])
                if alumni and extra.status != Member.Status.ALUMNI:
                    extra.status = Member.Status.ALUMNI
                    extra.joined_on = datetime.date(2021, 10, 1)
                    extra.left_on = datetime.date(2025, 7, 31)
                    extra.save()

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
