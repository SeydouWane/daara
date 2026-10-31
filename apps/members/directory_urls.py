from django.urls import path

from . import views

app_name = "directory"

urlpatterns = [
    path("", views.DirectoryView.as_view(), name="list"),
    path("<slug:slug>/", views.ProfileView.as_view(), name="detail"),
]
