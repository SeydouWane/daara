from django.urls import path

from . import views

app_name = "dashboard"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("validation/", views.ValidationQueueView.as_view(), name="validation"),
    path("translations/", views.TranslationsView.as_view(), name="translations"),
    path("indicators/", views.IndicatorsView.as_view(), name="indicators"),
]
