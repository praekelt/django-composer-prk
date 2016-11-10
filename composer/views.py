from django.http import Http404
from django.views.generic.detail import DetailView
from .models import Page
from django.shortcuts import render
from django.contrib.sites.shortcuts import get_current_site


class PageView(DetailView):
    model = Page

    def get_object(self):
        """Get the Page based on the URL"""
        url = self.request.path_info
        site_id = get_current_site(self.request).id
        # TODO: Should this be permitted instead of objects?
        page = Page.objects.filter(url=url, sites=site_id)
        if page:
            return page

        raise Http404("Page does not exist")
