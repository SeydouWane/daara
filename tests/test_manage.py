"""Pages « Gérer » de l'espace : le back-office des éditeurs et des administrateurs."""

import pytest
from django.contrib.admin.models import LogEntry
from django.urls import reverse

from apps.core.models import HomeFeature, Page, SiteSettings
from apps.dashboard import manage
from apps.members.models import Affiliation, Institution, Member, Role, User
from apps.research.models import Dataset

pytestmark = pytest.mark.django_db


def list_url(key):
    return reverse("dashboard:manage_list", args=[key])


def add_url(key):
    return reverse("dashboard:manage_add", args=[key])


def test_django_admin_is_for_superusers_only(client, make_user, django_user_model):
    client.force_login(make_user("admin", Role.ADMIN, is_staff=True))
    assert client.get(reverse("admin:index")).status_code == 302  # page de connexion
    client.force_login(django_user_model.objects.create_superuser("root", password="x" * 12))
    assert client.get(reverse("admin:index")).status_code == 200


def test_administrator_manages_every_content_from_the_dashboard(client, make_user):
    """Le rôle suffit : ni statut « équipe » ni super-utilisateur."""
    client.force_login(make_user("admin", Role.ADMIN))
    for key, managed in manage.REGISTRY.items():
        assert client.get(list_url(key), follow=True).status_code == 200, key
        if not managed.singleton:
            assert client.get(add_url(key)).status_code == 200, key


def test_editor_writes_the_texts_but_not_the_structure(client, make_user):
    client.force_login(make_user("editeur", Role.EDITOR))
    assert client.get(list_url("site"), follow=True).status_code == 200
    for key in ("pages", "members", "publications", "datasets", "projects"):
        assert client.get(list_url(key)).status_code == 200, key
    assert client.get(add_url("pages")).status_code == 403
    for key in ("institutions", "accounts", "roles", "models"):
        assert client.get(list_url(key)).status_code == 403, key


def test_researcher_has_no_management_page(client, make_user):
    client.force_login(make_user("chercheur", Role.RESEARCHER, member=True))
    assert client.get(list_url("pages")).status_code == 403


def test_site_settings_list_opens_the_single_form(client, make_user):
    client.force_login(make_user("editeur", Role.EDITOR))
    response = client.get(list_url("site"))
    assert response["Location"] == reverse("dashboard:manage_edit", args=["site", 1])


def test_saving_updates_the_site_and_the_action_log(client, make_user):
    client.force_login(make_user("editeur", Role.EDITOR))
    feature = HomeFeature.objects.get(destination="research:models")
    response = client.post(
        reverse("dashboard:manage_edit", args=["home-cards", feature.pk]),
        {
            "title_fr": "Modèles",
            "title_en": "Our models",
            "text_fr": "Texte.",
            "text_en": "Text.",
            "icon": "chip",
            "destination": "research:models",
            "order": 2,
            "is_visible": "on",
        },
    )
    assert response.status_code == 302
    assert "Our models" in client.get("/en/").content.decode()
    entry = LogEntry.objects.get()
    assert entry.object_repr == "Our models" and entry.is_change()


def test_adding_a_member_opens_their_account(client, make_user):
    client.force_login(make_user("admin", Role.ADMIN))
    ucad = Institution.objects.get(slug="ucad")
    response = client.post(
        add_url("members"),
        {
            "first_name": "Aïssatou",
            "last_name": "Diop",
            "status": Member.Status.ACTIVE,
            "primary_institution": ucad.pk,
        },
    )
    assert response.status_code == 302, response.context["form"].errors
    member = Member.objects.get(slug="aissatou-diop")
    assert str(member) == "Aïssatou Diop"
    assert not User.objects.get(pk=member.user_id).has_usable_password()
    assert Affiliation.objects.get(member=member).is_primary


def test_dataset_is_created_with_its_authors(client, make_user):
    client.force_login(make_user("admin", Role.ADMIN))
    response = client.post(
        add_url("datasets"),
        {
            "title": "Corpus parlé wolof",
            "status": Dataset.Status.PUBLISHED,
            "access": Dataset.Access.OPEN,
            "doi": "https://doi.org/10.5281/ZENODO.123",
            "abstract_en": "Speech corpus.",
            "authors-TOTAL_FORMS": "1",
            "authors-INITIAL_FORMS": "0",
            "authors-MIN_NUM_FORMS": "0",
            "authors-MAX_NUM_FORMS": "1000",
            "authors-0-position": "1",
            "authors-0-name": "Awa Sarr",
        },
    )
    assert response.status_code == 302, response.context["form"].errors
    dataset = Dataset.objects.get(slug="corpus-parle-wolof")
    assert dataset.doi == "10.5281/zenodo.123"
    assert [a.name for a in dataset.authorships.all()] == ["Awa Sarr"]


def test_protected_institution_is_not_deleted(client, make_user):
    client.force_login(make_user("admin", Role.ADMIN, member=True))
    unchk = Institution.objects.get(slug="unchk")
    Affiliation.objects.create(member=Member.objects.get(slug="admin"), institution=unchk)
    response = client.post(reverse("dashboard:manage_delete", args=["institutions", unchk.pk]))
    assert response.status_code == 302
    assert Institution.objects.filter(pk=unchk.pk).exists()


def test_editing_shortcuts_lead_to_the_dashboard(client, make_user):
    assert "Editing shortcuts" not in client.get("/en/about/").content.decode()
    client.force_login(make_user("editeur", Role.EDITOR))
    html = client.get("/en/about/").content.decode()
    about = Page.objects.get(slug="about")
    assert reverse("dashboard:manage_edit", args=["pages", about.pk]) in html
    assert "/admin/" not in html


def test_home_page_texts_come_from_the_site_settings(client):
    SiteSettings.objects.filter(pk=1).update(
        tagline_en="Open science", contact_email="contact@daara.example"
    )
    HomeFeature.objects.filter(destination="training:list").update(is_visible=False)
    html = client.get("/en/").content.decode()
    assert "Open science" in html
    assert "contact@daara.example" in html  # pied de page
    assert "Courses, archived webinars" not in html


def test_added_page_gets_an_address_and_a_menu_entry(client):
    Page.objects.create(
        slug="faq",
        title_fr="Questions fréquentes",
        title_en="FAQ",
        body_fr="Texte.",
        body_en="Text.",
        menu=Page.Menu.ABOUT,
        status=Page.Status.PUBLISHED,
    )
    assert client.get("/en/pages/faq/").status_code == 200
    assert 'href="/en/pages/faq/"' in client.get("/en/").content.decode()
    assert client.get("/en/pages/about/").status_code == 404
