from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("axes/", views.AxesView.as_view(), name="axes"),
    path("governance/", views.PageView.as_view(slug="governance"), name="governance"),
    path("partners/", views.PartnersView.as_view(), name="partners"),
    path("contact/", views.PageView.as_view(slug="contact"), name="contact"),
    path("legal-notice/", views.PageView.as_view(slug="legal-notice"), name="legal_notice"),
    path("privacy/", views.PageView.as_view(slug="privacy"), name="privacy"),
    path("dev/logo/", views.LogoSheetView.as_view(), name="logo_sheet"),
]
