import csv
import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from codelists.hierarchy import Hierarchy
from codelists.search import do_search
from mappings.bnfdmd.mappers import bnf_to_dmd
from opencodelists.models import User

from . import actions
from .forms import DraftCodelistForm
from .models import DraftCodelist

NO_SEARCH_TERM = object()


def download(request, username, draft_slug):
    draft = get_object_or_404(DraftCodelist, owner=username, slug=draft_slug)

    # get codes
    codes = list(
        draft.code_objs.filter(status__contains="+").values_list("code", flat=True)
    )

    # get terms for codes
    code_to_term = draft.coding_system.lookup_names(codes)

    timestamp = timezone.now().strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{username}-{draft_slug}-{timestamp}.csv"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    # render to csv
    writer = csv.writer(response)
    writer.writerow(["id", "term"])
    writer.writerows([(k, v) for k, v in code_to_term.items()])

    return response


def download_dmd(request, username, draft_slug):
    draft = get_object_or_404(
        DraftCodelist, owner=username, slug=draft_slug, coding_system_id="bnf"
    )

    # get codes
    codes = list(
        draft.code_objs.filter(status__contains="+").values_list("code", flat=True)
    )

    timestamp = timezone.now().strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{username}-{draft_slug}-{timestamp}.csv"

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'

    dmd_rows = bnf_to_dmd(codes)
    writer = csv.DictWriter(response, ["dmd_type", "dmd_id", "dmd_name", "bnf_code"])
    writer.writeheader()
    writer.writerows(dmd_rows)

    return response


@login_required
def index(request):
    return redirect("builder:user", request.user.username)


@login_required
def user(request, username):
    user = get_object_or_404(User, username=username)

    if request.method == "POST":
        form = DraftCodelistForm(request.POST)
        if form.is_valid():
            draft = actions.create_draft(
                owner=user,
                name=form.cleaned_data["name"],
                coding_system_id=form.cleaned_data["coding_system_id"],
            )
            return redirect(draft)
    else:
        form = DraftCodelistForm()

    ctx = {
        "user": user,
        "drafts": user.drafts.all().order_by("name"),
        "form": form,
    }
    return render(request, "builder/user.html", ctx)


@login_required
def draft(request, username, draft_slug, search_slug=None):
    draft = get_object_or_404(DraftCodelist, owner=username, slug=draft_slug)
    coding_system = draft.coding_system

    code_to_status = dict(draft.code_objs.values_list("code", "status"))
    all_codes = list(code_to_status)

    included_codes = [c for c in all_codes if code_to_status[c] == "+"]
    excluded_codes = [c for c in all_codes if code_to_status[c] == "-"]

    if search_slug is None:
        search = None
        displayed_codes = list(code_to_status)
    elif search_slug is NO_SEARCH_TERM:
        search = NO_SEARCH_TERM
        displayed_codes = list(
            draft.code_objs.filter(results=None).values_list("code", flat=True)
        )
    else:
        search = get_object_or_404(draft.searches, slug=search_slug)
        displayed_codes = list(search.results.values_list("code_obj__code", flat=True))

    searches = [
        {"term": s.term, "url": s.get_absolute_url(), "active": s == search}
        for s in draft.searches.order_by("term")
    ]

    if searches and draft.code_objs.filter(results=None).exists():
        searches.append(
            {
                "term": "[no search term]",
                "url": reverse(
                    "builder:no-search-term",
                    args=[draft.owner.username, draft.slug],
                ),
                "active": search_slug == NO_SEARCH_TERM,
            }
        )

    filter = request.GET.get("filter")
    if filter == "included":
        displayed_codes = [c for c in displayed_codes if "+" in code_to_status[c]]
    elif filter == "excluded":
        displayed_codes = [c for c in displayed_codes if "-" in code_to_status[c]]
    elif filter == "unresolved":
        displayed_codes = [c for c in displayed_codes if code_to_status[c] == "?"]
    elif filter == "in-conflict":
        displayed_codes = [c for c in displayed_codes if code_to_status[c] == "!"]
        filter = "in conflict"

    hierarchy = Hierarchy.from_codes(coding_system, all_codes)

    ancestor_codes = hierarchy.filter_to_ultimate_ancestors(set(displayed_codes))
    code_to_term = coding_system.code_to_term(hierarchy.nodes | set(all_codes))
    tree_tables = sorted(
        (type.title(), sorted(codes, key=code_to_term.__getitem__))
        for type, codes in coding_system.codes_by_type(
            ancestor_codes, hierarchy
        ).items()
    )

    update_url = reverse("builder:update", args=[draft.owner.username, draft.slug])
    search_url = reverse("builder:new_search", args=[draft.owner.username, draft.slug])
    download_url = reverse("builder:download", args=[draft.owner.username, draft.slug])

    if draft.coding_system_id == "bnf":
        download_dmd_url = reverse(
            "builder:download-dmd", args=[draft.owner.username, draft.slug]
        )
    else:
        download_dmd_url = None

    ctx = {
        "user": draft.owner,
        "draft": draft,
        "search": search,
        "NO_SEARCH_TERM": NO_SEARCH_TERM,
        # The following values are passed to the CodelistBuilder component.
        # When any of these chage, use generate_builder_fixture to update
        # static/test/js/fixtures/elbow.json.
        # {
        "searches": searches,
        "filter": filter,
        "tree_tables": tree_tables,
        "all_codes": all_codes,
        "included_codes": included_codes,
        "excluded_codes": excluded_codes,
        "parent_map": {p: list(cc) for p, cc in hierarchy.parent_map.items()},
        "child_map": {c: list(pp) for c, pp in hierarchy.child_map.items()},
        "code_to_term": code_to_term,
        "code_to_status": code_to_status,
        "is_editable": request.user == draft.owner,
        "update_url": update_url,
        "search_url": search_url,
        "download_url": download_url,
        "download_dmd_url": download_dmd_url,
        # }
    }

    return render(request, "builder/draft.html", ctx)


@login_required
@require_http_methods(["POST"])
def update(request, username, draft_slug):
    draft = get_object_or_404(DraftCodelist, owner=username, slug=draft_slug)
    updates = json.loads(request.body)["updates"]
    actions.update_code_statuses(draft=draft, updates=updates)
    return JsonResponse({"updates": updates})


@login_required
@require_http_methods(["POST"])
def new_search(request, username, draft_slug):
    draft = get_object_or_404(DraftCodelist, owner=username, slug=draft_slug)
    term = request.POST["term"]
    codes = do_search(draft.coding_system, term)["all_codes"]
    if not codes:
        # TODO message about no hits
        return redirect(draft)

    search = actions.create_search(draft=draft, term=term, codes=codes)
    return redirect(search)
