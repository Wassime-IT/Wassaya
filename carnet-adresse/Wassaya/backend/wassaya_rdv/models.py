from django.db import models
from wassaya_clinic.models import DoctorProfile, PatientProfile

class Appointment(models.Model):
    """
    EXPL: Rendez-vous patient ↔ docteur.
    status:
      - PENDING   : demande envoyée
      - CONFIRMED : confirmée par docteur
      - REJECTED  : refusée par docteur
      - CANCELLED : annulée par patient
    """
    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        CONFIRMED = "CONFIRMED", "Confirmed"
        REJECTED = "REJECTED", "Rejected"
        CANCELLED = "CANCELLED", "Cancelled"

    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name="appointments"
    )
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name="appointments"
    )

    datetime = models.DateTimeField()                 # EXPL: date/heure du RDV
    reason = models.CharField(max_length=255, blank=True)  # EXPL: motif
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)   # EXPL: auto date création

    class Meta:
        # EXPL: accélère les recherches RDV par docteur/date
        indexes = [
            models.Index(fields=["doctor", "datetime"]),
            models.Index(fields=["patient", "datetime"]),
        ]

    def __str__(self):
        return f"RDV {self.patient} -> {self.doctor} ({self.datetime})"
    
    reminder_24h_sent = models.BooleanField(default=False)
    reminder_1h_sent = models.BooleanField(default=False)
    

# EXPL: Historique des emails envoyés (global + par RDV).
#  On stocke seulement des métadonnées (propre et léger).
class EmailLog(models.Model):
    """
    Historique des emails envoyés (global + par RDV).
    On stocke seulement des métadonnées (propre et léger).
    """

    class Status(models.TextChoices):
        SENT = "SENT", "Sent"
        FAILED = "FAILED", "Failed"

    class Kind(models.TextChoices):
        PATIENT_CREATED = "PATIENT_CREATED", "Patient - RDV created (PENDING)"
        PATIENT_STATUS = "PATIENT_STATUS", "Patient - RDV status changed"
        PATIENT_CANCELLED = "PATIENT_CANCELLED", "Patient - RDV cancelled"
        DOCTOR_NEW_REQUEST = "DOCTOR_NEW_REQUEST", "Doctor - new RDV request"
        OTHER = "OTHER", "Other"

    created_at = models.DateTimeField(auto_now_add=True)

    # Lié au RDV (optionnel)
    appointment_id = models.IntegerField(null=True, blank=True, db_index=True)

    kind = models.CharField(max_length=40, choices=Kind.choices, default=Kind.OTHER)
    to_email = models.EmailField(max_length=254)
    subject = models.CharField(max_length=255)

    status = models.CharField(max_length=10, choices=Status.choices, default=Status.SENT)
    error_message = models.TextField(blank=True, default="")

    template = models.CharField(max_length=200, blank=True, default="")
    has_ics = models.BooleanField(default=False)

    def __str__(self):
        return f"[{self.status}] {self.kind} -> {self.to_email} ({self.created_at:%Y-%m-%d %H:%M})"

# EXPL: Fin de models.py
