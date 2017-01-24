from django.shortcuts import get_object_or_404
from django.views.generic.detail import DetailView

from composer.models import Slot


class SlotView(DetailView):
    """The slot detail view is only applicable to slots with slot_name
    "content".
    """

    model = Slot

    def get_object(self):
        # Return the slot based on the path
        url = self.request.path_info
        return get_object_or_404(
            Slot.permitted,
            url=self.request.path_info,
            slot_name="content"
        )

    def post(self, request, *args, **kwargs):
        return self.get(request, *args, **kwargs)
