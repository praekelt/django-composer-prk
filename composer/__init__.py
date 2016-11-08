from django.conf import settings


SETTINGS = {
        "layout_cache_time": 60,
        }
try:
    SETTINGS.update(settings.COMPOSER)
except AttributeError:
    # Use as is
    pass
