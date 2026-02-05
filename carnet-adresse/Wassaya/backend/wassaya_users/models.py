from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    """
    User personnalisé : on ajoute un champ role.
    - ADMIN  : gérant (supervision)
    - DOCTOR : médecin
    - PATIENT: patient
    """

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        DOCTOR = "DOCTOR", "Doctor"
        PATIENT = "PATIENT", "Patient"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PATIENT,
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
