from rest_framework import serializers
from .models import Appointment
from wassaya_clinic.models import DoctorProfile

class AppointmentCreateSerializer(serializers.Serializer):
    """
    EXPL: Données attendues lors de la création d’un RDV par un patient.
    """
    doctor_id = serializers.IntegerField()
    datetime = serializers.DateTimeField()
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)

    def validate_doctor_id(self, value):
        # EXPL: vérifier que le docteur existe et qu'il est actif
        if not DoctorProfile.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Doctor not found or inactive.")
        return value


class AppointmentSerializer(serializers.ModelSerializer):
    """
    EXPL: Données renvoyées au client pour affichage.
    """
    doctor_name = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = ["id", "datetime", "reason", "status", "created_at", "doctor_name"]

    def get_doctor_name(self, obj):
        return obj.doctor.user.get_full_name() or obj.doctor.user.username
# EXPL: Fin de serializers.py
