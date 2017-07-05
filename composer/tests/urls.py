from django.conf.urls import url, include
from django.views.generic.base import TemplateView

from composer.tests.views import DummyModel1View


urlpatterns = [
    url(
        r"^$",
        TemplateView.as_view(template_name="tests/home.html"),
        name="home"
    ),
    url(
        r"^dummymodel1/(?P<pk>\d+)/$",
        DummyModel1View.as_view(),
        name="dummymodel1-detail"
    ),
    url(
        r"^header/$",
        TemplateView.as_view(template_name="tests/header.html"),
        name="header"
    ),
    url(
        r"^aaa/$",
        TemplateView.as_view(template_name="tests/aaa.html"),
        name="aaa"
    ),
    url(
        r"^aaa/bbb/$",
        TemplateView.as_view(template_name="tests/bbb.html"),
        name="bbb"
    ),
    url(
        r"^slot-context/$",
        TemplateView.as_view(template_name="tests/slot_context.html"),
        name="slot_context"
    ),
]
