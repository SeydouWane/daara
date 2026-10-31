import datetime

import pytest
from django.utils import timezone

from apps.members.models import Axis, Member, Role, RoleAssignment, User


@pytest.fixture
def axis(db):
    return Axis.objects.create(name_fr="Langues", name_en="Languages", slug="langues")


@pytest.fixture
def make_user(db):
    """Crée un utilisateur avec les rôles donnés ; `axis` sert aux rôles de responsable d'axe."""

    def make(username, *roles, axis=None, member=False, **fields):
        user = User.objects.create_user(username, password="motdepasse-test", **fields)
        for role in roles:
            RoleAssignment.objects.create(
                user=user,
                role=role,
                axis=axis if role == Role.AXIS_LEAD else None,
                expires_on=(
                    timezone.localdate() + datetime.timedelta(days=30)
                    if role == Role.OBSERVER
                    else None
                ),
            )
        if member:
            Member.objects.create(user=user, slug=username)
        return user

    return make
