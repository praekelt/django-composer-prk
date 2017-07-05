from BeautifulSoup import BeautifulSoup

from django import template
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import NoReverseMatch, resolve, reverse
from django.db import models
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.template.response import TemplateResponse
from django.utils.text import mark_safe

from composer.models import Row


register = template.Library()


@register.tag
def composer(parser, token):
    try:
        tag_name, slot_name = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "composer tag requires argument slot_name"
        )
    return ComposerNode(slot_name)


class ComposerNode(template.Node):

    def __init__(self, slot_name):
        self.slot_name = slot_name

    def render(self, context):
        request = context["request"]

        # Recursion guard flag. Set by TileNode.
        if hasattr(request, "_composer_suppress_rows_tag"):
            return ""

        # Return nothing if the context processor is not installed
        if "composer_slots" not in context:
            return ""

        # Return nothing if the slot does not exist
        if self.slot_name not in context["composer_slots"]:
            return ""

        slot = context["composer_slots"][self.slot_name]
        rows = slot.rows
        if rows:
            # We have customized rows for the block. Use them.
            return render_to_string(
                "composer/inclusion_tags/composer.html",
                context={"rows": rows},
                request=request
            )

        # Default rendering
        return render_to_string(
            "composer/inclusion_tags/%s.html" % self.slot_name,
            context={"object": slot},
            request=request
        )


@register.tag
def tile(parser, token):
    try:
        tag_name, tile = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "tile tag requires argument tile"
        )
    return TileNode(tile)


class TileNode(template.Node):

    def __init__(self, tile):
        self.tile = template.Variable(tile)

    def _render_url(self, context, tile, url):
        """Helper method that safely renders a view looked up from a URL."""

        request = context["request"]

        # Resolve view name to a function or object xxx: this is slow
        # because there is no way to get the view function / object
        # directly from the view name - you have to pass through the url.
        # But since the result is consistent while the Django process is
        # running it is a good candidate for caching.
        view, args, kwargs = resolve(url)

        # Construct a final kwargs that includes the context
        final_kwargs = context.flatten()
        del final_kwargs["request"]
        final_kwargs.update(kwargs)
        final_kwargs["tile"] = tile

        # Set recursion guard flag
        setattr(request, "_composer_suppress_rows_tag", 1)
        html = ""

        # Call the view. Let any error propagate.
        result = view(request, *args, **final_kwargs)
        if isinstance(result, TemplateResponse):
            # The result of a class based view
            result.render()
            html = result.rendered_content
        elif isinstance(result, HttpResponse):
            # Old-school view
            html = result.content

        # Clear flag
        delattr(request, "_composer_suppress_rows_tag")

        # Extract content div if any. This is typically needed for views
        # that extend base.html, but we are only interested in the actual
        # view content.
        soup = BeautifulSoup(html)
        content = soup.find("div", id="content")
        if content:
            return content.renderContents()

        # No content div found
        return html

    def render(self, context):
        tile = self.tile.resolve(context)
        request = context["request"]

        if tile.view_name:
            try:
                url = reverse(tile.view_name)
            except NoReverseMatch:
                return "No reverse match for %s" % tile.view_name
            content = self._render_url(context, tile, url)
            with context.push():
                context["object"] = None
                context["content"] = content
                try:
                    return render_to_string(
                        "composer/inclusion_tags/%s.html" % tile.style or "tile",
                        context.flatten()
                    )
                except template.TemplateDoesNotExist:
                    return content

        if tile.target:
            with context.push():
                obj = tile.target
                context["object"] = obj

                # Template names follow typical Django naming convention, but
                # also traverse upwards over inheritance hierarchy.
                template_names = []
                ct = ContentType.objects.get_for_model(obj._meta.model)
                kls = obj._meta.model
                while ct.model != "model":
                    template_names.extend((
                        "%s/inclusion_tags/%s_%s.html" % \
                            (ct.app_label, ct.model, tile.style or "tile"),
                        "%s/inclusion_tags/%s.html" % \
                            (ct.app_label, tile.style or "tile"),
                    ))
                    kls = kls.__bases__[0]
                    if kls == models.Model:
                        break
                    ct = ContentType.objects.get_for_model(kls)

                for template_name in template_names:
                    try:
                        return render_to_string(template_name, context.flatten())
                    except template.TemplateDoesNotExist:
                        pass

                # We couldn't find a suitable template. Attempt get_absolute_url.
                url = getattr(tile.target, "get_absolute_url", lambda: None)()
                if url:
                    content = self._render_url(context, tile, url)
                    context["object"] = None
                    context["content"] = content
                    try:
                        return render_to_string(
                            "composer/inclusion_tags/%s.html" % tile.style or "tile",
                            context.flatten()
                        )
                    except template.TemplateDoesNotExist:
                        return content

        if tile.content:
            with context.push():
                context["object"] = None
                context["content"] = tile.content
                try:
                    return render_to_string(
                        "composer/inclusion_tags/%s.html" % tile.style or "tile",
                        context.flatten()
                    )
                except template.TemplateDoesNotExist:
                    return tile.content

        return "The tile id=%s could not be rendered" % tile.id
