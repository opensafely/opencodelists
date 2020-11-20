from functools import wraps

from django.shortcuts import get_object_or_404

from .models import DraftCodelist


def load_draft(view_fn):
    @wraps(view_fn)
    def wrapped_view(request, username, draft_slug, **kwargs):
        draft = get_object_or_404(DraftCodelist, owner=username, slug=draft_slug)
        return view_fn(request, draft, **kwargs)

    return wrapped_view
