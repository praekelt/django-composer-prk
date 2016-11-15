from .models import Slot


def slots(request):
    """
    Get the available slots for this url.

    This should return a dictionary with slot names as keys, and corresponding
    pk of a slot object for each slot to be filled. As lightweight as possible.
    """

    # TODO: caching
    # TODO: Generalize to containing paths and/or urlconf regexes.
    url = request.path_info
    # TODO: This can be recursively rolled up to the root url
    url_slots = list(Slot.objects.filter(url=url))
    # TODO: This can be cached separately, since it's the same for all urls.
    base_slots = list(Slot.objects.filter(url="/"))

    base_slots.extend(url_slots)
    slots = {}
    for slot in base_slots:
        slots[slot.slot_name] = slot

    return {"composer_slots": slots}
