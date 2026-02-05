from django.urls import path
from .views import SpecialityListView, DoctorListView, DoctorDetailView

urlpatterns = [
    path("specialities/", SpecialityListView.as_view()),
    path("doctors/", DoctorListView.as_view()),
    path("doctors/<int:pk>/", DoctorDetailView.as_view()),
]
# EXPL: routes hospital.
