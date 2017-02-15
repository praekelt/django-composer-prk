from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.test import TestCase

from composer.models import Slot, Row, Column, Tile


class MiddleWareTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        super(MiddleWareTestCase, cls).setUpTestData()
        cls.slot = Slot.objects.create(slot_name="content", url="/four-o-four/")
        cls.slot.sites = Site.objects.all()
        cls.slot.save()
        cls.tile = Tile.objects.create(
            column=Column.objects.create(row=Row.objects.create(slot=cls.slot))
        )
        # Abuse the header view for this test
        cls.tile.view_name = "header"
        cls.tile.save()

    def test_404(self):
        response = self.client.get("/four-o-four/")
        self.assertHTMLEqual("""
        <div id="header">
            Header slot
        </div>
        <div id="content">
            <div class="composer-row None">
                <div class="composer-column composer-column-8 None">
                    <div class="composer-tile None" data-oid="%s">
                        I am the header
                    </div>
                </div>
            </div>
        </div>
        <div id="footer">
            Footer slot
        </div>""" % self.tile.id, response.content)

    def test_404_no_slash(self):
        response = self.client.get("/four-o-four")
        self.assertRedirects(
            response,
            "/four-o-four/",
            status_code=301,
            target_status_code=200,
            fetch_redirect_response=True
        )

    def test_404_no_slash_no_redirect(self):
        with self.settings(APPEND_SLASH=False):
            response = self.client.get("/four-o-four")
            self.assertEqual(response.status_code, 404)
