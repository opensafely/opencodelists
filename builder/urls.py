from django.urls import path

from . import views

app_name = "builder"

urlpatterns = [
    path("", views.index, name="index"),
    path("<username>/", views.user, name="user"),
]

for subpath, view in [
    ("", views.draft),
    ("search/<search_slug>/", views.search),
    ("no-search-term/", views.no_search_term),
    ("update/", views.update),
    ("search/", views.new_search),
    ("download.csv", views.download),
    ("download-dmd.csv", views.download_dmd),
]:
    urlpatterns.append(path("codelist/<hash>/" + subpath, view, name=view.__name__))
    urlpatterns.append(path("<username>/<draft_slug>/" + subpath, view))
