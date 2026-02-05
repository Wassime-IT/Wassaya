from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model

from .models import DoctorProfile, PatientProfile

User = get_user_model()

@receiver(post_save, sender=User)
def auto_create_profiles(sender, instance, created, **kwargs):
    """
    EXPL:
    - Signal post_save: s’exécute après chaque sauvegarde d’un User.
    - created=True seulement à la création.
    - On crée automatiquement le profil correspondant au rôle.
    """
    if not created:
        return

    if instance.role == "DOCTOR":
        DoctorProfile.objects.get_or_create(user=instance)

    elif instance.role == "PATIENT":
        PatientProfile.objects.get_or_create(user=instance)

    # ADMIN: rien à créer
    else:
        pass
# EXPL: Signal pour créer automatiquement les profils DoctorProfile ou PatientProfile lors de la création d'un User.
