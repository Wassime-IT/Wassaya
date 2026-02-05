from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
path("site/", views.home_page, name="home_page"),
path("site/doctors/", views.doctor_list, name="doctor_list"),
path("site/doctors/<int:pk>/", views.doctor_detail, name="doctor_detail"),

# AUTH
path("site/register/", views.register_view, name="register_view"),
path("site/login/", views.login_view, name="login_view"),
path("site/logout/", views.logout_view, name="logout_view"),

# DASHBOARDS
path("site/patient/dashboard/", views.patient_dashboard, name="patient_dashboard"),
path("site/doctor/dashboard/", views.doctor_dashboard, name="doctor_dashboard"),
# RDV (site HTML)
path("site/patient/rdv/new/<int:doctor_id>/", views.patient_create_rdv, name="patient_create_rdv"),
path("site/patient/rdv/", views.patient_rdvs, name="patient_rdvs"),
path("site/patient/rdv/cancel/<int:rdv_id>/", views.patient_cancel_rdv, name="patient_cancel_rdv"),

path("site/doctor/rdv/", views.doctor_rdvs, name="doctor_rdvs"),
path("site/doctor/rdv/confirm/<int:rdv_id>/", views.doctor_confirm_rdv, name="doctor_confirm_rdv"),
path("site/doctor/rdv/reject/<int:rdv_id>/", views.doctor_reject_rdv, name="doctor_reject_rdv"),
path("site/rdv/ics/<int:rdv_id>/", views.rdv_ics_download, name="rdv_ics_download"),
# Email logs
path("patient/emails/", views.patient_email_logs, name="patient_email_logs"),
path("doctor/emails/", views.doctor_email_logs, name="doctor_email_logs"),
path("emails/<int:pk>/", views.email_log_detail, name="email_log_detail"),
# about path
path("about/", views.about_page, name="about_page"),
path("contact/", views.contact_page, name="contact_page"),
path("privacy/", views.privacy_page, name="privacy_page"),
]
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=getattr(settings, "STATIC_ROOT", None))
# EXPL: Routes URL pour les pages HTML du site (accueil, liste des médecins, détail d'un médecin, auth, dashboards).
