import markdown

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import get_script_prefix
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.functional import cached_property
from django.utils.text import mark_safe
from django.utils.translation import ugettext_lazy as _

from simplemde.fields import SimpleMDEField

from composer.managers import PermittedManager


# TODO: Make sure slot is unique per url and site

class AttributeWrapper:
    """Wrapper that allows attributes to be added or overridden on an object.
    Copied from jmbo-foundry.
    """

    def __init__(self, obj, **kwargs):
        self._obj = obj
        self._attributes = {}
        for k, v in kwargs.items():
            self._attributes[k] = v

    def __getattr__(self, key):
        if key in self._attributes:
            return self._attributes[key]
        return getattr(self._obj, key)

    def __setstate__(self, dict):
        self.__dict__.update(dict)

    @property
    def klass(self):
        """Can't override __class__ and making it a property also does not
        work. Could be because of Django metaclasses.
        """
        return self._obj.__class__


class Slot(models.Model):
    url = models.CharField(
        _("URL"),
        max_length=100,
        default="^/$",
        db_index=True,
        help_text=_("""Where on the site this slot will appear. This value
may be a regular expression and may be very complex. A simple example is
^/about-us/, which means any URL starting with /about-us/ will have this slot."""
        ),
    )
    slot_name = models.CharField(
        max_length=32,
        help_text="Which base template slot should this be rendered in?"
    )
    title = models.CharField(
        max_length=200,
        help_text="A title that may appear in the browser window caption.",
    )
    description = models.TextField(
        help_text=_("A short description. More verbose than the title but \
limited to one or two sentences."),
        null=True,
        blank=True,
    )
    sites = models.ManyToManyField(
        "sites.Site",
        help_text="Sites that this slot will appear on.",
        blank=True,
    )

    objects = models.Manager()
    permitted = PermittedManager()

    def __unicode__(self):
        # Use same pattern as flatpages
        return "%s -- %s" % (self.url, self.title)

    def get_absolute_url(self):
        # Taken from flatpages. Handle script prefix manually because we
        # bypass reverse().
        return iri_to_uri(get_script_prefix().rstrip("/") + self.url)

    @property
    def rows(self):
        """Fetch rows, columns and tiles in a single query
        """

        # Organize into a structure
        tiles = []
        for tile in Tile.objects.select_related("column__row").filter(
            column__row__slot=self
        ).order_by("position"):
            tiles.append(AttributeWrapper(tile, target=None))

        # The most difficult part is to fetch the generic foreign keys in the
        # least amount of queries.

        # Key is content type id, value is target id
        map_ct_targets = {}

        # Key one is content type id, key two is target id, value is a list of
        # tiles.
        map_two_deep = {}

        # Populate the dictionaries
        for tile in tiles:
            ct_id = tile.target_content_type_id
            if not ct_id:
                continue
            target_id = tile.target_object_id

            # map_ct_targets
            if ct_id not in map_ct_targets:
                map_ct_targets[ct_id] = []
            map_ct_targets[ct_id].append(target_id)

            # map_two_deep
            if ct_id not in map_two_deep:
                map_two_deep[ct_id] = {}
            if target_id not in map_two_deep[ct_id]:
                map_two_deep[ct_id][target_id] = []
            map_two_deep[ct_id][target_id].append(tile)

        # Pre-lookup the content types
        content_types = {}
        for ct in ContentType.objects.filter(id__in=map_ct_targets.keys()):
            content_types[ct.id] = ct

        # Set the target objects on the tiles
        for ct_id, ids in map_ct_targets.items():
            for obj in content_types[ct_id].model_class().objects.filter(id__in=ids):
                for tile in map_two_deep[ct_id][obj.id]:
                    tile._attributes["target"] = obj

        # Build the structure
        struct = {}
        for tile in tiles:
            row = tile.column.row
            if row not in struct:
                struct.setdefault(row, {})
            column = tile.column
            if column not in struct[row]:
                struct[row].setdefault(column, [])
            struct[row][column].append(tile)

        # Sort rows and columns in the structure
        result = []
        keys_row = struct.keys()
        keys_row.sort(lambda a, b: cmp(a.position, b.position))
        for row in keys_row:
            keys_column = struct[row].keys()
            keys_column.sort(lambda a, b: cmp(a.position, b.position))
            column_objs = []
            for column in keys_column:
                column_objs.append(AttributeWrapper(
                    column, tiles=struct[row][column]))
            result.append(AttributeWrapper(row, columns=column_objs))

        return result


class Row(models.Model):
    slot = models.ForeignKey(Slot)
    position = models.PositiveIntegerField(default=0)
    class_name = models.CharField(
        max_length=200,
        help_text="One or more CSS classes that are applied to the row.",
        null=True,
        blank=True,
    )

    @property
    def columns(self):
        """Fetch columns and tiles in a single query"""

        # Organize into a structure
        struct = {}
        tiles = Tile.objects.select_related("column").filter(
                column__row=self).order_by("position")
        for tile in tiles:
            column = tile.column
            if column not in struct:
                struct.setdefault(column, [])
            struct[column].append(tile)

        # Sort columns in the structure
        result = []
        keys_column = struct.keys()
        keys_column.sort(lambda a, b: cmp(a.position, b.position))
        for column in keys_column:
            result.append(AttributeWrapper(column, tiles=struct[column]))

        return result

    class Meta:
        ordering = ['position']


class Column(models.Model):
    row = models.ForeignKey(Row)
    position = models.PositiveIntegerField(default=0)
    width = models.PositiveIntegerField(
        default=8,
        validators = [
            MaxValueValidator(12),
            MinValueValidator(1),
        ]
    )
    title = models.CharField(
        max_length=256,
        help_text="The title is rendered at the top of a column.",
        null=True,
        blank=True,
    )
    class_name = models.CharField(
        max_length=200,
        help_text="One or more CSS classes that are applied to the column.",
        null=True,
        blank=True,
    )

    @property
    def tiles(self):
        return self.tile_set.all().order_by("position")

    class Meta:
        ordering = ['position']


class Tile(models.Model):
    """A block tile that renders a view or an object.
    """

    column = models.ForeignKey(Column)
    position = models.PositiveIntegerField(default=0)
    view_name = models.CharField(
        max_length=200,
        help_text="""A view to be rendered in this tile. This view is \
typically a snippet of a larger page. If you are unsure test and see if \
it works. If this value is set it has precedence over target.""",
        null=True,
        blank=True
    )
    target_content_type = models.ForeignKey(
        ContentType,
        related_name="tile_target_content_type",
        null=True,
        blank=True,
    )
    target_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
    )
    target = GenericForeignKey(
        "target_content_type",
        "target_object_id",
    )
    markdown = SimpleMDEField(null=True, blank=True)
    style = models.CharField(
        max_length=200,
        default="tile",
        help_text="""The style of template that is used to render the item \
inside the tile if target is set.""",
        null=True,
        blank=True
    )
    class_name = models.CharField(
        max_length=200,
        help_text="One or more CSS classes that are applied to the tile.",
        null=True,
        blank=True,
    )

    @property
    def label(self):
        # Dangling targets pose a problem
        try:
            target = self.target
        except AttributeError:
            target = "Target has been deleted"
        return unicode(self.view_name or target or self.markdown[:100])

    @cached_property
    def content(self):
        if not self.markdown:
            return ""
        return mark_safe(markdown.markdown(self.markdown))

    class Meta:
        ordering = ['position']
