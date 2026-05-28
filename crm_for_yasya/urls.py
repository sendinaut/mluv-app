from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("user.urls", namespace="user")),
    path("", include("main.urls", namespace="main")),
    path("", include("crm.urls", namespace="crm")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
