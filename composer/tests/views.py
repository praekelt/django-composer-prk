from django.views.generic.detail import DetailView

from composer.tests.models import DummyModel1


class DummyModel1View(DetailView):
    model = DummyModel1
    template_name = "tests/dummymodel1_detail.html"
