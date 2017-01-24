from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import get_script_prefix
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from composer.managers import DefaultManager, PermittedManager


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
        default="/",
        db_index=True,
        help_text=_("Where on the site this slot will appear. Start and end \
with a slash. Example: '/about-us/people/'"),
    )
    # TODO: Add option to also render on all urls below this one. For now,
    # that defaults to True.
    # TODO: Add field with options to pick from a range of urlconf regexes.
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

    objects = DefaultManager()
    permitted = PermittedManager()

    def __unicode__(self):
        # Use same pattern as flatpages
        return "%s -- %s" % (self.url, self.title)

    def get_absolute_url(self):
        # Taken from flatpages
        # Handle script prefix manually because we bypass reverse()
        return iri_to_uri(get_script_prefix().rstrip("/") + self.url)

    @property
    def rows(self):
        """Fetch rows, columns and tiles in a single query
        """

        # Organize into a structure
        tiles = Tile.objects.select_related().filter(
            column__row__slot=self
        ).order_by("position")
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

    @property
    def rows_admin(self):
        return self.row_set.all().order_by("position")

    @property
    def rows_by_block_name(self):
        """Return rows grouped by block_name."""
        result = {}
        for row in self.rows:
            result.setdefault(row.block_name, [])
            result[row.block_name].append(row)
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
        tiles = Tile.objects.select_related().filter(
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


class Tile(models.Model):
    """
    A block tile that can hold a listing or content item.
    """
    column = models.ForeignKey(Column)

    position = models.PositiveIntegerField(default=0)

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

    view_name = models.CharField(
        max_length=200,
        help_text="""A view to be rendered in this tile. This view is \
typically a snippet of a larger page. If you are unsure test and see if \
it works - you cannot break anything.""",
        null=True,
        blank=True
    )

    style = models.CharField(
        max_length=200,
        help_text="Display style. This corresponds to a listing or object \
style template.",
        null=True,
        blank=True,
    )

    class_name = models.CharField(
        max_length=200,
        help_text="One or more CSS classes that are applied to the tile.",
        null=True,
        blank=True,
    )

    @property
    def label(self):
        return str(self.target or self.view_name)
