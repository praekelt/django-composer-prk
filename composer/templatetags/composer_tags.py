import cPickle

from BeautifulSoup import BeautifulSoup

from django import template
from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import NoReverseMatch, resolve, reverse
from django.template.loader import render_to_string
from django.template.response import TemplateResponse

# We use the special shortcut for jmbo objects
try:
    from jmbo.templatetags.jmbo_inclusion_tags import RenderObjectNode
    has_jmbo = True
except ImportError:
    has_jmbo = False

from .. import SETTINGS as app_settings
from ..models import Row

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
            return

        # Return nothing if the context processor is not installed
        if "composer_slots" not in context:
            return

        # Return nothing if the slot does not exist
        if self.slot_name not in context["composer_slots"]:
            return

        slot_id = context["composer_slots"][self.slot_name].id

        # Cache homepage rows_by_block_name
        # TODO: Is this caching needed, given ultracache?
        key = "composer-slot-%s" % slot_id
        cached = cache.get(key, None)
        if cached is None:
            rows = Row.objects.filter(slot__id=slot_id).order_by("position")
            cache.set(
                key,
                cPickle.dumps(rows),
                app_settings["layout_cache_time"]
            )
        else:
            rows = cPickle.loads(cached)

        if rows:
            # We have customized rows for the block. Use them.
            return render_to_string(
                "composer/inclusion_tags/rows.html",
                context={"rows":rows},
                request=request
            )

        # Default rendering
        return render_to_string(
            "composer/inclusion_tags/%s.html" % self.slot_name,
            context={},
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

    def render(self, context):
        tile = self.tile.resolve(context)
        request = context["request"]

        if tile.view_name:
            # Resolve view name to a function or object
            # xxx: this is slow because there is no way to get the view
            # function / object directly from the view name - you have to pass
            # through the url. But since the result is consistent while the
            # Django process is running it is a good candidate for caching.
            try:
                url = reverse(tile.view_name)
            except NoReverseMatch:
                return "No reverse match for %s" % tile.view_name
            view, args, kwargs = resolve(url)

            # Set recursion guard flag and render only content block flag
            setattr(request, "_composer_suppress_rows_tag", 1)
            setattr(request, "render_only_content_block", True)
            html = ""
            # Call the view. Let any error propagate.
            result = view(request, *args, **kwargs)
            if isinstance(result, TemplateResponse):
                # The result of a generic view
                result.render()
                html = result.rendered_content
            elif isinstance(result, HttpResponse):
                # Old-school view
                html = result.content
            # Clear flags
            # xxx: something may clear the flags. Need to investigate more
            # incase of thread safety problem.
            if hasattr(request, "_composer_suppress_rows_tag"):
                delattr(request, "_composer_suppress_rows_tag")
            if hasattr(request, "render_only_content_block"):
                delattr(request, "render_only_content_block")

            # Extract content div if any
            soup = BeautifulSoup(html)
            content = soup.find("div", id="content")
            if content:
                return content.renderContents()

            # No content div found
            return html

        if tile.target is not None:
            if has_jmbo and hasattr(tile.target, "modelbase_obj"):
                with context.push():
                    context['tile_target'] = tile.target
                    return RenderObjectNode("tile_target", "detail")\
                            .render(context)

            #Most targetable things follow a predictable pattern to get a
            #rendered inclusion tag. Construct a template snippet to render it.
            with context.push():
                context['tile_target'] = tile.target
                tag_file = "%s_tags" % tile.target.__module__.split(".")[0]
                tag_string = '%s "%s"' % (
                    tile.target.__class__.__name__.lower(),
                    tile.target.slug)
                try:
                    t = template.Template("{%% load %s %%}{%% %s %%}" % (
                        tag_file,
                        tag_string))
                    result = t.render(context)
                except template.TemplateSyntaxError:
                    print tag_file, tag_string
                    t = template.Template("{%% load %s %%}{%% render_%s %%}" % (
                        tag_file,
                        tag_string))
                    result = t.render(context)
                return t.render(context)
            return "The tile target could not be found"
        return "The tile could not be rendered"


@register.tag
def tile_url(parser, token):
    """Return the Url for a given view. Very similar to the {% url %} template
    tag, but can accept a variable as first parameter."""
    try:
        tag_name, tile = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "tile_url tag requires argument tile"
        )
    return TileUrlNode(tile)


class TileUrlNode(template.Node):
    def __init__(self, tile):
        self.tile = template.Variable(tile)

    def render(self, context):
        tile = self.tile.resolve(context)
        if tile.view_name:
            try:
                return reverse(tile.view_name)
            except NoReverseMatch:
                return ""

        if tile.target:
            # xxx: not strictly correct since target may be menu or navbar.
            # No harm done for now.
            try:
                url = reverse("listing-detail", args=[tile.target.slug])
            except NoReverseMatch:
                url = tile.target.get_absolute_url()
            return url
