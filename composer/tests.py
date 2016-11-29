from django.test import TestCase
from django.apps import apps
from django.contrib.contenttypes.models import ContentType


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

composer_slots = [
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
            "target_content_type": "post.Post",
            "target_object_id": 20,
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
                    app_label=target_app, model=target_app)

        obj = model.objects.create(**item)
        obj.sites = [1]
        obj.save()

class BasicTestCase(TestCase):

    def test_default_slots(self):
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

    def test_header_footer_content(self):
        create_content(test_post_data + header_footer_posts)
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Header slot:")
        self.assertContains(response, "Content slot:")
        self.assertContains(response, "Footer slot:")

    def test_header_slots(self):
        create_content(composer_slots + test_post_data + header_footer_posts)

        # The header post should show up in the header slot
        response = self.client.get("/")
        self.assertNotContains(response, "Header slot:")
        self.assertContains(response, "Header Post markdown stuff")

        # And also on the test post page
        response = self.client.get("/post/test-post/")
        self.assertNotContains(response, "Header slot:")
        self.assertContains(response, "Header Post markdown stuff")

    def test_set_stuff(self):
        pass
