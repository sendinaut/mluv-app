from django.urls import path
from django.views.generic import TemplateView

from main.views import (
    menu_view,
)

app_name = "main"

urlpatterns = [
    path("", menu_view, name="index"),
    path("menu/", menu_view, name="menu"),
    path(
        "publichna-oferta",
        TemplateView.as_view(template_name="main/public_offer.html"),
        name="public-offer-url",
    ),
]
