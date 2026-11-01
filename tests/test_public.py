import datetime
from io import BytesIO

import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from PIL import Image

from apps.core.images import rendition_name, rendition_widths
from apps.core.models import Page
from apps.core.templatetags.daara import render_markdown
from apps.members.models import Affiliation, Axis, Institution, Member, Role

pytestmark = pytest.mark.django_db


@pytest.fixture
def team(make_user, axis):
    """Deux membres actifs et un alumni, rattachés à l'UNCHK (créée par la migration)."""
    unchk = Institution.objects.get(slug="unchk")
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


def test_senegalese_public_universities_are_partners():
    acronyms = set(
        Institution.objects.filter(country="SN", is_partner=True).values_list("acronym", flat=True)
    )
    assert {"UCAD", "UGB", "UASZ", "UIDT", "UADB", "USSEIN", "UNCHK", "UAM"} <= acronyms


def test_home_announces_the_partner_universities(client):
    html = client.get("/fr/").content.decode()
    assert "En partenariat avec 8 universités" in html
    assert "UCAD" in html


def test_institution_logo_gets_webp_renditions(client):
    buffer = BytesIO()
    Image.new("RGBA", (600, 300), (15, 92, 74, 255)).save(buffer, "PNG")
    ucad = Institution.objects.get(slug="ucad")
    ucad.logo = SimpleUploadedFile("ucad.png", buffer.getvalue(), content_type="image/png")
    ucad.save()
    for width in (160, 320):
        assert ucad.logo.storage.exists(rendition_name(ucad.logo.name, width))

    html = client.get("/en/partners/").content.decode()
    assert "160w" in html and "320w" in html
    assert 'alt="Université Cheikh Anta Diop de Dakar"' in html
    # Sans logo, le sigle sert de monogramme.
    assert ">UGB</span>" in html


def test_renditions_never_upscale():
    assert rendition_widths(200, (160, 320)) == [160, 200]
    assert rendition_widths(1000, (160, 320)) == [160, 320]
    assert rendition_widths(None, (160, 320)) == []


def test_axis_icon_is_drawn_on_the_axes_page(client, axis):
    Axis.objects.filter(pk=axis.pk).update(icon=Axis.Icon.LANGUAGE)
    html = client.get("/en/axes/").content.decode()
    assert 'viewBox="0 0 48 48"' in html


def test_alumni_profile_shows_the_period(client, team):
    html = client.get("/en/members/ali/").content.decode()
    assert "Alumni" in html
    assert "2025" in html
