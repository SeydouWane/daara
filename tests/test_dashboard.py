import pytest

from apps.members.models import Member, Role

pytestmark = pytest.mark.django_db


def sidebar_labels(response):
    return {
        str(link["label"]) for section in response.context["sidebar"] for link in section["links"]
    }


def test_dashboard_requires_login(client):
    response = client.get("/en/dashboard/")
    assert response.status_code == 302
    assert response["Location"] == "/en/account/login/?next=/en/dashboard/"


def test_login_leads_to_the_dashboard(client, make_user):
    make_user("awa", Role.PHD_STUDENT)
    response = client.post("/en/account/login/", {"username": "awa", "password": "motdepasse-test"})
    assert response.status_code == 302
    assert response["Location"] == "/en/dashboard/"


def test_failed_login_does_not_echo_the_password(client, make_user):
    make_user("awa")
    response = client.post("/en/account/login/", {"username": "awa", "password": "mauvais-mdp"})
    assert response.status_code == 200
    assert "mauvais-mdp" not in response.content.decode()


def test_sidebar_merges_every_role(client, make_user, axis):
    user = make_user("moussa", Role.RESEARCHER, Role.AXIS_LEAD, Role.EDITOR, axis=axis, member=True)
    client.force_login(user)
    labels = sidebar_labels(client.get("/en/dashboard/"))
    assert labels == {"Overview", "My profile", "Validation queue", "Translations", "Indicators"}


def test_phd_student_cannot_open_the_validation_queue(client, make_user):
    client.force_login(make_user("awa", Role.PHD_STUDENT, member=True))
    labels = sidebar_labels(client.get("/en/dashboard/"))
    assert "Validation queue" not in labels
    assert client.get("/en/dashboard/validation/").status_code == 403


def test_observer_sees_indicators_only(client, make_user):
    client.force_login(make_user("fatou", Role.OBSERVER))
    labels = sidebar_labels(client.get("/en/dashboard/"))
    assert labels == {"Overview", "Indicators"}
    assert client.get("/en/dashboard/indicators/").status_code == 200


def test_staff_administrator_reaches_role_management(client, make_user):
    client.force_login(make_user("admin", Role.ADMIN, is_staff=True))
    labels = sidebar_labels(client.get("/en/dashboard/"))
    assert {"Members and roles", "Action log"} <= labels


def test_member_edits_their_own_profile(client, make_user):
    user = make_user("awa", Role.PHD_STUDENT, member=True)
    client.force_login(user)
    response = client.post(
        "/en/dashboard/profile/",
        {
            "bio_fr": "Doctorante en TAL.",
            "bio_en": "PhD student in NLP.",
            "orcid": "0000-0002-1825-0097",
        },
    )
    assert response.status_code == 302
    member = Member.objects.get(user=user)
    assert member.bio_en == "PhD student in NLP."
    assert member.orcid == "0000-0002-1825-0097"


def test_translations_list_contents_written_in_one_language(client, make_user):
    make_user("auteur", Role.RESEARCHER, member=True)
    Member.objects.filter(user__username="auteur").update(bio_fr="Biographie en français.")
    client.force_login(make_user("editeur", Role.EDITOR))
    response = client.get("/en/dashboard/translations/")
    assert response.status_code == 200
    assert [item["missing"] for item in response.context["items"]] == [["en"]]
