from django.urls import path

from . import views

app_name = "research"

urlpatterns = [
    path("publications/", views.PublicationListView.as_view(), name="publications"),
    path("publications/<slug:slug>/", views.PublicationDetailView.as_view(), name="publication"),
    path("publications/<slug:slug>/bibtex/", views.publication_bibtex, name="publication_bibtex"),
    path("datasets/", views.DatasetListView.as_view(), name="datasets"),
    path("datasets/<slug:slug>/", views.DatasetDetailView.as_view(), name="dataset"),
    path("models/", views.ModelListView.as_view(), name="models"),
    path("models/<slug:slug>/", views.ModelDetailView.as_view(), name="model"),
]
