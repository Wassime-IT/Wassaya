from rest_framework import serializers
from .models import Speciality, DoctorProfile

class SpecialitySerializer(serializers.ModelSerializer):
    """
    EXPL: Transforme Speciality <-> JSON
    """
    class Meta:
        model = Speciality
        fields = ["id", "name"]


class DoctorProfileSerializer(serializers.ModelSerializer):
    """
    EXPL: On expose infos docteur + infos user (username/nom)
    """
    username = serializers.CharField(source="user.username", read_only=True)
    full_name = serializers.SerializerMethodField()  # EXPL: champ calculé
    speciality = SpecialitySerializer(read_only=True)

    class Meta:
        model = DoctorProfile
        fields = ["id", "username", "full_name", "speciality", "bio", "phone", "fee", "is_active"]

    def get_full_name(self, obj):
        return obj.user.get_full_name() or obj.user.username
# EXPL: Fin de serializers.py
