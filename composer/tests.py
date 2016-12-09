from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase
from listing.models import Listing
from post.models import Post

from .composer.models import Slot

test_post_data = [{
        "model": "post.Post",
        "pk": 10,
        "title": "Test Post",
        "markdown": "Test Post markdown stuff",
        "state": "published",
        }]

header_footer_posts = [
        {
            "model": "post.Post",
            "pk": 20,
            "title": "Header Post",
            "markdown": "Header Post markdown stuff",
            "state": "published",
            },
        {
            "model": "post.Post",
            "pk": 30,
            "title": "Footer Post",
            "markdown": "Footer Post markdown stuff",
            "state": "published",
            },
        ]

listings = [
        {
            "model": "listing.Listing",
            "pk": 110,
            "title": "Test Listing 1",
            "slug": "test_listing_1",
            "style": "Vertical",
            },
        {
            "model": "listing.Listing",
            "pk": 120,
            "title": "Test Listing 2",
            "slug": "test_listing_2",
            "style": "Vertical",
            },
        {
            "model": "composer.Slot",
            "pk": 3000,
            "url": "/test/",
            "slot_name": "content",
            "title": "Content Slot",
            },
        {
            "model": "composer.Row",
            "pk": 3100,
            "slot_id": 3000,
            "position": 1,
            "class_name": "row_3100",
            },
        {
            "model": "composer.Column",
            "pk": 3110,
            "title": "column 3110",
            "row_id": 3100,
            "width": 12,
            "position": 1,
            "class_name": "column_3110",
            },
        {
            "model": "composer.Tile",
            "pk": 3111,
            "column_id": 3110,
            "position": 1,
            "class_name": "tile_3111",
            "target_content_type": "listing.listing",
            "target_object_id": 110,
            },
        ]

composer_header_slots = [
        {
            "model": "navbuilder.menu",
            "pk": 50,
            "title": "Test menu",
            "slug": "test_menu",
            },
        {
            "model": "navbuilder.MenuItem",
            "pk": 51,
            "title": "Menu Item 1",
            "slug": "menu_item_1",
            "position": "1",
            "menu_id": 50,
            },
        {
            "model": "composer.Slot",
            "pk": 1000,
            "url": "/",
            "slot_name": "header",
            "title": "Homepage Header slot",
            },
        {
            "model": "composer.Row",
            "pk": 1100,
            "slot_id": 1000,
            "position": 1,
            "class_name": "row_1100",
            },
        {
            "model": "composer.Row",
            "pk": 1200,
            "slot_id": 1000,
            "position": 2,
            "class_name": "row_1200",
            },
        {
            "model": "composer.Column",
            "pk": 1110,
            "title": "column 1110",
            "row_id": 1100,
            "width": 12,
            "position": 1,
            "class_name": "column_1110",
            },
        {
            "model": "composer.Tile",
            "pk": 1111,
            "column_id": 1110,
            "position": 1,
            "class_name": "tile_1111",
            "target_content_type": "navbuilder.menu",
            "target_object_id": 50,
            },
        ]

composer_footer_slots = [
        {
            "model": "composer.Slot",
            "pk": 2000,
            "url": "/",
            "slot_name": "footer",
            "title": "Homepage Footer slot",
            },
        {
            "model": "composer.Row",
            "pk": 2100,
            "slot_id": 2000,
            "position": 1,
            "class_name": "row_2100",
            },
        {
            "model": "composer.Row",
            "pk": 2200,
            "slot_id": 2000,
            "position": 2,
            "class_name": "row_2200",
            },
        {
            "model": "composer.Column",
            "pk": 2110,
            "title": "column 2110",
            "row_id": 2100,
            "width": 12,
            "position": 1,
            "class_name": "column_2110",
            },
        {
            "model": "composer.Tile",
            "pk": 2111,
            "column_id": 2110,
            "position": 1,
            "class_name": "tile_2111",
            "target_content_type": "post.post",
            "target_object_id": 30,
            },
        ]


def create_content(data):
    """
    Basic test object creation.

    Fixtures are inflexible for testing. This allows us to create only what we
    need, with the exact properties we need.
    """
    for i in data:
        item = i.copy()
        model = apps.get_model(item["model"])
        del item["model"]

        # Special handling for the specific generic foreign key
        if "target_content_type" in item and \
                isinstance(item["target_content_type"], str):
            target_app, target_model = item["target_content_type"].split(".")
            item["target_content_type"] = ContentType.objects.get(
                    app_label=target_app, model=target_model)

        obj = model.objects.create(**item)
        obj.sites = [1]
        obj.save()

class BasicTestCase(TestCase):

    def test_default_slots(self):
        # Test that the default content slot gets filled
        # Create a post to test against.
        create_content(test_post_data)

        # All the unfilled default slots are visible on the home page.
        response = self.client.get("/")
        self.assertContains(response, "Header slot:")
        self.assertContains(response, "Content slot:")
        self.assertContains(response, "Footer slot:")

        # The test post fills the content slot, but not the other slots.
        response = self.client.get("/post/test-post/")
        self.assertContains(response, "Header slot:")
        self.assertNotContains(response, "Content slot:")
        self.assertContains(response, "Test Post markdown stuff")
        self.assertContains(response, "Footer slot:")

    def test_header_slots(self):
        # Creating a header slot should show it on all applicable pages
        create_content(composer_header_slots + test_post_data + header_footer_posts)

        # The test menu should show up in the header slot
        response = self.client.get("/")
        self.assertNotContains(response, "Header slot:")
        self.assertContains(response, "Menu Item 1")
        self.assertNotContains(response, "Test Post markdown stuff")

        # And also on the test post page
        response = self.client.get("/post/test-post/")
        self.assertNotContains(response, "Header slot:")
        self.assertContains(response, "Menu Item 1")
        self.assertContains(response, "Test Post markdown stuff")

    def test_footer_slots(self):
        # Make sure that caching does not re-render just the header slot.
        create_content(
                composer_header_slots + 
                composer_footer_slots +
                test_post_data +
                header_footer_posts)

        # The test menu post should show up in the header slot
        response = self.client.get("/")
        self.assertNotContains(response, "Footer slot:")
        self.assertContains(response, "Footer Post markdown stuff")
        self.assertNotContains(response, "Test Post markdown stuff")

        # And also on the test post page
        response = self.client.get("/post/test-post/")
        self.assertNotContains(response, "Footer slot:")
        self.assertContains(response, "Footer Post markdown stuff")
        self.assertContains(response, "Test Post markdown stuff")

    def test_listings(self):
        """
        We should be able to show listings in the content area on specific
        urls.
        """
        # Set up
        create_content(
                composer_header_slots +
                listings +
                test_post_data +
                header_footer_posts)
        Listing.objects.get(pk=110).set_content(Post.objects.all())

        # The listing should NOT show up in the homepage content slot
        response = self.client.get("/")
        self.assertNotContains(response, "Test Listing 1")

        # This URL is for the slot object.
        response = self.client.get("/test/")
        self.assertContains(response, "Test Listing 1")

    def test_404(self):
        """
        Setting a content slot on the home page could potentially override 404
        or object detail pages everywhere on the site.
        """
        # Set up
        create_content(
                composer_header_slots +
                listings +
                test_post_data +
                header_footer_posts)
        Listing.objects.get(pk=110).set_content(Post.objects.all())
        slot = Slot.objects.get(pk=3000)
        slot.url = "/"
        slot.save()

        # The listing should show up in the homepage content slot
        response = self.client.get("/")
        self.assertContains(response, "Test Listing 1")
        self.assertContains(response, "Menu Item 1")

        # but not on an object detail url
        response = self.client.get("/post/test-post/")
        self.assertNotContains(response, "Test Listing 1")
        self.assertContains(response, "Menu Item 1")

        # A nonexistent page should return 404
        response = self.client.get("/test/")
        self.assertNotContains(response, "Test Listing 1", status_code=404)
        # TODO: The 404 page should still show the header and footer slots.
        # This depends on a 404 page that extends base.html
