from django.db import models
from django.contrib.sites.shortcuts import get_current_site

try:
    from jmbo.managers import DefaultManager
    from jmbo.managers import PermittedManager as JmboPermittedManager
    has_jmbo = True
except ImportError:
    from django.db.models import Manager as DefaultManager
    has_jmbo = False

try:
    from crum import get_current_request
    has_crum = True
except ImportError:
    has_crum = False


class ComposerPermittedManager(models.Manager):
    """Get site from request if available, otherwise default."""

    def get_queryset(self):
        queryset = super(ComposerPermittedManager, self).get_queryset()

        if has_crum:
            site = get_current_site(get_current_request())
        else:
            site = get_current_site()
        queryset = queryset.filter(sites__id__exact=site.id)

        return queryset

if has_jmbo:
    PermittedManager = JmboPermittedManager
else:
    PermittedManager = ComposerPermittedManager
