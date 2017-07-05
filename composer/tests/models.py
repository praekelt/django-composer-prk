from django.core.urlresolvers import reverse
from django.db import models


class DummyModel1(models.Model):
    title = models.CharField(max_length=100)

    def get_absolute_url(self):
        return reverse("dummymodel1-detail", args=(self.pk,))


class DummyModel2(models.Model):
    title = models.CharField(max_length=100)

    def get_absolute_url(self):
        return reverse("dummymodel2-detail", args=(self.pk,))
