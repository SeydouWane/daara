import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.members.models import Axis, Grade, Role, RoleAssignment, User

DEMO_PASSWORD = "daara-demo-2026"

# Axes provisoires (les vrais se décident au lot 0) et grades de référence.
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
# Comptes de test des rôles, sans profil public : l'annuaire ne montre que de vrais membres.
ACCOUNTS = [
    ("admin", "Aminata", "Diallo", "administratrice", [Role.ADMIN]),
    (
        "moussa",
        "Moussa",
        "Ndiaye",
        "chercheur + responsable d'axe + éditeur",
        [Role.RESEARCHER, Role.EDITOR, (Role.AXIS_LEAD, "langues")],
    ),
    ("awa", "Awa", "Sarr", "doctorante", [Role.PHD_STUDENT]),
    ("fatou", "Fatou", "Ba", "observatrice, accès de 6 mois", [Role.OBSERVER]),
]


class Command(BaseCommand):
    help = (
        "Prépare un environnement de développement : axes provisoires, grades et quatre "
        "comptes de test aux rôles combinés, sans profil public."
    )

    def handle(self, *args, **options):
        if not settings.DEBUG:
            raise CommandError("seed_demo ne tourne qu'en développement (DEBUG=True).")
        with transaction.atomic():
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
            for order, (name_fr, name_en) in enumerate(GRADES):
                Grade.objects.update_or_create(
                    name_fr=name_fr, defaults={"name_en": name_en, "order": order}
                )
            for username, first_name, last_name, _description, roles in ACCOUNTS:
                user = self._user(username, first_name, last_name, superuser=username == "admin")
                if Role.EDITOR in roles and not user.is_staff:
                    # L'éditeur travaille dans l'administration (apps/members/backends.py).
                    user.is_staff = True
                    user.save(update_fields=["is_staff"])
                self._roles(user, roles, axes)

        self.stdout.write(self.style.SUCCESS("Environnement de démonstration prêt."))
        self.stdout.write(f"Mot de passe commun des comptes de test : {DEMO_PASSWORD}")
        for username, _first, _last, description, _roles in ACCOUNTS:
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

    def _roles(self, user, roles, axes):
        today = timezone.localdate()
        for entry in roles:
            role, axis_slug = entry if isinstance(entry, tuple) else (entry, None)
            expires_on = today + datetime.timedelta(days=182) if role == Role.OBSERVER else None
            RoleAssignment.objects.get_or_create(
                user=user,
                role=role,
                axis=axes.get(axis_slug),
                defaults={"expires_on": expires_on},
            )
