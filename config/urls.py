from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("i18nn/",
         include("django.conf.urls.i18n")),
]

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    prefix_default_language=False,
)