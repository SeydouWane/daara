"""Pages publiques des jeux de données, des modèles et des projets."""

import json
import re

import pytest

from apps.members.models import Institution, Member, Role
from apps.projects.models import Project
from apps.research.models import AIModel, Authorship, Dataset

pytestmark = pytest.mark.django_db


@pytest.fixture
def awa(make_user):
    user = make_user("awa", Role.RESEARCHER, first_name="Awa", last_name="Sarr", member=True)
    return Member.objects.get(user=user)


@pytest.fixture
def corpus(awa):
    dataset = Dataset.objects.create(
        title="Corpus parlé wolof",
        status=Dataset.Status.PUBLISHED,
        year=2026,
        doi="10.5281/zenodo.123",
        url="https://zenodo.org/records/123",
        license="CC BY 4.0",
        covered_languages="Wolof",
        abstract_en="Ten hours of transcribed Wolof speech.",
    )
    Authorship.objects.create(production=dataset, position=1, name="Awa Sarr", member=awa)
    return dataset


def test_empty_catalogues_explain_what_is_coming(client):
    for url in ("/fr/datasets/", "/fr/models/", "/fr/projects/"):
        response = client.get(url)
        assert response.status_code == 200, url
        assert response.context["paginator"].count == 0
        assert 'class="mt-4 flex flex-col items-center' in response.content.decode()


def test_dataset_page_offers_citation_and_structured_data(client, corpus):
    assert "Corpus parlé wolof" in client.get("/en/datasets/").content.decode()
    html = client.get(corpus.get_absolute_url()).content.decode()
    assert "Awa Sarr (2026). Corpus parlé wolof [Data set]." in html
    data = json.loads(
        re.search(r'<script type="application/ld\+json">(.*?)</script>', html).group(1)
    )
    assert data["@type"] == "Dataset"
    assert data["identifier"] == "https://doi.org/10.5281/zenodo.123"
    assert data["creator"] == [{"@type": "Person", "name": "Awa Sarr"}]


def test_draft_dataset_stays_hidden(client, corpus):
    Dataset.objects.filter(pk=corpus.pk).update(status=Dataset.Status.DRAFT)
    assert client.get(corpus.get_absolute_url()).status_code == 404
    assert "Corpus parlé wolof" not in client.get("/en/datasets/").content.decode()


def test_model_page_links_its_training_data(client, corpus):
    model = AIModel.objects.create(
        title="Wolof ASR",
        status=AIModel.Status.PUBLISHED,
        task="Speech recognition",
        huggingface_id="daara/wolof-asr",
    )
    model.datasets.add(corpus)
    html = client.get(model.get_absolute_url()).content.decode()
    assert "https://huggingface.co/daara/wolof-asr" in html
    assert corpus.get_absolute_url() in html
    assert "Wolof ASR" in client.get(corpus.get_absolute_url()).content.decode()


def test_catalogue_filters_by_access_with_htmx(client, corpus):
    response = client.get("/en/datasets/", {"access": "restricted"}, HTTP_HX_REQUEST="true")
    html = response.content.decode()
    assert "<html" not in html
    assert "Corpus parlé wolof" not in html


def test_project_page_shows_team_partners_and_outputs(client, awa, corpus):
    project = Project.objects.create(
        title_fr="Voix du Sénégal",
        title_en="Voices of Senegal",
        acronym="VOIX",
        slug="voix",
        summary_en="Speech technologies for Senegalese languages.",
        status=Project.Status.ONGOING,
        lead=awa,
    )
    project.members.add(awa)
    project.partners.add(Institution.objects.get(slug="ucad"))
    project.outputs.add(corpus)
    html = client.get("/en/projects/voix/").content.decode()
    assert "Voices of Senegal" in html
    assert "Awa Sarr" in html and "Project lead" in html
    assert corpus.get_absolute_url() in html
    assert "VOIX" in client.get("/en/projects/").content.decode()
    # Le profil du membre renvoie au projet et au jeu de données.
    profile = client.get(awa.get_absolute_url()).content.decode()
    assert "/en/projects/voix/" in profile and corpus.get_absolute_url() in profile


def test_draft_project_is_not_public(client):
    Project.objects.create(title_en="Secret", slug="secret", summary_en="Draft.")
    assert client.get("/en/projects/secret/").status_code == 404
    assert "Secret" not in client.get("/en/projects/").content.decode()


def test_home_counts_datasets_and_models(client, corpus):
    response = client.get("/en/")
    counters = {str(label): value for label, value, _icon in response.context["counters"]}
    assert counters["Datasets"] == 1
    assert counters["Models and code"] == 0
