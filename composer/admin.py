from django.contrib import admin
import nested_admin

from .models import Slot, Row, Column, Tile


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


class SlotAdmin(nested_admin.NestedModelAdmin):
    inlines = [RowInline]


admin.site.register(Slot, SlotAdmin)
