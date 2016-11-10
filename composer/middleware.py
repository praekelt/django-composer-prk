from django.conf import settings
from django.http import Http404

from .views import PageView

if "flatpages" in settings.INSTALLED_APPS:
    from django.contrib.flatpages.views import flatpage


class ComposerFallbackMiddleware(object):
    """Combine composer page and flatpage fallbacks.
    """
    def process_response(self, request, response):
        # Composer pages and flatpages only render on 404
        if response.status_code != 404:
            return response

        try:
            return PageView.as_view()(request)
        except Http404:
            # Pass through to the flatpage fallback
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
