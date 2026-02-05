from django.contrib import admin
from .models import Speciality, DoctorProfile, PatientProfile

@admin.register(Speciality)
class SpecialityAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "speciality", "fee", "is_active")
    list_filter = ("speciality", "is_active")
    search_fields = ("user__username", "user__first_name", "user__last_name", "speciality__name")

@admin.register(PatientProfile)
class PatientProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone")
    search_fields = ("user__username", "user__first_name", "user__last_name", "phone")
