from django.conf import settings
from django.http import Http404, HttpResponsePermanentRedirect
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse

from composer.models import Slot
from composer.views import SlotView


if "flatpages" in settings.INSTALLED_APPS:
    from django.contrib.flatpages.views import flatpage


class ComposerFallbackMiddleware(object):
    """Combine composer slot and flatpage fallbacks.
    """

    def process_response(self, request, response):
        # Composer pages and flatpages only render on 404
        if response.status_code != 404:
            return response

        try:
            response = SlotView.as_view()(request)
            if isinstance(response, TemplateResponse):
                return response.render()
            else:
                return response
        except Http404:
            # Try the url with a slash appended.
            url = request.path_info
            if not url.endswith("/") and settings.APPEND_SLASH:
                url += "/"
                try:
                    f = get_object_or_404(
                        Slot.permitted,
                        url=url,
                        slot_name="content"
                    )
                    return HttpResponsePermanentRedirect("%s/" % request.path)
                except Http404:
                    # No slot with slash appended. Fall through.
                    pass
            else:
                # Settings say do not append a slash.
                pass

        # Both "pass" conditions above means we did not find a suitable slot.
        if "flatpages" not in settings.INSTALLED_APPS:
            return response

        try:
            return flatpage(request, request.path_info)
        # Return the original response if any errors happened. Because this
        # is a middleware, we can't assume the errors will be caught elsewhere.
        except Http404:
            return response
        except Exception:
            if settings.DEBUG:
                raise
            return response
