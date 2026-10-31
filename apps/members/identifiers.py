"""Identifiants externes, stockés sous forme normalisée, sans préfixe d'URL (spec §6.2)."""

import re

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

ORCID_RE = re.compile(r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$")
ROR_RE = re.compile(r"^0[a-hj-km-np-tv-z0-9]{6}\d{2}$")


def _strip_prefix(value, *prefixes):
    value = (value or "").strip()
    for prefix in prefixes:
        if value.lower().startswith(prefix):
            return value[len(prefix) :]
    return value


def normalize_orcid(value):
    return _strip_prefix(value, "https://orcid.org/", "http://orcid.org/", "orcid.org/").upper()


def normalize_ror(value):
    return _strip_prefix(value, "https://ror.org/", "http://ror.org/", "ror.org/").lower()


def orcid_checksum_is_valid(orcid):
    """Clé de contrôle ISO 7064 11-2 du dernier caractère."""
    digits = orcid.replace("-", "")
    total = 0
    for char in digits[:-1]:
        total = (total + int(char)) * 2
    check = (12 - total % 11) % 11
    expected = "X" if check == 10 else str(check)
    return digits[-1] == expected


def validate_orcid(value):
    if not ORCID_RE.match(value) or not orcid_checksum_is_valid(value):
        raise ValidationError(_("Enter a valid ORCID iD, e.g. 0000-0002-1825-0097."))


def validate_ror(value):
    if not ROR_RE.match(value):
        raise ValidationError(_("Enter a valid ROR identifier, e.g. 05c3q4c27."))
