from django.db import models
from django.conf import settings

# EXPL: settings.AUTH_USER_MODEL = notre user personnalisé (wassaya_users.User)
# On l’utilise pour lier DoctorProfile / PatientProfile à User.

class Speciality(models.Model):
    """
    EXPL: Spécialité médicale : Cardiologie, Dentiste, etc.
    """
    name = models.CharField(max_length=120, unique=True)  # EXPL: unique pour éviter doublons

    def __str__(self):
        return self.name


class DoctorProfile(models.Model):
    """
    EXPL: Profil médecin lié à un User (role=DOCTOR).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,              # EXPL: si l'user est supprimé, son profil aussi
        related_name="doctor_profile"          # EXPL: accès via user.doctor_profile
    )

    speciality = models.ForeignKey(
        Speciality,
        on_delete=models.SET_NULL,             # EXPL: si spécialité supprimée -> met NULL
        null=True,
        blank=True
    )

    bio = models.TextField(blank=True)         # EXPL: description du docteur
    phone = models.CharField(max_length=30, blank=True)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)  # EXPL: tarif
    is_active = models.BooleanField(default=True)  # EXPL: admin peut désactiver

    def __str__(self):
        return f"Dr {self.user.get_full_name() or self.user.username}"


class PatientProfile(models.Model):
    """
    EXPL: Profil patient lié à un User (role=PATIENT).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile"         # EXPL: accès via user.patient_profile
    )
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username
# EXPL: Fin de models.py
