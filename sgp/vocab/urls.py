from django.urls import path

from . import views

app_name = "vocab"

urlpatterns = [
    path("", views.vocabulary_list, name="lists"),
    path("termos/<int:term_id>/", views.term_change, name="term"),
    path("<slug:code>/", views.vocabulary_detail, name="detail"),
]
