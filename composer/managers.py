from django.db import models
from django.contrib.sites.shortcuts import get_current_site

from crum import get_current_request


class PermittedManager(models.Manager):
    """This maneger filters by site."""

    def get_queryset(self):
        queryset = super(PermittedManager, self).get_queryset()
        site = get_current_site(get_current_request())
        queryset = queryset.filter(sites__id__exact=site.id)
        return queryset
