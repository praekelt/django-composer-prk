from django.contrib.sites.shortcuts import get_current_site
from django.http import Http404
from django.shortcuts import render
from django.views.generic.detail import DetailView

from .models import Slot


class SlotView(DetailView):
    model = Slot

    def get_object(self):
        """Get the Slot based on the URL"""
        url = self.request.path_info
        site_id = get_current_site(self.request).id
        # TODO: Should this be permitted instead of objects?
        page = Slot.objects.filter(url=url, sites=site_id, slot_name="content")
        if page:
            return page

        raise Http404("Slot does not exist")
