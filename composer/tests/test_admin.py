from django.test import TestCase, override_settings

from composer import admin

class TestTileAdminForm(TestCase):

    @override_settings(COMPOSER={"load_existing_styles": {"includes": {"tests": "__all__"}}})
    def test_existing_styles(self):
        choices = admin.TileInlineForm().fields["style"].widget.choices
        expected_choices = [("tile", "Tile"), ("extra_style", "Extra style"),]
        self.assertEqual(choices, expected_choices)
