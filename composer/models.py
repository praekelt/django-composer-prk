import cPickle
import inspect
import re

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.translation import ugettext_lazy as _

from jmbo.managers import DefaultManager, PermittedManager

# TODO: Make sure page is unique per url and site
from composer import SETTINGS as app_settings

class AttributeWrapper:
    """
    Wrapper that allows attributes to be added or overridden on an object.

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
        """
        Can't override __class__ and making it a property also does not work.
        Could be because of Django metaclasses.
        """
        return self._obj.__class__


class Page(models.Model):
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
        help_text="Sites that this page will appear on.",
        null=True,
        blank=True,
    )

    objects = DefaultManager()
    permitted = PermittedManager()

    def __unicode__(self):
        if self.subtitle:
            return "%s (%s)" % (self.title, self.subtitle)
        else:
            return self.title

    @property
    def rows(self):
        """
        Fetch rows, columns and tiles in a single query
        """

        key = "composer-page-rows-%s" % self.id
        cached = cache.get(key, None)
        if cached:
            return cPickle.loads(cached)

        # Organize into a structure
        tiles = Tile.objects.select_related().filter(column__row__page=self)\
                .order_by("position")
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

        cache.set(key, cPickle.dumps(result),app_settings["layout_cache_time"]

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


class PageView(models.Model):
    """
    We need this bridging class for fast lookups
    """
    page = models.ForeignKey(Page)

    view_name = models.CharField(
        max_length=200,
        help_text="A view that uses the target page to render itself.",
    )

    def __unicode__(self):
        return "%s > %s" % (self.page.title, self.view_name)


class Row(models.Model):
    page = models.ForeignKey(Page)
    position = models.PositiveIntegerField(default=0, editable=False)
    block_name = models.CharField(
        max_length=32,
        default="content",
        choices=(
            ("header", _("Header")),
            ("content", _("Content")),
            ("footer", _("Footer")),
        ),
        help_text="The Django base template block that this row is rendered \
            within. It is only applicable if the page is set to be the home \
            page."
    )
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

    position = models.PositiveIntegerField(
        default=0,
        editable=False,
    )

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

    designation = models.CharField(
        max_length=32,
        help_text="Applicable to content (green) rows. Used to display \
                columns to the left and right of the content block.",
        choices=(
            ("left", _("Left")),
            ("right", _("Right")),
        ),
        default="",
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

    position = models.PositiveIntegerField(
        default=0,
        editable=False,
    )

    target_content_type = models.ForeignKey(
        ContentType,
        related_name="tile_target_content_type",
        null=True,
    )

    target_object_id = models.PositiveIntegerField(
        null=True,
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
        blank=True,
    )

    class_name = models.CharField(
        max_length=200,
        help_text="One or more CSS classes that are applied to the tile.",
        null=True,
        blank=True,
    )

    enable_ajax = models.BooleanField(default=False)

    condition_expression = models.CharField(
        max_length=255,
        help_text="A python expression. Variable request is in scope.",
        null=True,
        blank=True,
    )

    @property
    def label(self):
        return str(self.target or self.view_name)

    def condition_expression_result(self, request):
        if not self.condition_expression:
            return True
        try:
            return eval(self.condition_expression)
        except:
            return False
