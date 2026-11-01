from django.urls import path

from . import views

app_name = "research"

urlpatterns = [
    path("publications/", views.PublicationListView.as_view(), name="publications"),
    path("publications/<slug:slug>/", views.PublicationDetailView.as_view(), name="publication"),
    path("publications/<slug:slug>/bibtex/", views.publication_bibtex, name="publication_bibtex"),
]
