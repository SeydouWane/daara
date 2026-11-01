from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError

from apps.members.models import Institution, Member

EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp"}


class Command(BaseCommand):
    help = (
        "Téléverse en une fois les logos d'institutions et les photos de membres d'un dossier. "
        "Nommer chaque fichier d'après le sigle ou le slug : ucad.png, ussein.jpg, "
        "oumy-niass.png… Les fichiers existants sont remplacés."
    )

    def add_arguments(self, parser):
        parser.add_argument("folder", help="Dossier contenant les images, ex. a_importer")

    def handle(self, folder, **options):
        directory = Path(folder)
        if not directory.is_dir():
            raise CommandError(f"Dossier introuvable : {directory}")
        institutions = {}
        for institution in Institution.objects.all():
            institutions[institution.slug.lower()] = institution
            if institution.acronym:
                institutions[institution.acronym.lower()] = institution
        members = {member.slug: member for member in Member.objects.all()}

        for path in sorted(directory.iterdir()):
            if path.suffix.lower() not in EXTENSIONS:
                continue
            key = path.stem.lower()
            target, field = None, None
            if key in institutions:
                target, field = institutions[key], "logo"
            elif key in members:
                target, field = members[key], "photo"
            if target is None:
                self.stdout.write(
                    self.style.WARNING(f"  ? {path.name} : aucun sigle ni slug ne correspond")
                )
                continue
            with path.open("rb") as handle:
                getattr(target, field).save(f"{target.slug}{path.suffix.lower()}", File(handle))
            label = "logo" if field == "logo" else "photo"
            self.stdout.write(self.style.SUCCESS(f"  + {path.name} → {label} de {target}"))
