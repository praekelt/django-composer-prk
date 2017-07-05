import re

from composer.models import Slot


def slots(request):
    """Get the available slots for this URL and return as a mapping."""

    # todo: cache

    # Sort by slot url length reversed because we want the best regex match
    slots = list(Slot.permitted.all())
    slots.sort(lambda a, b: cmp(len(b.url), len(a.url)))

    # Assemble map with best matches
    slot_map = {}
    request_path = request.get_full_path()
    for slot in slots:
        if slot.slot_name in slot_map:
            continue
        if re.search(r"%s" % slot.url, request_path):
            slot_map[slot.slot_name] = slot

    return {"composer_slots": slot_map}
