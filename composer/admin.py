from django import forms
from django.conf import settings
from django.contrib import admin
from django.template import loader

import nested_admin

from composer.models import Column, Row, Slot, Tile
from composer.templatetags.composer_tags import ComposerNode
from composer.utils import get_view_choices


class TileInlineForm(forms.ModelForm):

    class Meta:
        model = Tile
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super(TileInlineForm, self).__init__(*args, **kwargs)

        self.fields["view_name"].widget = forms.widgets.Select(
            choices=[("", "")] + get_view_choices()
        )

        try:
            styles = list(settings.COMPOSER["styles"])
        except (AttributeError, KeyError):
            styles = []
        styles.append(("tile", "Tile"))
        styles.sort()
        self.fields["style"].widget = forms.widgets.Select(choices=styles)


class TileInline(nested_admin.NestedTabularInline):
    model = Tile
    sortable_field_name = "position"
    extra = 0
    form = TileInlineForm


class ColumnInline(nested_admin.NestedTabularInline):
    model = Column
    sortable_field_name = "position"
    inlines = [TileInline]
    extra = 0


class RowInline(nested_admin.NestedTabularInline):
    model = Row
    sortable_field_name = "position"
    inlines = [ColumnInline]
    extra = 0


class SlotAdminForm(forms.ModelForm):
    model = Slot

    def __init__(self, *args, **kwargs):
        """ Manipulate the form to provide a choice field for the slot name. We
        need to get the field choices from the base template. Doing this in the
        model init is wasteful, as we only need this when doing an admin edit.

        Also, it leads to circular imports.  An alternative could be to use the
        django.utils function lazy.
        """
        super(SlotAdminForm, self).__init__(*args, **kwargs)

        # Get the choices from the base template.
        nodelist = loader.get_template("base.html").template.nodelist
        composer_nodes = nodelist.get_nodes_by_type(ComposerNode)
        slot_name_choices = [[i.slot_name, i.slot_name]
                for i in composer_nodes]

        # The help text on the widget needs to be carried over.
        slot_name_help = self.fields["slot_name"].help_text

        # Set the choices and initial value
        self.fields["slot_name"] = forms.ChoiceField(
            help_text=slot_name_help,
            label="Slot Position",
            choices=slot_name_choices
        )

        # Find a sensible initial value. Prefer "content". If instance is in
        # kwargs, we already have a choice, so ignore.
        if "instance" not in kwargs and slot_name_choices:
            initial = slot_name_choices[0][0]
            for i, j in slot_name_choices:
                if i == "content":
                    initial = i

            self.initial["slot_name"] = initial


class SlotAdmin(nested_admin.NestedModelAdmin):
    inlines = [RowInline]
    form = SlotAdminForm
    search_fields = [
        "title", "url"
    ]
    list_filter = [
        "slot_name"
    ]
    ordering = ["url"]


class TileAdmin(admin.ModelAdmin):
    list_display = ("_label", "_slot", "_slot_url")
    search_fields = [
        "column__row__slot__url", "column__row__slot__title"
    ]
    list_filter = [
        "column__row__slot__slot_name"
    ]
    ordering = ["column__row__slot__url"]

    def _label(self, obj):
        return obj.label

    def _slot(self, obj):
        return obj.column.row.slot.title

    def _slot_url(self, obj):
        return obj.column.row.slot.url


admin.site.register(Slot, SlotAdmin)
admin.site.register(Tile, TileAdmin)
