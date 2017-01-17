from .models import Slot


def slots(request):
    """
    Get the available slots for this url.

    This should return a dictionary with slot names as keys, and corresponding
    pk of a slot object for each slot to be filled. As lightweight as possible.
    """

    # TODO: caching
    # TODO: Generalize to use urlconf regexes as well.
    url = request.path_info
    url_parts = [part for part in url.split("/") if part]
    reconstructed_url = "/"

    # Traverse down the url 'folder' structure, collecting slots
    url_slots = list(Slot.objects.filter(url="/"))
    for part in url_parts:
        reconstructed_url += "%s/" % part
        url_slots.extend(list(Slot.objects.filter(url=reconstructed_url)))

    # Last slot (most specific url) in the url_slots list wins.
    slots = {}
    for slot in url_slots:
        slots[slot.slot_name] = slot

    return {"composer_slots": slots}
