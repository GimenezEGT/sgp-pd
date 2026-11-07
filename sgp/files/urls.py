from django.urls import path

from . import views

app_name = "files"

urlpatterns = [
    path("<int:file_id>/", views.download, name="download"),
]
