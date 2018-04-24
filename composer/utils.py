from importlib import import_module


_composer_utils_cache = {}


def _build_view_names_recurse(url_patterns=None, namespace=None):
    """Returns a tuple of url pattern names suitable for use as field choices.
    """

    if url_patterns is None:
        # Must import late
        from django.conf import settings
        mod = import_module(settings.ROOT_URLCONF)
        url_patterns = mod.urlpatterns

    result = []
    for pattern in url_patterns:
        try:
            # Rules: (1) named patterns (2) may not contain arguments.
            if pattern.name is not None:
                actual_pattern = getattr(pattern, "pattern", pattern)
                if actual_pattern.regex.pattern.find("<") == -1:
                    key = ""
                    if namespace:
                        key = namespace + ":"
                    key += pattern.name
                    result.append((key, key))
        except AttributeError:
            # If the pattern itself is an include, recursively fetch its
            # patterns. Ignore admin patterns.
            actual_pattern = getattr(pattern, "pattern", pattern)
            if not actual_pattern.regex.pattern.startswith("^admin"):
                try:
                    result += _build_view_names_recurse(pattern.url_patterns, pattern.namespace)
                except AttributeError:
                    pass
    return result


def get_view_choices():
    # Implement a simple module level cache. The result never changes
    # for the duration of the Django process life.
    if "get_view_choices" not in _composer_utils_cache:
        result = _build_view_names_recurse()
        result.sort()
        _composer_utils_cache["get_view_choices"] = result
    return _composer_utils_cache["get_view_choices"]
