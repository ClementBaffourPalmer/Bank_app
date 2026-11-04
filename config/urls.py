from django.contrib import admin
from django.urls import include, path

from accounts.views import health_check, landing

urlpatterns = [
    path("", landing, name="landing"),
    path("health/", health_check, name="health"),
    path("admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("", include("ledger.urls")),
]
