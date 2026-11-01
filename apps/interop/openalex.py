"""Import de publications depuis OpenAlex (spec §8.1), sans ressaisie (spec §1.3, principe 3).

OpenAlex fusionne parfois des homonymes sous un même auteur : l'import se lance pour un
membre précis, après relecture de la liste, en écartant les travaux d'un homonyme.
"""

import json
import urllib.parse
import urllib.request

from django.conf import settings
from django.db import transaction

from apps.members.models import Member
from apps.research.models import Authorship, Publication, normalize_doi

API = "https://api.openalex.org"

KINDS = {
    "article": Publication.Kind.JOURNAL_ARTICLE,
    "conference-paper": Publication.Kind.CONFERENCE_PAPER,
    "proceedings-article": Publication.Kind.CONFERENCE_PAPER,
    "book-chapter": Publication.Kind.BOOK_CHAPTER,
    "book": Publication.Kind.BOOK,
    "dissertation": Publication.Kind.THESIS,
    "preprint": Publication.Kind.PREPRINT,
    "report": Publication.Kind.REPORT,
}


def _get(path, params):
    if settings.OPENALEX_MAILTO:
        params = {**params, "mailto": settings.OPENALEX_MAILTO}
    request = urllib.request.Request(
        f"{API}{path}?{urllib.parse.urlencode(params)}",
        headers={"User-Agent": "DAARA (https://github.com/SeydouWane/daara)"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def author_works(author_id):
    """Tous les travaux d'un auteur OpenAlex, page par page (pagination par curseur)."""
    cursor = "*"
    while cursor:
        page = _get(
            "/works", {"filter": f"author.id:{author_id}", "per-page": 100, "cursor": cursor}
        )
        yield from page["results"]
        cursor = page["meta"].get("next_cursor")


def short_id(openalex_url):
    return (openalex_url or "").rsplit("/", 1)[-1]


def abstract_from_index(index):
    """OpenAlex livre les résumés sous forme d'index inversé (mot → positions)."""
    if not index:
        return ""
    words = {}
    for word, positions in index.items():
        for position in positions:
            words[position] = word
    return " ".join(words[position] for position in sorted(words))


def publication_fields(work):
    """Champs d'une Publication tirés d'un travail OpenAlex ; None si ce n'en est pas une
    (jeu de données, logiciel…), ces productions relevant d'autres modules."""
    kind = KINDS.get(work.get("type"))
    title = " ".join((work.get("title") or "").split())
    if kind is None or not title:
        return None
    location = work.get("primary_location") or {}
    source = location.get("source") or {}
    if kind == Publication.Kind.JOURNAL_ARTICLE and source.get("type") == "conference":
        kind = Publication.Kind.CONFERENCE_PAPER
    biblio = work.get("biblio") or {}
    return {
        "title": title[:500],
        "year": work.get("publication_year"),
        "language": (work.get("language") or "")[:8],
        "kind": kind,
        "doi": normalize_doi(work.get("doi")),
        "venue": (source.get("display_name") or "")[:500],
        "publisher": (source.get("host_organization_name") or "")[:300],
        "volume": (biblio.get("volume") or "")[:30],
        "issue": (biblio.get("issue") or "")[:30],
        "pages": "–".join(filter(None, [biblio.get("first_page"), biblio.get("last_page")]))[:30],
        "url": (location.get("landing_page_url") or "")[:500],
        "open_access": bool((work.get("open_access") or {}).get("is_oa")),
        "openalex_id": short_id(work.get("id")),
    }


@transaction.atomic
def import_work(work, status=Publication.Status.PUBLISHED):
    """Crée ou met à jour une publication. Le statut et l'axe choisis ensuite par l'équipe
    sont conservés lors d'un nouvel import. Renvoie (publication, créée) ou (None, False).

    Chaque co-auteur est relié au membre qui porte son identifiant OpenAlex : une publication
    partagée par plusieurs membres reste liée à tous, quel que soit celui qu'on importe.
    """
    fields = publication_fields(work)
    if fields is None:
        return None, False
    publication = Publication.objects.filter(openalex_id=fields["openalex_id"]).first()
    if publication is None and fields["doi"]:
        publication = Publication.objects.filter(doi=fields["doi"]).first()
    created = publication is None
    if created:
        publication = Publication(status=status)
    for name, value in fields.items():
        setattr(publication, name, value)
    abstract = abstract_from_index(work.get("abstract_inverted_index"))
    if abstract:
        language = fields["language"]
        if language not in settings.MODELTRANSLATION_LANGUAGES:
            language = settings.LANGUAGE_CODE
        setattr(publication, f"abstract_{language}", abstract)
    publication.save()

    known = dict(Member.objects.exclude(openalex_id="").values_list("openalex_id", "pk"))
    # Liens posés à la main dans l'administration, retrouvés par le nom de l'auteur.
    linked_by_hand = {
        authorship.name: authorship.member_id
        for authorship in publication.authorships.all()
        if authorship.member_id
    }
    publication.authorships.all().delete()
    authorships = []
    for position, authorship in enumerate(work.get("authorships") or [], start=1):
        name = authorship["author"]["display_name"][:200]
        member_id = known.get(short_id(authorship["author"].get("id"))) or linked_by_hand.get(name)
        authorships.append(
            Authorship(production=publication, position=position, name=name, member_id=member_id)
        )
    Authorship.objects.bulk_create(authorships)
    return publication, created
