from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from wassaya_rdv.models import Appointment
from webui.email_service import notify_appointment_reminder


class Command(BaseCommand):
    help = "Envoie les rappels automatiques des rendez-vous confirmés (24h et 1h)."

    def handle(self, *args, **options):
        now = timezone.now()

        # Fenêtres de rappel (tolérance 10 min)
        tol = timedelta(minutes=10)

        # 24h avant
        target_24h_start = now + timedelta(hours=24) - tol
        target_24h_end   = now + timedelta(hours=24) + tol

        qs_24h = Appointment.objects.filter(
            status="CONFIRMED",
            datetime__gte=target_24h_start,
            datetime__lte=target_24h_end,
            reminder_24h_sent=False,
        )

        count_24h = 0
        for appt in qs_24h:
            notify_appointment_reminder(appt, reminder_label="dans 24 heures")
            appt.reminder_24h_sent = True
            appt.save(update_fields=["reminder_24h_sent"])
            count_24h += 1

        # 1h avant
        target_1h_start = now + timedelta(hours=1) - tol
        target_1h_end   = now + timedelta(hours=1) + tol

        qs_1h = Appointment.objects.filter(
            status="CONFIRMED",
            datetime__gte=target_1h_start,
            datetime__lte=target_1h_end,
            reminder_1h_sent=False,
        )

        count_1h = 0
        for appt in qs_1h:
            notify_appointment_reminder(appt, reminder_label="dans 1 heure")
            appt.reminder_1h_sent = True
            appt.save(update_fields=["reminder_1h_sent"])
            count_1h += 1

        self.stdout.write(self.style.SUCCESS(
            f"Reminders sent: 24h={count_24h}, 1h={count_1h}"
        ))
# EXPL: Commande management Django pour envoyer des rappels automatiques de rendez-vous confirmés 24h et 1h avant l'heure prévue.
