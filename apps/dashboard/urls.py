from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("validation/", views.ValidationQueueView.as_view(), name="validation"),
    path("translations/", views.TranslationsView.as_view(), name="translations"),
    path("indicators/", views.IndicatorsView.as_view(), name="indicators"),
    path("action-log/", views.ActionLogView.as_view(), name="action_log"),
    # Pages « Gérer » : un même jeu de vues pour chaque contenu du registre (manage.py).
    path("manage/<slug:key>/", views.ManageListView.as_view(), name="manage_list"),
    path("manage/<slug:key>/new/", views.ManageEditView.as_view(), name="manage_add"),
    path("manage/<slug:key>/<int:pk>/", views.ManageEditView.as_view(), name="manage_edit"),
    path(
        "manage/<slug:key>/<int:pk>/delete/",
        views.ManageDeleteView.as_view(),
        name="manage_delete",
    ),
]
