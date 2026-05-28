from django.urls import path

from main.views import (
    menu_view,
)

app_name = "main"

urlpatterns = [
    path("", menu_view, name="index"),
    path("menu/", menu_view, name="menu"),
]
