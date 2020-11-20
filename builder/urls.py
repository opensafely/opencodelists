from django.urls import path

from . import views

app_name = "builder"

urlpatterns = [
    path("", views.index, name="index"),
    path("<username>/", views.user, name="user"),
    path("<username>/<draft_slug>/", views.draft, name="draft"),
    path("<username>/<draft_slug>/search/<search_slug>/", views.search, name="search"),
    path(
        "<username>/<draft_slug>/no-search-term/",
        views.no_search_term,
        name="no-search-term",
    ),
    path("<username>/<draft_slug>/update/", views.update, name="update"),
    path("<username>/<draft_slug>/search/", views.new_search, name="new_search"),
    path("<username>/<draft_slug>/download.csv", views.download, name="download"),
    path(
        "<username>/<draft_slug>/download-dmd.csv",
        views.download_dmd,
        name="download-dmd",
    ),
]
