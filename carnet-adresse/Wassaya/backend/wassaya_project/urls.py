from django.contrib import admin
from django.urls import path, include
from wassaya_project.views import home  # ton JSON API running
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path("", home),  # / => JSON

    path("admin/", admin.site.urls),

    # API REST
    path("api/auth/", include("wassaya_users.urls")),
    path("api/clinic/", include("wassaya_clinic.urls")),
    path("api/rdv/", include("wassaya_rdv.urls")),

    # SITE HTML
    path("", include("webui.urls")),
]
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()

# EXPL: Fichier de routage principal du projet Wassaya, incluant les routes pour l'admin, l'API REST et l'interface web HTML.
