from django.urls import path
from .views import RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from django.contrib import admin
admin.site.site_header = "Wassaya Admin"
admin.site.site_title = "Wassaya Admin"
admin.site.index_title = "Tableau de bord"

urlpatterns = [
    # AUTH API
    path("register/", RegisterView.as_view()),
    path("login/", TokenObtainPairView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
]
# EXPL: Fichier de routage pour l'application wassaya_users, incluant les routes pour l'enregistrement et l'authentification via JWT, ainsi que la personnalisation de l'interface d'administration Django.
