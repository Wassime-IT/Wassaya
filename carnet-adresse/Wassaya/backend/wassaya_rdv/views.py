from rest_framework import generics, status
from rest_framework.response import Response
from django.utils import timezone

from wassaya_users.permissions import IsPatient, IsDoctor
from wassaya_clinic.models import DoctorProfile, PatientProfile
from .models import Appointment
from .serializers import AppointmentCreateSerializer, AppointmentSerializer


class MyAppointmentsView(generics.ListAPIView):
    """
    EXPL: GET /api/rdv/mine/
    - Patient -> ses RDV
    - Doctor  -> ses RDV
    """
    serializer_class = AppointmentSerializer

    def get_queryset(self):
        user = self.request.user

        if user.role == "PATIENT":
            return Appointment.objects.filter(
                patient__user=user
            ).select_related("doctor__user").order_by("-datetime")

        if user.role == "DOCTOR":
            return Appointment.objects.filter(
                doctor__user=user
            ).select_related("patient__user").order_by("-datetime")

        return Appointment.objects.none()


class CreateAppointmentView(generics.GenericAPIView):
    """
    EXPL: POST /api/rdv/create/
    Le patient crée une demande de RDV => status=PENDING
    """
    serializer_class = AppointmentCreateSerializer
    permission_classes = [IsPatient]

    def post(self, request):
        ser = self.get_serializer(data=request.data)
        ser.is_valid(raise_exception=True)

        # EXPL: récupérer (ou créer) le profil patient lié à ce user
        patient_profile, _ = PatientProfile.objects.get_or_create(user=request.user)

        # EXPL: récupérer docteur
        doctor = DoctorProfile.objects.get(id=ser.validated_data["doctor_id"])

        dt = ser.validated_data["datetime"]

        # EXPL: empêcher RDV dans le passé
        if dt <= timezone.now():
            return Response({"detail": "Datetime must be in the future."}, status=status.HTTP_400_BAD_REQUEST)

        # EXPL: empêcher double réservation même docteur même créneau
        taken = Appointment.objects.filter(
            doctor=doctor,
            datetime=dt
        ).exclude(status__in=["REJECTED", "CANCELLED"]).exists()

        if taken:
            return Response({"detail": "This slot is already taken."}, status=status.HTTP_409_CONFLICT)

        appt = Appointment.objects.create(
            doctor=doctor,
            patient=patient_profile,
            datetime=dt,
            reason=ser.validated_data.get("reason", ""),
            status=Appointment.Status.PENDING,
        )

        return Response(AppointmentSerializer(appt).data, status=status.HTTP_201_CREATED)


class DoctorConfirmAppointmentView(generics.GenericAPIView):
    """
    EXPL: POST /api/rdv/doctor/<pk>/confirm/
    Le docteur confirme un RDV (qui lui appartient).
    """
    permission_classes = [IsDoctor]

    def post(self, request, pk):
        appt = Appointment.objects.select_related("doctor__user").get(pk=pk)

        if appt.doctor.user != request.user:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        appt.status = Appointment.Status.CONFIRMED
        appt.save()
        return Response({"detail": "Confirmed."})


class DoctorRejectAppointmentView(generics.GenericAPIView):
    """
    EXPL: POST /api/rdv/doctor/<pk>/reject/
    Le docteur refuse un RDV.
    """
    permission_classes = [IsDoctor]

    def post(self, request, pk):
        appt = Appointment.objects.select_related("doctor__user").get(pk=pk)

        if appt.doctor.user != request.user:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        appt.status = Appointment.Status.REJECTED
        appt.save()
        return Response({"detail": "Rejected."})


class PatientCancelAppointmentView(generics.GenericAPIView):
    """
    EXPL: POST /api/rdv/patient/<pk>/cancel/
    Le patient annule son RDV.
    """
    permission_classes = [IsPatient]

    def post(self, request, pk):
        appt = Appointment.objects.select_related("patient__user").get(pk=pk)

        if appt.patient.user != request.user:
            return Response({"detail": "Not allowed."}, status=status.HTTP_403_FORBIDDEN)

        appt.status = Appointment.Status.CANCELLED
        appt.save()
        return Response({"detail": "Cancelled."})
# EXPL: Fin de views.py
