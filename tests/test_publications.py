import copy
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.core.images import rendition_name
from apps.interop.openalex import abstract_from_index, import_work, publication_fields
from apps.members.models import Member, Role
from apps.research.citation import bibtex, reference
from apps.research.models import Publication

pytestmark = pytest.mark.django_db

# Travail OpenAlex simulé : aucun appel réseau dans les tests.
WORK = {
    "id": "https://openalex.org/W100",
    "doi": "https://doi.org/10.1109/TEST.2024.42",
    "title": "Fact-checking  Senegalese news & opinions",
    "publication_year": 2024,
    "language": "en",
    "type": "article",
    "primary_location": {
        "landing_page_url": "https://example.org/paper",
        "source": {
            "display_name": "Conference on Data Science",
            "host_organization_name": "IEEE",
            "type": "conference",
        },
    },
    "biblio": {"volume": "12", "issue": "3", "first_page": "10", "last_page": "18"},
    "open_access": {"is_oa": True},
    "abstract_inverted_index": {"We": [0], "check": [1], "facts.": [2]},
    "authorships": [
        {"author": {"id": "https://openalex.org/A1", "display_name": "Jean Dupont"}},
        {"author": {"id": "https://openalex.org/A42", "display_name": "Awa Sarr"}},
    ],
}


@pytest.fixture
def author(make_user):
    user = make_user("awa", Role.RESEARCHER, first_name="Awa", last_name="Sarr")
    return Member.objects.create(user=user, slug="awa-sarr", openalex_id="A42")


@pytest.fixture
def publication(author):
    return import_work(WORK)[0]


def test_openalex_work_is_mapped_to_publication_fields():
    fields = publication_fields(WORK)
    assert fields["title"] == "Fact-checking Senegalese news & opinions"
    # Un « article » publié dans une conférence est une communication.
    assert fields["kind"] == Publication.Kind.CONFERENCE_PAPER
    assert fields["doi"] == "10.1109/test.2024.42"
    assert fields["pages"] == "10–18"
    assert fields["openalex_id"] == "W100"
    assert fields["open_access"] is True


def test_datasets_are_not_imported_as_publications():
    assert publication_fields({**WORK, "type": "dataset"}) is None


def test_abstract_is_rebuilt_from_the_inverted_index():
    assert abstract_from_index({"facts.": [2], "We": [0], "check": [1]}) == "We check facts."


def test_import_links_the_member_and_keeps_author_order(publication, author):
    assert [a.name for a in publication.authorships.all()] == ["Jean Dupont", "Awa Sarr"]
    assert publication.authorships.get(position=2).member == author
    assert publication.abstract_en == "We check facts."
    assert publication.status == Publication.Status.PUBLISHED


def test_reimport_updates_without_duplicating_and_keeps_editorial_choices(publication, author):
    Publication.objects.filter(pk=publication.pk).update(status=Publication.Status.ARCHIVED)
    changed = copy.deepcopy(WORK)
    changed["title"] = "Fact-checking Senegalese news, revised"
    updated, created = import_work(changed)
    assert not created
    assert Publication.objects.count() == 1
    assert updated.title == "Fact-checking Senegalese news, revised"
    assert updated.status == Publication.Status.ARCHIVED


def test_shared_publication_stays_linked_to_every_member_coauthor(make_user, publication, author):
    """Importer un co-auteur ne doit pas délier les membres déjà reliés (cas Sall et Sarr)."""
    user = make_user("jean", Role.RESEARCHER, first_name="Jean", last_name="Dupont")
    coauthor = Member.objects.create(user=user, slug="jean-dupont", openalex_id="A1")
    updated, _created = import_work(WORK)
    assert [a.member for a in updated.authorships.all()] == [coauthor, author]


def test_manual_author_links_survive_a_reimport(make_user, publication):
    user = make_user("jean", Role.RESEARCHER, first_name="Jean", last_name="Dupont")
    jean = Member.objects.create(user=user, slug="jean-dupont")
    publication.authorships.filter(position=1).update(member=jean)
    updated, _created = import_work(WORK)
    assert updated.authorships.get(position=1).member == jean


def test_bibtex_and_reference(publication):
    entry = bibtex(publication)
    assert entry.startswith("@inproceedings{dupont2024factchecking,")
    assert "booktitle = {Conference on Data Science}" in entry
    assert r"title = {{Fact-checking Senegalese news \& opinions}}" in entry
    assert "pages = {10--18}" in entry
    assert reference(publication) == (
        "Jean Dupont, Awa Sarr (2024). Fact-checking Senegalese news & opinions. "
        "Conference on Data Science, 12(3), 10–18. https://doi.org/10.1109/test.2024.42"
    )


def test_publication_list_filters_by_member_and_answers_htmx(client, publication):
    response = client.get("/en/publications/", {"member": "awa-sarr"})
    assert [p.pk for p in response.context["publications"]] == [publication.pk]
    partial = client.get("/en/publications/", {"q": "senegalese"}, HTTP_HX_REQUEST="true")
    assert "<html" not in partial.content.decode()
    assert "Fact-checking Senegalese news" in partial.content.decode()


def test_unpublished_publications_stay_private(client, publication):
    Publication.objects.filter(pk=publication.pk).update(status=Publication.Status.PENDING)
    assert client.get(publication.get_absolute_url()).status_code == 404
    assert client.get("/en/publications/").context["publications"].count() == 0


def test_publication_page_offers_citation_and_bibtex_download(client, publication):
    html = client.get(f"/en/publications/{publication.slug}/").content.decode()
    assert "https://doi.org/10.1109/test.2024.42" in html
    assert 'href="/en/members/awa-sarr/"' in html
    download = client.get(f"/en/publications/{publication.slug}/bibtex/")
    assert download["Content-Type"].startswith("application/x-bibtex")
    assert download.content.decode().startswith("@inproceedings{")


def test_member_profile_lists_their_publications(client, publication):
    html = client.get("/en/members/awa-sarr/").content.decode()
    assert "Fact-checking Senegalese news" in html


def test_home_counts_published_publications(client, publication):
    response = client.get("/en/")
    assert ("Publications", 1, "document") in [
        (str(label), value, icon) for label, value, icon in response.context["counters"]
    ]


def test_publications_menu_entry_is_now_a_link(client):
    assert 'href="/fr/publications/"' in client.get("/fr/").content.decode()


def test_member_photo_gets_renditions_and_replaces_initials(client, author):
    buffer = BytesIO()
    Image.new("RGB", (400, 600), (200, 180, 160)).save(buffer, "JPEG")
    author.photo = SimpleUploadedFile("awa.jpg", buffer.getvalue(), content_type="image/jpeg")
    author.save()
    assert author.photo.storage.exists(rendition_name(author.photo.name, 384))
    html = client.get("/en/members/awa-sarr/").content.decode()
    assert "192w" in html
    assert ">AS</span>" not in html
