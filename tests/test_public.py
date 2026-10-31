import datetime

import pytest
from django.core.exceptions import ValidationError

from apps.core.models import Page
from apps.core.templatetags.daara import render_markdown
from apps.members.models import Affiliation, Axis, Institution, Member, Role

pytestmark = pytest.mark.django_db


@pytest.fixture
def team(make_user, axis):
    """Deux membres actifs et un alumni, rattachés à une même institution."""
    unchk = Institution.objects.create(
        name_fr="Université numérique", name_en="Digital university", acronym="UNCHK",
        slug="unchk", country="SN",
    )  # fmt: skip
    health = Axis.objects.create(name_fr="Santé", name_en="Health", slug="sante")

    def add(username, first_name, last_name, member_axis, alumni=False):
        user = make_user(username, Role.RESEARCHER, first_name=first_name, last_name=last_name)
        member = Member.objects.create(
            user=user,
            slug=username,
            status=Member.Status.ALUMNI if alumni else Member.Status.ACTIVE,
            left_on=datetime.date(2025, 6, 30) if alumni else None,
        )
        member.axes.add(member_axis)
        Affiliation.objects.create(member=member, institution=unchk, is_primary=True)
        return member

    return [
        add("awa", "Awa", "Sarr", axis),
        add("moussa", "Moussa", "Ndiaye", health),
        add("ali", "Ali", "Ba", axis, alumni=True),
    ]


def test_main_menu_shows_sections_and_upcoming_modules(client):
    html = client.get("/fr/").content.decode()
    for label in ("À propos", "Recherche", "Membres", "Formation et actualités", "Contact"):
        assert label in html
    assert 'href="/fr/about/"' in html
    assert 'href="/fr/members/"' in html
    # Les publications n'existent pas encore : libellé « bientôt », sans lien.
    assert "bientôt" in html
    assert "/fr/publications/" not in html


def test_language_selector_marks_the_current_language(client):
    html = client.get("/fr/about/").content.decode()
    assert '<span lang="fr" aria-current="true"' in html
    assert 'href="/i18n/en/?next=%2Ffr%2Fabout%2F"' in html


def test_seeded_pages_are_served_in_both_languages(client):
    assert "Gouvernance" in client.get("/fr/governance/").content.decode()
    assert "Governance" in client.get("/en/governance/").content.decode()


def test_draft_pages_stay_hidden_until_published(client):
    assert client.get("/fr/legal-notice/").status_code == 404
    assert 'href="/fr/legal-notice/"' not in client.get("/fr/").content.decode()
    Page.objects.filter(slug="legal-notice").update(status=Page.Status.PUBLISHED)
    assert client.get("/fr/legal-notice/").status_code == 200
    assert 'href="/fr/legal-notice/"' in client.get("/fr/").content.decode()


def test_publishing_requires_every_editorial_language():
    page = Page(slug="essai", title_fr="Titre", body_fr="Texte", status=Page.Status.PUBLISHED)
    with pytest.raises(ValidationError):
        page.full_clean()
    page.title_en, page.body_en = "Title", "Text"
    page.full_clean()


def test_missing_translation_falls_back_with_a_notice(client):
    Page.objects.filter(slug="contact").update(body_en="")
    html = client.get("/en/contact/").content.decode()
    assert "Available in French only" in html
    assert 'class="prose" lang="fr"' in html


def test_markdown_is_rendered_and_sanitised():
    html = render_markdown("## Titre\n\n<script>alert(1)</script> [lien](https://example.org)")
    assert "<h2>Titre</h2>" in html
    assert "<script>" not in html
    assert 'href="https://example.org"' in html


def test_partners_page_lists_institutions(client, team):
    html = client.get("/en/partners/").content.decode()
    assert "UNCHK" in html
    assert "/en/members/?institution=unchk" in html


def test_axes_page_names_the_axis_lead(client, make_user, axis):
    make_user("lead", Role.AXIS_LEAD, axis=axis, first_name="Moussa", last_name="Ndiaye")
    html = client.get("/en/axes/").content.decode()
    assert "Languages" in html
    assert "Moussa Ndiaye" in html


def test_directory_lists_active_members_alphabetically(client, team):
    response = client.get("/en/members/")
    assert [member.slug for member in response.context["members"]] == ["moussa", "awa"]


def test_directory_filters_by_axis_and_shows_alumni_on_request(client, team):
    by_axis = client.get("/en/members/", {"axis": "langues"})
    assert [member.slug for member in by_axis.context["members"]] == ["awa"]
    alumni = client.get("/en/members/", {"status": "alumni"})
    assert [member.slug for member in alumni.context["members"]] == ["ali"]


def test_directory_returns_only_the_results_to_htmx(client, team):
    response = client.get("/en/members/", {"q": "sarr"}, HTTP_HX_REQUEST="true")
    html = response.content.decode()
    assert "<html" not in html
    assert "Awa Sarr" in html
    assert "Moussa Ndiaye" not in html


def test_profile_page_shows_axes_and_external_links(client, team):
    Member.objects.filter(slug="awa").update(orcid="0000-0002-1825-0097")
    html = client.get("/en/members/awa/").content.decode()
    assert "Awa Sarr" in html
    assert "Languages" in html
    assert "https://orcid.org/0000-0002-1825-0097" in html


def test_alumni_profile_shows_the_period(client, team):
    html = client.get("/en/members/ali/").content.decode()
    assert "Alumni" in html
    assert "2025" in html
