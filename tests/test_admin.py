import pytest
from django.urls import reverse

from apps.core.models import HomeFeature, Page, SiteSettings
from apps.members.models import Member, Role, User

pytestmark = pytest.mark.django_db

CHANGELISTS = [
    "core_sitesettings",
    "core_homefeature",
    "core_page",
    "core_standard",
    "core_partnershipstep",
    "members_axis",
    "research_publication",
    "members_member",
    "members_grade",
    "members_institution",
    "members_user",
    "members_roleassignment",
    "admin_logentry",
]


def changelist(name):
    return reverse(f"admin:{name}_changelist")


def test_admin_index_follows_the_public_site(client, django_user_model):
    client.force_login(django_user_model.objects.create_superuser("root", password="x" * 12))
    sections = [str(app["name"]) for app in client.get(reverse("admin:index")).context["app_list"]]
    assert sections == [
        "Home page and footer",
        "Pages: About, Partners, Contact…",
        "Research",
        "Members",
        "Partner institutions",
        "Accounts and roles",
        "Action log",
    ]


def test_administrator_role_manages_everything_without_superuser_status(client, make_user):
    """Les droits viennent du rôle : aucune permission Django à cocher à la main."""
    client.force_login(make_user("admin", Role.ADMIN, is_staff=True))
    for name in CHANGELISTS:
        response = client.get(changelist(name), follow=True)
        assert response.status_code == 200, name
    assert client.get(reverse("admin:members_member_add")).status_code == 200


def test_lists_count_active_members(client, make_user):
    client.force_login(make_user("admin", Role.ADMIN, is_staff=True))
    for name in ("members_institution", "members_axis"):
        html = client.get(changelist(name)).content.decode()
        assert "Member.None" not in html, name


def test_editor_writes_the_texts_but_not_the_structure(client, make_user):
    client.force_login(make_user("editeur", Role.EDITOR, is_staff=True))
    settings_url = reverse("admin:core_sitesettings_change", args=[SiteSettings.load().pk])
    assert client.get(settings_url).status_code == 200
    assert client.get(changelist("core_page")).status_code == 200
    assert client.get(changelist("members_member")).status_code == 200
    # Créer une page, gérer les institutions ou les comptes reste à l'administrateur.
    assert client.get(reverse("admin:core_page_add")).status_code == 403
    assert client.get(changelist("members_institution")).status_code == 403
    assert client.get(changelist("members_user")).status_code == 403


def test_staff_status_alone_gives_no_right(make_user):
    user = make_user("chercheur", Role.RESEARCHER, is_staff=True)
    assert not user.has_perm("research.change_publication")
    assert not user.has_perm("core.change_page")


def test_site_settings_list_opens_the_single_form(client, make_user):
    client.force_login(make_user("editeur", Role.EDITOR, is_staff=True))
    response = client.get(changelist("core_sitesettings"))
    assert response.status_code == 302
    assert response["Location"] == reverse("admin:core_sitesettings_change", args=[1])


def test_home_page_texts_come_from_the_administration(client):
    SiteSettings.objects.filter(pk=1).update(
        tagline_en="Open science", contact_email="contact@daara.example"
    )
    HomeFeature.objects.filter(destination="training:list").update(is_visible=False)
    html = client.get("/en/").content.decode()
    assert "Open science" in html
    assert "contact@daara.example" in html  # pied de page
    assert "Models and demonstrators" in html
    assert "Courses, archived webinars" not in html


def test_admin_bar_links_what_the_page_shows(client, make_user):
    assert "Administration shortcuts" not in client.get("/en/about/").content.decode()

    client.force_login(make_user("editeur", Role.EDITOR, is_staff=True))
    html = client.get("/en/about/").content.decode()
    about = Page.objects.get(slug="about")
    assert reverse("admin:core_page_change", args=[about.pk]) in html
    assert changelist("core_standard") in html


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
    response = client.get("/en/pages/faq/")
    assert response.status_code == 200
    assert 'href="/en/pages/faq/"' in client.get("/en/").content.decode()
    # Une page fixe garde son unique adresse.
    assert client.get("/en/pages/about/").status_code == 404


def test_adding_a_member_opens_their_account(client, make_user):
    client.force_login(make_user("admin", Role.ADMIN, is_staff=True))
    response = client.post(
        reverse("admin:members_member_add"),
        {
            "first_name": "Aïssatou",
            "last_name": "Diop",
            "status": Member.Status.ACTIVE,
            "affiliations-TOTAL_FORMS": "0",
            "affiliations-INITIAL_FORMS": "0",
            "affiliations-MIN_NUM_FORMS": "0",
            "affiliations-MAX_NUM_FORMS": "1000",
        },
    )
    assert response.status_code == 302, response.context["adminform"].form.errors
    member = Member.objects.get(slug="aissatou-diop")
    assert str(member) == "Aïssatou Diop"
    assert not User.objects.get(pk=member.user_id).has_usable_password()


def test_sidebar_opens_the_public_site_to_editors(client, make_user):
    client.force_login(make_user("editeur", Role.EDITOR, is_staff=True))
    sidebar = client.get("/en/dashboard/").context["sidebar"]
    labels = {str(link["label"]) for section in sidebar for link in section["links"]}
    assert {"Home page and footer", "Pages", "Members", "Publications"} <= labels
    assert "Partner institutions" not in labels
    assert "Members and roles" not in labels
