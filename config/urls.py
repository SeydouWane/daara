from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from apps.core import views as core_views

urlpatterns = [
    path("healthz", core_views.healthz, name="healthz"),
    path("i18n/<str:lang>/", core_views.switch_language, name="switch_language"),
]

# Toutes les pages publiques sont préfixées par la langue : /fr/…, /en/… (spec §5.3).
urlpatterns += i18n_patterns(
    path(settings.ADMIN_URL, admin.site.urls),
    path("account/", include("apps.members.urls")),
    path("members/", include("apps.members.directory_urls")),
    path("", include("apps.research.urls")),
    path("dashboard/", include("apps.dashboard.urls")),
    path("", include("apps.core.urls")),
)

if settings.DEBUG:
    # En développement seulement ; en production, le serveur web sert les fichiers téléversés.
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
