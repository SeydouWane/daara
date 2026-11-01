from django.core.management.base import BaseCommand, CommandError

from apps.interop.openalex import author_works, import_work, publication_fields, short_id
from apps.members.models import Member


class Command(BaseCommand):
    help = (
        "Importe les publications d'un auteur OpenAlex et les relie à un membre. Relisez "
        "d'abord la liste avec --dry-run : OpenAlex fusionne parfois des homonymes, ou coupe "
        "une même personne en plusieurs auteurs (passer alors tous les identifiants)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "authors", nargs="+", help="Identifiant(s) OpenAlex de l'auteur, ex. A5011347992"
        )
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

    def handle(self, authors, member, exclude, dry_run, **options):
        try:
            profile = Member.objects.get(slug=member)
        except Member.DoesNotExist as error:
            raise CommandError(f"Aucun membre avec le slug « {member} ».") from error
        authors = [short_id(author) for author in authors]
        for author in authors:
            other = (
                Member.objects.exclude(pk=profile.pk).filter(openalex_id__contains=author).first()
            )
            if other and author in other.openalex_ids:
                raise CommandError(f"L'auteur OpenAlex {author} est déjà relié à {other}.")
        if not dry_run:
            # Le lien membre ↔ auteur(s) sert ensuite à chaque import, y compris celui d'un
            # co-auteur : les publications partagées restent reliées à tous leurs membres.
            ids = list(dict.fromkeys([*profile.openalex_ids, *authors]))
            if ids != profile.openalex_ids:
                profile.openalex_id = " ".join(ids)
                profile.save(update_fields=["openalex_id"])

        excluded = set(exclude)
        seen = set()
        counts = {"created": 0, "updated": 0, "skipped": 0}
        for author in authors:
            for work in author_works(author):
                work_id = short_id(work.get("id"))
                if work_id in seen:
                    continue
                seen.add(work_id)
                fields = publication_fields(work)
                if work_id in excluded or fields is None:
                    counts["skipped"] += 1
                    reason = "écarté" if work_id in excluded else f"type {work.get('type')}"
                    self.stdout.write(f"  - {work_id} ({reason}) {(work.get('title') or '')[:70]}")
                    continue
                if dry_run:
                    self.stdout.write(f"  + {work_id} {fields['year']} {fields['title'][:80]}")
                    continue
                _publication, created = import_work(work)
                counts["created" if created else "updated"] += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"{counts['created']} créée(s), {counts['updated']} mise(s) à jour, "
                f"{counts['skipped']} écartée(s)."
            )
        )
