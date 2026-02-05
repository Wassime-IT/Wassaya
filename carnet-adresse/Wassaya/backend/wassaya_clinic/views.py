from rest_framework import generics, permissions
from .models import DoctorProfile, Speciality
from .serializers import DoctorProfileSerializer, SpecialitySerializer

class SpecialityListView(generics.ListAPIView):
    """
    EXPL: GET /api/clinic/specialities/
    Public : liste des spécialités
    """
    queryset = Speciality.objects.all().order_by("name")
    serializer_class = SpecialitySerializer
    permission_classes = [permissions.AllowAny]


class DoctorListView(generics.ListAPIView):
    """
    EXPL: GET /api/clinic/doctors/
    Public : liste des docteurs actifs
    """
    queryset = DoctorProfile.objects.filter(is_active=True).select_related("user", "speciality").order_by("user__username")
    serializer_class = DoctorProfileSerializer
    permission_classes = [permissions.AllowAny]


class DoctorDetailView(generics.RetrieveAPIView):
    """
    EXPL: GET /api/clinic/doctors/<id>/
    Public : détail d’un docteur
    """
    queryset = DoctorProfile.objects.filter(is_active=True).select_related("user", "speciality")
    serializer_class = DoctorProfileSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = "id"  # EXPL: URL paramètre : /doctors/<id>/

# EXPL: Fin de views.py