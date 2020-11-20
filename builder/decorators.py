from functools import wraps

from django.shortcuts import get_object_or_404, redirect

from opencodelists.hash_utils import unhash

from .models import DraftCodelist


def load_draft(view_fn):
    """Load a DraftCodelist (or raise 404) and either pass it to view function, or
    redirect to canonical URL.
    """

    @wraps(view_fn)
    def wrapped_view(request, hash=None, username=None, draft_slug=None, **kwargs):
        if hash:
            assert username is None and draft_slug is None
            id = unhash(hash, "DraftCodelist")
            draft = get_object_or_404(DraftCodelist, id=id)
            return view_fn(request, draft, **kwargs)
        else:
            draft = get_object_or_404(DraftCodelist, owner=username, slug=draft_slug)
            return redirect("builder:" + view_fn.__name__, hash=draft.hash, **kwargs)

    return wrapped_view
