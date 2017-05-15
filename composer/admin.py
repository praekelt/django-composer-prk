import os
import re

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib import admin
from django.template import loader
from django.template.loaders import app_directories

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
        styles = self.get_existing_styles(styles)
        styles.sort()
        self.fields["style"].widget = forms.widgets.Select(choices=styles)

    def get_existing_styles(self, current_styles):
        """return list(tuple("key", "val"), ...)
        self -- current inline form instance.
        current_styles -- styles that are already present by default or
        obtained from other settings.

        If the settings are not present, it will return the list of already set
        styles, by default consisting only of [("tile", "Tile")].
        """
        try:
            setting = settings.COMPOSER
        except AttributeError:
            return current_styles

        if not setting.get("load-existing-styles"):
            return current_styles

        # Get a list of all the availible templates in the project.
        styles_settings = setting["load-existing-styles"]
        greedy = styles_settings.get("greedy", False)
        excludes = styles_settings.get("excludes")
        includes = styles_settings.get("includes")

        # If for some reason none of the actual values are supplied return an
        # empty list.
        if not greedy and (excludes is None) and (includes is None):
            return []

        # Get the app template directories and installed apps.
        template_dirs = app_directories.get_app_template_dirs("templates")
        installed_apps = apps.app_configs.keys()

        # Traverse all the directories within the template directories for all
        # available apps.
        template_dict = {}
        for app_dir in template_dirs:
            for path, dirnames, filenames in os.walk(app_dir):

                # Composer template tags expect the templates to live within
                # the app inclusion tags, so a good area to start ignoring any
                # templates that won't match.
                if filenames and "inclusion_tags" in path:
                    split = path.split("/")

                    # Ensures inclusion_tags is the current directory we are in.
                    if not split[len(split)-1] == "inclusion_tags":
                        continue

                    # We already made sure inclusion_tags is in the path, so
                    # safe assumption is app_label should prefix it. In the
                    # event this is not a valid app name, these files will
                    # merely get ignored.
                    app_label = split[len(split)-2]
                    for filename in filenames:

                        # The naming convention that the composer tags expect
                        # is modelname_style.html. If the template name has no
                        # underscores it won't ever be valid.
                        if len(filename.split("_")) > 1:
                            data = {
                                "path": os.path.join(path, filename),
                                "filename": filename
                            }

                            # There will more than likely be multiple templates
                            # with the same base key, so we add them to a list
                            # for iteration later on.
                            if template_dict.get(app_label, None) is None:
                                template_dict[app_label] = []
                            template_dict[app_label].append(data)

        # We compare against the actual installed apps and their models to try
        # and get rid of false positives.
        styles_dict = {}
        for model in apps.get_models():
            model_name = model._meta.model_name
            app_label = model._meta.app_label
            template_data = template_dict.get(app_label, None)
            if template_data is not None:

                if not greedy:
                    if excludes:
                        to_exclude = excludes.get(app_label, [])
                        if to_exclude == "__all__" or model_name in to_exclude:
                            continue
                    if includes:
                        to_include = includes.get(app_label, [])
                        if to_include != "__all__" and model_name not in to_include:
                            continue

                # Pattern to replace the modelname as well as the file
                # extension later on.
                pattern = re.compile((r"%s_|\.html" % (model_name)))

                for template in template_data:
                    filename = template["filename"]
                    path = template["path"]

                    # Further exclusions based on the composer template tag's
                    # expectations.
                    # <app_label>/inclusion_tags/<model_name>_<style>
                    if "%s/inclusion_tags/%s_" % (app_label, model_name) in path:

                        # Remove the file extension and model name to get only
                        # the style.
                        style = pattern.sub("", filename)

                        # We add the styles to a dictionary, so we can easily
                        # make sure we don't have duplicate styles and convert
                        # it to a list of tuples.
                        if style not in styles_dict.keys():

                            # Try to make the values we display a bit more
                            # admin friendly.
                            styles_dict[style] = style.capitalize().replace(
                                "_", " "
                            )

        # Return the list of tuples containing the found styles.
        new_styles = [(k, v) for k, v in styles_dict.iteritems()]

        # Make use of the built in set to remove exact duplicates then
        # parse back into a list of tuples.
        new_styles = set(current_styles + new_styles)
        return list(new_styles)


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
