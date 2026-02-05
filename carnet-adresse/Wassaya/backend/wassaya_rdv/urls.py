from django.urls import path
from wassaya_users.views import RegisterView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    MyAppointmentsView,
    CreateAppointmentView,
    DoctorConfirmAppointmentView,
    DoctorRejectAppointmentView,
    PatientCancelAppointmentView,
)

urlpatterns = [
    path("mine/", MyAppointmentsView.as_view()),
    path("create/", CreateAppointmentView.as_view()),

    path("doctor/<int:pk>/confirm/", DoctorConfirmAppointmentView.as_view()),
    path("doctor/<int:pk>/reject/", DoctorRejectAppointmentView.as_view()),

    path("patient/<int:pk>/cancel/", PatientCancelAppointmentView.as_view()),
    path("register/", RegisterView.as_view()),
    path("login/", TokenObtainPairView.as_view()),
    path("refresh/", TokenRefreshView.as_view()),
    
]
# EXPL: routes rdv.py
    