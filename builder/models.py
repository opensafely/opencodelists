from django.db import models
from django.urls import reverse
from django.utils.functional import cached_property

from codelists.coding_systems import CODING_SYSTEMS
from opencodelists.hash_utils import hash
from opencodelists.models import User


class DraftCodelist(models.Model):
    CODING_SYSTEMS_CHOICES = [
        ("snomedct", CODING_SYSTEMS["snomedct"].name),
        ("ctv3", CODING_SYSTEMS["ctv3"].name),
        ("bnf", CODING_SYSTEMS["bnf"].name),
    ]

    owner = models.ForeignKey(User, related_name="drafts", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField()
    coding_system_id = models.CharField(
        choices=CODING_SYSTEMS_CHOICES, max_length=32, verbose_name="Coding system"
    )
    codelist = models.ForeignKey(
        "codelists.Codelist", related_name="drafts", on_delete=models.CASCADE, null=True
    )

    class Meta:
        unique_together = ("owner", "slug")

    def __str__(self):
        return self.name

    @cached_property
    def coding_system(self):
        return CODING_SYSTEMS[self.coding_system_id]

    @property
    def hash(self):
        return hash(self.id, "DraftCodelist")

    def get_absolute_url(self):
        return reverse("builder:draft", args=[self.hash])

    def get_search_url(self, search_term):
        return reverse("builder:search", args=[self.hash, search_term])

    def get_no_search_url(self):
        return reverse("builder:no_search_term", args=[self.hash])

    def get_update_url(self):
        return reverse("builder:update", args=[self.hash])

    def get_new_search_url(self):
        return reverse("builder:new_search", args=[self.hash])

    def get_download_url(self):
        return reverse("builder:download", args=[self.hash])

    def get_download_dmd_url(self):
        if self.coding_system_id == "bnf":
            return reverse("builder:download_dmd", args=[self.hash])


class CodeObj(models.Model):
    draft = models.ForeignKey(
        "DraftCodelist", related_name="code_objs", on_delete=models.CASCADE
    )
    code = models.CharField(max_length=18)
    status = models.CharField(max_length=3, default="?")

    class Meta:
        unique_together = ("draft", "code")
        constraints = [
            models.CheckConstraint(
                name="%(app_label)s_%(class)s_status_valid",
                check=models.Q(
                    status__in=[
                        "?",  # Undecided
                        "!",  # In conflict
                        "+",  # Included with descendants
                        "(+)",  # Included by ancestor
                        "-",  # Included with descendants
                        "(-)",  # Excluded by ancestor
                    ]
                ),
            )
        ]


class Search(models.Model):
    draft = models.ForeignKey(
        "DraftCodelist", related_name="searches", on_delete=models.CASCADE
    )
    term = models.CharField(max_length=255)
    slug = models.SlugField()

    class Meta:
        unique_together = ("draft", "slug")

    def get_absolute_url(self):
        return self.draft.get_search_url(self.slug)


class SearchResult(models.Model):
    search = models.ForeignKey(
        "Search", related_name="results", on_delete=models.CASCADE
    )
    code_obj = models.ForeignKey(
        "CodeObj", related_name="results", on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("search", "code_obj")
