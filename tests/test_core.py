import re

import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import override_settings

pytestmark = pytest.mark.django_db


def test_root_redirects_to_browser_language(client):
    response = client.get("/", HTTP_ACCEPT_LANGUAGE="fr-FR,fr;q=0.9")
    assert response.status_code == 302
    assert response["Location"] == "/fr/"


def test_root_falls_back_to_default_language(client):
    response = client.get("/", HTTP_ACCEPT_LANGUAGE="de")
    assert response["Location"] == "/en/"


@pytest.mark.parametrize(
    ("lang", "title"),
    [
        ("fr", "Données, Apprentissage Automatique et Recherche en Afrique"),
        ("en", "AI Research Alliance for Africa"),
    ],
)
def test_home_is_served_in_each_language(client, lang, title):
    response = client.get(f"/{lang}/")
    assert response.status_code == 200
    html = response.content.decode()
    assert f'<html lang="{lang}">' in html
    assert title in html


def test_header_shows_reduced_logo_and_footer_offers_animation_pause(client):
    html = client.get("/fr/").content.decode()
    assert 'class="logo-symbol"' in html
    assert '<span class="logo max-sm:hidden">DAARA</span>' in html
    assert "data-motion-toggle" in html
    assert "Mettre en pause les animations" in html


def test_pages_declare_reciprocal_hreflang(client):
    html = client.get("/fr/").content.decode()
    assert '<link rel="alternate" hreflang="fr" href="http://testserver/fr/">' in html
    assert '<link rel="alternate" hreflang="en" href="http://testserver/en/">' in html
    assert '<link rel="alternate" hreflang="x-default" href="http://testserver/en/">' in html


def test_language_switch_keeps_current_page_and_sets_cookie(client):
    response = client.get("/i18n/fr/", {"next": "/en/"})
    assert response.status_code == 302
    assert response["Location"] == "/fr/"
    assert response.cookies[settings.LANGUAGE_COOKIE_NAME].value == "fr"


def test_language_switch_falls_back_to_home_for_unknown_page(client):
    response = client.get("/i18n/en/", {"next": "/fr/page-inexistante/"})
    assert response["Location"] == "/en/"


def test_language_switch_ignores_external_next(client):
    response = client.get("/i18n/fr/", {"next": "https://example.com/"})
    assert response["Location"] == "/fr/"


def test_language_switch_rejects_inactive_language(client):
    assert client.get("/i18n/de/").status_code == 404


def test_healthz_checks_database(client):
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.content == b"ok"


def test_logo_sheet_is_dev_only(client):
    assert client.get("/fr/dev/logo/").status_code == 404
    with override_settings(DEBUG=True):
        assert client.get("/fr/dev/logo/").status_code == 200


def test_custom_user_model_is_active():
    assert get_user_model()._meta.label == "members.User"


def test_french_interface_is_fully_translated():
    """Niveau 1 de la spec §5.1 : l'interface est traduite à 100 %."""
    po = (settings.BASE_DIR / "locale/fr/LC_MESSAGES/django.po").read_text(encoding="utf-8")
    assert "#, fuzzy" not in po
    entries = po.split("\n\n")[1:]  # la première entrée est l'en-tête du catalogue
    untranslated = [
        entry
        for entry in entries
        if re.search(r'^msgstr ""$', entry, re.M) and not re.search(r'^msgstr ""\n"', entry, re.M)
    ]
    assert untranslated == []
