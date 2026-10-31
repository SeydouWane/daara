import datetime

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError
from django.utils import timezone

from apps.members.models import Axis, Member, Role, RoleAssignment
from apps.members.permissions import ALL, Module, can, granted

pytestmark = pytest.mark.django_db


def test_anonymous_visitor_gets_the_visitor_column():
    visitor = AnonymousUser()
    assert granted(visitor, Module.PUBLICATIONS) == {"L"}
    assert granted(visitor, Module.REGISTRATIONS) == {"C"}
    assert granted(visitor, Module.DASHBOARD) == set()


def test_single_role_matches_its_column(make_user):
    student = make_user("awa", Role.PHD_STUDENT)
    assert granted(student, Module.PUBLICATIONS) == set("LCM")
    assert not can(student, "P", Module.PUBLICATIONS)
    assert not can(student, "V", Module.PUBLICATIONS)


def test_combined_roles_add_up(make_user, axis):
    user = make_user("moussa", Role.RESEARCHER, Role.AXIS_LEAD, Role.EDITOR, axis=axis)
    assert granted(user, Module.PUBLICATIONS) == set("LCMPV")
    assert granted(user, Module.EDITORIAL_PAGES) == set("LCMP")
    assert granted(user, Module.TRAININGS) == set("LCMPV")


def test_axis_lead_validates_only_their_axis(make_user, axis):
    other = Axis.objects.create(name_fr="Santé", name_en="Health", slug="sante")
    lead = make_user("lead", Role.AXIS_LEAD, axis=axis)
    assert can(lead, "V", Module.PUBLICATIONS, axis=axis)
    assert not can(lead, "V", Module.PUBLICATIONS, axis=other)


def test_expired_role_no_longer_counts(make_user):
    user = make_user("ancien")
    yesterday = timezone.localdate() - datetime.timedelta(days=1)
    RoleAssignment.objects.create(
        user=user, role=Role.RESEARCHER, starts_on=yesterday, expires_on=yesterday
    )
    assert granted(user, Module.PUBLICATIONS) == {"L"}


def test_administrators_get_every_right(make_user, django_user_model):
    admin = make_user("admin", Role.ADMIN)
    superuser = django_user_model.objects.create_superuser("root", password="motdepasse-test")
    for module in Module:
        assert granted(admin, module) == ALL
        assert granted(superuser, module) == ALL


def test_alumni_keep_reading_but_lose_write_rights(make_user):
    user = make_user("alumni", Role.RESEARCHER, member=True)
    Member.objects.filter(user=user).update(
        status=Member.Status.ALUMNI, left_on=timezone.localdate()
    )
    user.refresh_from_db()
    assert granted(user, Module.PUBLICATIONS) == {"L"}


def test_observer_access_needs_an_expiry_of_twelve_months_at_most(make_user):
    user = make_user("bailleur")
    today = timezone.localdate()
    with pytest.raises(ValidationError):
        RoleAssignment(user=user, role=Role.OBSERVER, starts_on=today).full_clean()
    with pytest.raises(ValidationError):
        RoleAssignment(
            user=user,
            role=Role.OBSERVER,
            starts_on=today,
            expires_on=today + datetime.timedelta(days=400),
        ).full_clean()
    RoleAssignment(
        user=user,
        role=Role.OBSERVER,
        starts_on=today,
        expires_on=today + datetime.timedelta(days=365),
    ).full_clean()


def test_an_axis_has_a_single_active_lead(make_user, axis):
    make_user("premier", Role.AXIS_LEAD, axis=axis)
    second = make_user("second")
    with pytest.raises(ValidationError):
        RoleAssignment(user=second, role=Role.AXIS_LEAD, axis=axis).full_clean()


def test_only_axis_leads_are_scoped_to_an_axis(make_user, axis):
    user = make_user("chercheur")
    with pytest.raises(ValidationError):
        RoleAssignment(user=user, role=Role.RESEARCHER, axis=axis).full_clean()
    with pytest.raises(ValidationError):
        RoleAssignment(user=user, role=Role.AXIS_LEAD).full_clean()


def test_orcid_is_normalised_and_checked(make_user):
    member = Member(
        user=make_user("orcid"), slug="orcid", orcid="https://orcid.org/0000-0002-1825-0097"
    )
    member.full_clean()
    assert member.orcid == "0000-0002-1825-0097"

    member.orcid = "0000-0002-1825-0098"
    with pytest.raises(ValidationError):
        member.full_clean()
