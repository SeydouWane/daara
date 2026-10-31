from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("dev/logo/", views.LogoSheetView.as_view(), name="logo_sheet"),
]
