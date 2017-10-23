from django.shortcuts import get_object_or_404
from django.views.generic.detail import DetailView

from composer.models import Slot


class SlotView(DetailView):
    """The slot detail view is only applicable to slots with slot_name
    "content".
    """

    model = Slot

    def dispatch(self, request, *args, **kwargs):
        # Always return the get method's response, except if this view manages
        # to trigger the method not allowed code path.
        handler = super(SlotView, self).dispatch(request, *args, **kwargs)

        # The method not allowed path will come back with a 405 "Method Not
        # Allowed" status. This is checked for and should proceed as default
        # implementation dictates.
        if handler.status_code != 405:
            return self.get(request, *args, **kwargs)
        else:
            return handler

    def get_object(self):
        # Return the slot based on the path
        url = self.request.path_info
        return get_object_or_404(
            Slot.permitted,
            url=self.request.path_info,
            slot_name="content"
        )
