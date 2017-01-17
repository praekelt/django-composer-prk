from django import forms
from django.contrib import admin
from django.template import loader

import nested_admin

from .models import Column, Row, Slot, Tile
from .templatetags.composer_tags import ComposerNode


class TileInline(nested_admin.NestedTabularInline):
    model = Tile
    sortable_field_name = "position"
    extra = 0


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
        """
        Manipulate the form to provide a choice field for the slot name. We
        need to get the field choices from the base template. Doing this in the
        model init is wasteful, as we only need this when doing an admin edit.
        Also, it leads to circular imports.
        An alternative could be to use the django.utils function lazy.
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
                choices=slot_name_choices)

        # Find a sensible initial value. Prefer "content"
        # If instance is in kwargs, we already have a choice, so ignore.
        if "instance" not in kwargs and slot_name_choices:
            initial = slot_name_choices[0][0]
            for i,j in slot_name_choices:
                if i == "content":
                    initial = i

            self.initial["slot_name"] = initial


class SlotAdmin(nested_admin.NestedModelAdmin):
    inlines = [RowInline]
    form = SlotAdminForm


admin.site.register(Slot, SlotAdmin)
