from django.core.management.base import BaseCommand, CommandError

from apps.interop.openalex import author_works, import_work, publication_fields, short_id
from apps.members.models import Member


class Command(BaseCommand):
    help = (
        "Importe les publications d'un auteur OpenAlex et les relie à un membre. Relisez "
        "d'abord la liste avec --dry-run : OpenAlex fusionne parfois des homonymes."
    )

    def add_arguments(self, parser):
        parser.add_argument("author", help="Identifiant OpenAlex de l'auteur, ex. A5011347992")
        parser.add_argument("--member", required=True, help="Slug du profil DAARA de l'auteur")
        parser.add_argument(
            "--exclude",
            nargs="*",
            default=[],
            help="Identifiants OpenAlex de travaux à écarter (homonymes, doublons)",
        )
        parser.add_argument(
            "--dry-run", action="store_true", help="Afficher la liste sans rien enregistrer"
        )

    def handle(self, author, member, exclude, dry_run, **options):
        try:
            profile = Member.objects.get(slug=member)
        except Member.DoesNotExist as error:
            raise CommandError(f"Aucun membre avec le slug « {member} ».") from error
        author = short_id(author)
        excluded = set(exclude)
        counts = {"created": 0, "updated": 0, "skipped": 0}

        for work in author_works(author):
            work_id = short_id(work.get("id"))
            fields = publication_fields(work)
            if work_id in excluded or fields is None:
                counts["skipped"] += 1
                reason = "écarté" if work_id in excluded else f"type {work.get('type')}"
                self.stdout.write(f"  - {work_id} ({reason}) {(work.get('title') or '')[:70]}")
                continue
            if dry_run:
                self.stdout.write(f"  + {work_id} {fields['year']} {fields['title'][:80]}")
                continue
            _publication, created = import_work(work, profile, author)
            counts["created" if created else "updated"] += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{counts['created']} créée(s), {counts['updated']} mise(s) à jour, "
                f"{counts['skipped']} écartée(s)."
            )
        )
